from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class Livre(Base):
    """Représente la table 'livres' dans PostgreSQL."""
    __tablename__ = "livres"

    id         = Column(Integer, primary_key=True, index=True)
    titre      = Column(String(255), nullable=False)
    auteur     = Column(String(255), nullable=False)
    isbn       = Column(String(20), unique=True, nullable=False)
    annee      = Column(Integer)
    genre      = Column(String(100))
    quantite   = Column(Integer, default=1)       # Nombre total d'exemplaires
    disponible = Column(Integer, default=1)        # Nombre d'exemplaires disponibles
