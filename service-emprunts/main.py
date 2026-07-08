from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import date, timedelta
import httpx
import models, schemas
from database import engine, get_db
import os

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Microservice Emprunts",
    description="API de gestion des emprunts - Bibliothèque DIT",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_LIVRES       = os.getenv("SERVICE_LIVRES_URL",       "http://service-livres:8001")
SERVICE_UTILISATEURS = os.getenv("SERVICE_UTILISATEURS_URL", "http://service-utilisateurs:8002")

CLE_AUTO_VALIDATION = "auto_validation"


# ── Helpers config ──

def get_auto_validation(db: Session) -> bool:
    """Lit le mode de validation automatique depuis la base. Défaut : True."""
    cfg = db.query(models.Config).filter(models.Config.cle == CLE_AUTO_VALIDATION).first()
    if cfg is None:
        # Initialiser à True si absent
        db.add(models.Config(cle=CLE_AUTO_VALIDATION, valeur="true"))
        db.commit()
        return True
    return cfg.valeur.lower() == "true"


def set_auto_validation(db: Session, valeur: bool):
    cfg = db.query(models.Config).filter(models.Config.cle == CLE_AUTO_VALIDATION).first()
    if cfg:
        cfg.valeur = "true" if valeur else "false"
    else:
        db.add(models.Config(cle=CLE_AUTO_VALIDATION, valeur="true" if valeur else "false"))
    db.commit()


# ── Helpers inter-services ──

def verifier_utilisateur(utilisateur_id: int) -> dict:
    try:
        r = httpx.get(f"{SERVICE_UTILISATEURS}/utilisateurs/{utilisateur_id}", timeout=5)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Utilisateur {utilisateur_id} introuvable")
        r.raise_for_status()
        return r.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service utilisateurs indisponible")


def verifier_livre(livre_id: int) -> dict:
    try:
        r = httpx.get(f"{SERVICE_LIVRES}/livres/{livre_id}", timeout=5)
        if r.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Livre {livre_id} introuvable")
        r.raise_for_status()
        return r.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service livres indisponible")


def marquer_livre_indisponible(livre_id: int):
    try:
        livre = httpx.get(f"{SERVICE_LIVRES}/livres/{livre_id}", timeout=5).json()
        dispo = max(0, livre.get("disponible", 1) - 1)
        httpx.put(f"{SERVICE_LIVRES}/livres/{livre_id}", json={"disponible": dispo}, timeout=5)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service livres indisponible")


def marquer_livre_disponible(livre_id: int):
    try:
        livre = httpx.get(f"{SERVICE_LIVRES}/livres/{livre_id}", timeout=5).json()
        dispo = livre.get("disponible", 0) + 1
        quantite = livre.get("quantite", dispo)
        dispo = min(dispo, quantite)
        httpx.put(f"{SERVICE_LIVRES}/livres/{livre_id}", json={"disponible": dispo}, timeout=5)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Service livres indisponible")


# ── Config auto-validation ──

@app.get("/config/auto-validation", response_model=schemas.AutoValidationResponse)
def lire_auto_validation(db: Session = Depends(get_db)):
    """Retourne l'état actuel du mode de validation automatique des emprunts."""
    return {"auto_validation": get_auto_validation(db)}


@app.put("/config/auto-validation", response_model=schemas.AutoValidationResponse)
def modifier_auto_validation(data: schemas.AutoValidationUpdate, db: Session = Depends(get_db)):
    """Active ou désactive la validation automatique des emprunts."""
    set_auto_validation(db, data.auto_validation)
    return {"auto_validation": data.auto_validation}


# ── Emprunts ──

@app.post("/emprunts", response_model=schemas.EmpruntResponse, status_code=201)
def emprunter_livre(emprunt: schemas.EmpruntCreate, db: Session = Depends(get_db)):
    """
    Crée une demande d'emprunt.
    - Si la validation automatique est activée : l'emprunt est validé immédiatement,
      le stock est décrémenté et le membre peut venir chercher le livre.
    - Si la validation est manuelle : l'emprunt est créé en attente (valide=False),
      le stock n'est PAS encore décrémenté. L'admin doit valider depuis l'interface.
    """
    verifier_utilisateur(emprunt.utilisateur_id)

    # Vérifier la limite de 2 emprunts validés en cours par utilisateur
    emprunts_en_cours = db.query(models.Emprunt).filter(
        models.Emprunt.utilisateur_id == emprunt.utilisateur_id,
        models.Emprunt.date_retour_reelle == None,
        models.Emprunt.valide == True
    ).count()
    if emprunts_en_cours >= 2:
        raise HTTPException(
            status_code=400,
            detail="Vous avez déjà 2 emprunts en cours. Veuillez retourner un livre avant d'en emprunter un nouveau."
        )

    livre = verifier_livre(emprunt.livre_id)
    if not livre.get("disponible", 0) > 0:
        raise HTTPException(status_code=400, detail="Aucun exemplaire disponible pour ce livre")

    auto = get_auto_validation(db)
    aujourd_hui = date.today()
    date_retour = emprunt.date_retour_prevue or (aujourd_hui + timedelta(days=15))

    nouvel_emprunt = models.Emprunt(
        utilisateur_id     = emprunt.utilisateur_id,
        livre_id           = emprunt.livre_id,
        date_emprunt       = aujourd_hui,
        date_retour_prevue = date_retour,
        valide             = auto,
    )
    db.add(nouvel_emprunt)

    if auto:
        # Validation automatique : on réserve le stock immédiatement
        marquer_livre_indisponible(emprunt.livre_id)

    db.commit()
    db.refresh(nouvel_emprunt)
    return nouvel_emprunt


