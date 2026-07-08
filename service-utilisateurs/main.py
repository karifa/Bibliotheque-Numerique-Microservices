from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import hashlib
import hmac
import json
import base64
import time
import os

import models, schemas
from database import engine, get_db
from models import TypeUtilisateur, RoleUtilisateur

models.Base.metadata.create_all(bind=engine)

SECRET_KEY = os.getenv("SECRET_KEY", "bibliotheque-dit-secret-key-2026")
TOKEN_EXPIRY = 86400 * 7  # 7 jours

app = FastAPI(
    title="Microservice Utilisateurs",
    description="API de gestion des membres - Bibliothèque DIT",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Utilitaires Auth ──

def hash_password(password: str) -> str:
    return hashlib.sha256((password + SECRET_KEY).encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def create_token(user_id: int, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": int(time.time()) + TOKEN_EXPIRY
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def decode_token(token: str) -> dict:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token manquant")
    token = authorization[7:]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    user = db.query(models.Utilisateur).filter(models.Utilisateur.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable")
    return user


# ── Endpoints Auth ──

@app.post("/auth/register", response_model=schemas.LoginResponse, status_code=201)
def register(data: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Inscription d'un nouveau membre."""
    if db.query(models.Utilisateur).filter(models.Utilisateur.email == data.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")

    # Validation conditionnelle
    if data.type == TypeUtilisateur.etudiant:
        if not data.matricule:
            raise HTTPException(status_code=400, detail="Le matricule est obligatoire pour les étudiants")
        if db.query(models.Utilisateur).filter(models.Utilisateur.matricule == data.matricule).first():
            raise HTTPException(status_code=400, detail="Ce matricule est déjà utilisé")
    else:
        if not data.piece_identite_numero:
            raise HTTPException(status_code=400, detail="Le numéro de pièce d'identité est obligatoire pour les enseignants et le personnel")

    nouveau = models.Utilisateur(
        nom=data.nom,
        prenom=data.prenom,
        email=data.email,
        mot_de_passe=hash_password(data.mot_de_passe),
        telephone=data.telephone,
        type=data.type,
        role=RoleUtilisateur.membre,
        matricule=data.matricule,
        piece_identite_type=data.piece_identite_type,
        piece_identite_numero=data.piece_identite_numero,
    )
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)

    token = create_token(nouveau.id, nouveau.role.value)
    return schemas.LoginResponse(access_token=token, user=schemas.UtilisateurResponse.model_validate(nouveau))


@app.post("/auth/login", response_model=schemas.LoginResponse)
def login(data: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Connexion d'un membre existant."""
    user = db.query(models.Utilisateur).filter(models.Utilisateur.email == data.email).first()
    if not user or not verify_password(data.mot_de_passe, user.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")
    if not user.actif:
        raise HTTPException(status_code=403, detail="Compte désactivé")

    token = create_token(user.id, user.role.value)
    return schemas.LoginResponse(access_token=token, user=schemas.UtilisateurResponse.model_validate(user))


@app.get("/auth/me", response_model=schemas.UtilisateurResponse)
def get_me(current_user: models.Utilisateur = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté."""
    return current_user


@app.post("/auth/changer-mot-de-passe", response_model=schemas.UtilisateurResponse)
def changer_mot_de_passe(
    data: schemas.ChangePasswordRequest,
    current_user: models.Utilisateur = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Permet à l'utilisateur de changer son mot de passe (obligatoire si temporaire)."""
    if not verify_password(data.ancien_mot_de_passe, current_user.mot_de_passe):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect")
    if len(data.nouveau_mot_de_passe) < 6:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit contenir au moins 6 caractères")
    if data.ancien_mot_de_passe == data.nouveau_mot_de_passe:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit être différent de l'ancien")

    current_user.mot_de_passe = hash_password(data.nouveau_mot_de_passe)
    current_user.mot_de_passe_temporaire = False
    db.commit()
    db.refresh(current_user)
    return current_user


# ── Endpoints CRUD (compatibilité) ──

@app.get("/utilisateurs", response_model=List[schemas.UtilisateurResponse])
def lister_utilisateurs(db: Session = Depends(get_db)):
    return db.query(models.Utilisateur).order_by(models.Utilisateur.id).all()


@app.get("/utilisateurs/type/{type_utilisateur}", response_model=List[schemas.UtilisateurResponse])
def lister_par_type(type_utilisateur: TypeUtilisateur, db: Session = Depends(get_db)):
    return db.query(models.Utilisateur).filter(models.Utilisateur.type == type_utilisateur).all()


@app.get("/utilisateurs/{utilisateur_id}", response_model=schemas.UtilisateurResponse)
def obtenir_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return utilisateur


@app.post("/utilisateurs", response_model=schemas.UtilisateurResponse, status_code=201)
def creer_utilisateur(utilisateur: schemas.UtilisateurCreate, db: Session = Depends(get_db)):
    if db.query(models.Utilisateur).filter(models.Utilisateur.email == utilisateur.email).first():
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé")
    if utilisateur.matricule:
        if db.query(models.Utilisateur).filter(models.Utilisateur.matricule == utilisateur.matricule).first():
            raise HTTPException(status_code=400, detail="Ce matricule est déjà utilisé")

    data = utilisateur.model_dump()
    data["mot_de_passe"] = hash_password(data["mot_de_passe"])
    # Les comptes membres créés par l'admin ont un mot de passe temporaire.
    # Les comptes admin (ex: bootstrap initial) n'ont pas de mot de passe temporaire.
    est_temporaire = (utilisateur.role == RoleUtilisateur.membre)
    nouveau = models.Utilisateur(**data, mot_de_passe_temporaire=est_temporaire)
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


@app.put("/utilisateurs/{utilisateur_id}", response_model=schemas.UtilisateurResponse)
def modifier_utilisateur(utilisateur_id: int, mise_a_jour: schemas.UtilisateurUpdate, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    for champ, valeur in mise_a_jour.model_dump(exclude_unset=True).items():
        setattr(utilisateur, champ, valeur)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


@app.put("/utilisateurs/{utilisateur_id}/desactiver", response_model=schemas.UtilisateurResponse)
def desactiver_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    """Désactive un compte membre sans le supprimer (conservation de l'historique)."""
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    if utilisateur.role.value == "admin":
        raise HTTPException(status_code=403, detail="Impossible de désactiver un compte administrateur")
    utilisateur.actif = False
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


@app.delete("/utilisateurs/{utilisateur_id}", status_code=204)
def supprimer_utilisateur(utilisateur_id: int, db: Session = Depends(get_db)):
    utilisateur = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not utilisateur:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    db.delete(utilisateur)
    db.commit()
    return None


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "utilisateurs"}
