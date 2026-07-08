from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.sql import func
from database import Base
import enum


class TypeUtilisateur(str, enum.Enum):
    etudiant = "etudiant"
    professeur = "professeur"
    personnel_administratif = "personnel_administratif"


class RoleUtilisateur(str, enum.Enum):
    admin = "admin"
    membre = "membre"


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    mot_de_passe = Column(String(255), nullable=False)
    telephone = Column(String(20), nullable=True)
    type = Column(Enum(TypeUtilisateur), nullable=False)
    role = Column(Enum(RoleUtilisateur), default=RoleUtilisateur.membre, nullable=False)
    matricule = Column(String(50), unique=True, nullable=True)
    piece_identite_type = Column(String(50), nullable=True)
    piece_identite_numero = Column(String(100), nullable=True)
    actif = Column(Boolean, default=True)
    mot_de_passe_temporaire = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
