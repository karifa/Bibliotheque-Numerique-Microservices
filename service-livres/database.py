from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# L'URL est injectée par Docker Compose via une variable d'environnement
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/bibliotheque"
)

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()


def get_db():
    """Fournit une session de base de données et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
