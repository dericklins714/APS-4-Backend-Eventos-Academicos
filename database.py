"""Configuração do banco de dados SQLite com SQLAlchemy.

O arquivo do banco (eventos.db) é criado na mesma pasta deste arquivo,
ou seja, na raiz do projeto.
"""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'eventos.db'}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def ativar_chaves_estrangeiras(conexao, _registro):
    """O SQLite não valida chaves estrangeiras por padrão; ativamos aqui."""
    cursor = conexao.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Classe base de todos os modelos SQLAlchemy."""


def criar_tabelas():
    """Cria as tabelas a partir dos modelos (se ainda não existirem)."""
    # Importar os modelos registra as tabelas no metadata da Base.
    from model import evento, inscricao, participante, usuario  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependência do FastAPI: abre uma sessão e a encerra ao final da requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
