from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models import TypeUtilisateur, RoleUtilisateur


class RegisterRequest(BaseModel):
    nom: str
    prenom: str
    email: str
    mot_de_passe: str
    telephone: Optional[str] = None
    type: TypeUtilisateur
    matricule: Optional[str] = None
    piece_identite_type: Optional[str] = None
    piece_identite_numero: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    mot_de_passe: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UtilisateurResponse"


class UtilisateurCreate(BaseModel):
    nom: str
    prenom: str
    email: str
    mot_de_passe: str
    telephone: Optional[str] = None
    type: TypeUtilisateur
    role: RoleUtilisateur = RoleUtilisateur.membre
    matricule: Optional[str] = None
    piece_identite_type: Optional[str] = None
    piece_identite_numero: Optional[str] = None


class UtilisateurUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    email: Optional[str] = None
    telephone: Optional[str] = None
    type: Optional[TypeUtilisateur] = None
    matricule: Optional[str] = None
    piece_identite_type: Optional[str] = None
    piece_identite_numero: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str


class UtilisateurResponse(BaseModel):
    id: int
    nom: str
    prenom: str
    email: str
    telephone: Optional[str]
    type: TypeUtilisateur
    role: RoleUtilisateur
    matricule: Optional[str]
    piece_identite_type: Optional[str]
    piece_identite_numero: Optional[str]
    actif: bool
    mot_de_passe_temporaire: bool = False
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


LoginResponse.model_rebuild()
