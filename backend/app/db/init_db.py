import app.models  # noqa: F401
from app.db.session import Base, engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("BASE DE DONNÉES INITIALISÉE")
    print("TABLES :", list(Base.metadata.tables.keys()))
