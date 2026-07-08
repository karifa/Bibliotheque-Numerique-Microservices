from sqlalchemy import Column, Integer, Date, Boolean, String
from database import Base


class Config(Base):
    """
    Table de configuration globale du service.
    Stocke les paramètres persistants comme le mode de validation des emprunts.
    """
    __tablename__ = "config"

    cle   = Column(String(100), primary_key=True)
    valeur = Column(String(255), nullable=False)


class Emprunt(Base):
    """
    Représente la table 'emprunts' dans PostgreSQL.
    - valide       : False = en attente de validation admin, True = validé (livre physiquement remis)
    - date_retour_reelle est null tant que le livre n'a pas été rendu
    - retard est True si le livre a été rendu après la date prévue
    """
    __tablename__ = "emprunts"

    id                 = Column(Integer, primary_key=True, index=True)
    utilisateur_id     = Column(Integer, nullable=False)
    livre_id           = Column(Integer, nullable=False)
    date_emprunt       = Column(Date, nullable=False)
    date_retour_prevue = Column(Date, nullable=False)
    date_retour_reelle = Column(Date, nullable=True)
    retard             = Column(Boolean, default=False)
    valide             = Column(Boolean, default=True)   # False = en attente de validation admin
