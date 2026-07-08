from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Microservice Livres",
    description="API de gestion des livres - Bibliothèque DIT",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/livres", response_model=List[schemas.LivreResponse])
def lister_livres(db: Session = Depends(get_db)):
    """Retourne la liste de tous les livres, triés par ID."""
    return db.query(models.Livre).order_by(models.Livre.id).all()


@app.get("/livres/recherche", response_model=List[schemas.LivreResponse])
def rechercher_livres(
    titre:  Optional[str] = Query(None, description="Recherche par titre"),
    auteur: Optional[str] = Query(None, description="Recherche par auteur"),
    isbn:   Optional[str] = Query(None, description="Recherche par ISBN"),
    db: Session = Depends(get_db)
):
    """Recherche des livres par titre, auteur ou ISBN. Les paramètres sont cumulables."""
    query = db.query(models.Livre)
    if titre:
        query = query.filter(models.Livre.titre.ilike(f"%{titre}%"))
    if auteur:
        query = query.filter(models.Livre.auteur.ilike(f"%{auteur}%"))
    if isbn:
        query = query.filter(models.Livre.isbn == isbn)
    return query.all()


@app.get("/livres/{livre_id}", response_model=schemas.LivreResponse)
def obtenir_livre(livre_id: int, db: Session = Depends(get_db)):
    """Retourne les détails d'un livre par son ID."""
    livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    return livre


@app.post("/livres", response_model=schemas.LivreResponse, status_code=201)
def ajouter_livre(livre: schemas.LivreCreate, db: Session = Depends(get_db)):
    """Ajoute un nouveau livre. L'ISBN doit être unique."""
    existant = db.query(models.Livre).filter(models.Livre.isbn == livre.isbn).first()
    if existant:
        raise HTTPException(status_code=400, detail="Un livre avec cet ISBN existe déjà")

    data = livre.model_dump()
    data["disponible"] = data["quantite"]  # Au départ tous les exemplaires sont disponibles
    nouveau_livre = models.Livre(**data)
    db.add(nouveau_livre)
    db.commit()
    db.refresh(nouveau_livre)
    return nouveau_livre


@app.put("/livres/{livre_id}", response_model=schemas.LivreResponse)
def modifier_livre(livre_id: int, mise_a_jour: schemas.LivreUpdate, db: Session = Depends(get_db)):
    """Modifie un livre existant. Seuls les champs fournis sont mis à jour."""
    livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    for champ, valeur in mise_a_jour.model_dump(exclude_unset=True).items():
        setattr(livre, champ, valeur)

    db.commit()
    db.refresh(livre)
    return livre


@app.delete("/livres/{livre_id}", status_code=204)
def supprimer_livre(livre_id: int, db: Session = Depends(get_db)):
    """Supprime un livre de la bibliothèque."""
    livre = db.query(models.Livre).filter(models.Livre.id == livre_id).first()
    if not livre:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    db.delete(livre)
    db.commit()
    return None


@app.get("/health")
def health_check():
    """Vérifie que le service est opérationnel."""
    return {"status": "ok", "service": "livres"}
