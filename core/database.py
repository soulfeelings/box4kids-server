from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Автоматический commit при успехе
        print("Commit success")
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
        db.rollback()  # Автоматический rollback при ошибке
        raise
    finally:
        db.close() 