@app.put("/emprunts/{emprunt_id}/valider", response_model=schemas.EmpruntResponse)
def valider_emprunt(emprunt_id: int, db: Session = Depends(get_db)):
    """
    Valide manuellement un emprunt en attente.
    Décrémente le stock du livre et marque l'emprunt comme validé.
    """
    emprunt = db.query(models.Emprunt).filter(models.Emprunt.id == emprunt_id).first()
    if not emprunt:
        raise HTTPException(status_code=404, detail="Emprunt non trouvé")
    if emprunt.valide:
        raise HTTPException(status_code=400, detail="Cet emprunt est déjà validé")
    if emprunt.date_retour_reelle:
        raise HTTPException(status_code=400, detail="Cet emprunt est déjà clôturé")

    emprunt.valide = True
    marquer_livre_indisponible(emprunt.livre_id)
    db.commit()
    db.refresh(emprunt)
    return emprunt


@app.put("/emprunts/{emprunt_id}/retour", response_model=schemas.EmpruntResponse)
def retourner_livre(emprunt_id: int, db: Session = Depends(get_db)):
    """
    Enregistre le retour d'un livre.
    Impossible si l'emprunt n'est pas encore validé.
    """
    emprunt = db.query(models.Emprunt).filter(models.Emprunt.id == emprunt_id).first()
    if not emprunt:
        raise HTTPException(status_code=404, detail="Emprunt non trouvé")
    if not emprunt.valide:
        raise HTTPException(status_code=400, detail="Cet emprunt n'est pas encore validé")
    if emprunt.date_retour_reelle:
        raise HTTPException(status_code=400, detail="Ce livre a déjà été retourné")

    aujourd_hui = date.today()
    emprunt.date_retour_reelle = aujourd_hui
    emprunt.retard = aujourd_hui > emprunt.date_retour_prevue

    marquer_livre_disponible(emprunt.livre_id)
    db.commit()
    db.refresh(emprunt)
    return emprunt


@app.get("/emprunts/en-attente", response_model=List[schemas.EmpruntResponse])
def emprunts_en_attente(db: Session = Depends(get_db)):
    """Retourne les demandes d'emprunt en attente de validation admin."""
    return db.query(models.Emprunt).filter(
        models.Emprunt.valide == False
    ).order_by(models.Emprunt.date_emprunt).all()


@app.get("/emprunts/en-cours", response_model=List[schemas.EmpruntResponse])
def emprunts_en_cours(db: Session = Depends(get_db)):
    """Retourne les emprunts validés dont le livre n'a pas encore été rendu."""
    return db.query(models.Emprunt).filter(
        models.Emprunt.date_retour_reelle == None,
        models.Emprunt.valide == True
    ).all()


@app.get("/emprunts/retards", response_model=List[schemas.EmpruntResponse])
def emprunts_en_retard(db: Session = Depends(get_db)):
    """Retourne les emprunts validés en retard."""
    aujourd_hui = date.today()
    return db.query(models.Emprunt).filter(
        models.Emprunt.valide == True,
        (models.Emprunt.retard == True) |
        (
            (models.Emprunt.date_retour_reelle == None) &
            (models.Emprunt.date_retour_prevue < aujourd_hui)
        )
    ).all()


@app.get("/emprunts", response_model=List[schemas.EmpruntResponse])
def historique_emprunts(db: Session = Depends(get_db)):
    """Retourne l'historique complet de tous les emprunts (validés et en attente)."""
    return db.query(models.Emprunt).order_by(models.Emprunt.id.desc()).all()


@app.get("/emprunts/utilisateur/{utilisateur_id}", response_model=List[schemas.EmpruntResponse])
def historique_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    """Retourne tous les emprunts d'un membre donné."""
    return db.query(models.Emprunt).filter(
        models.Emprunt.utilisateur_id == utilisateur_id
    ).order_by(models.Emprunt.id.desc()).all()


@app.get("/emprunts/{emprunt_id}", response_model=schemas.EmpruntResponse)
def detail_emprunt(emprunt_id: int, db: Session = Depends(get_db)):
    """Retourne le détail d'un emprunt."""
    emprunt = db.query(models.Emprunt).filter(models.Emprunt.id == emprunt_id).first()
    if not emprunt:
        raise HTTPException(status_code=404, detail="Emprunt non trouvé")
    return emprunt


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "emprunts"}
