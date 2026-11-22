"""Configuração compartilhada dos testes.

Os testes usam um banco SQLite em memória (não alteram eventos.db) e uma chave
secreta própria de teste, definida ANTES de importar a aplicação.
"""
import os

os.environ["SECRET_KEY"] = "chave-somente-para-testes-0123456789-abcdefghij"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from model import evento, inscricao, participante, usuario  # noqa: E402,F401
from model.usuario import PerfilUsuario  # noqa: E402
from service import usuario_service  # noqa: E402

SENHA_ADMIN = "admin-senha-123"
SENHA_USUARIO = "usuario-senha-123"


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk(conexao, _registro):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    fabrica = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override():
        db = fabrica()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield fabrica
    app.dependency_overrides.clear()


@pytest.fixture()
def anon(session_factory):
    """Cliente sem token."""
    return TestClient(app)


def _cliente_autenticado(session_factory, nome, email, senha, perfil):
    with session_factory() as db:
        usuario_service.criar_usuario(db, nome, email, senha, perfil)
    resposta = TestClient(app).post("/auth/login", json={"email": email, "senha": senha})
    assert resposta.status_code == 200
    token = resposta.json()["access_token"]
    cliente = TestClient(app)
    cliente.headers.update({"Authorization": f"Bearer {token}"})
    return cliente


@pytest.fixture()
def admin_client(session_factory):
    return _cliente_autenticado(
        session_factory, "Admin", "admin@exemplo.com", SENHA_ADMIN, PerfilUsuario.ADMINISTRADOR
    )


@pytest.fixture()
def user_client(session_factory):
    return _cliente_autenticado(
        session_factory, "Aluno", "aluno@exemplo.com", SENHA_USUARIO, PerfilUsuario.USUARIO
    )
