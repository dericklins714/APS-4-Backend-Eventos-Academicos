from contextlib import asynccontextmanager

from fastapi import FastAPI

from controller.auth_controller import router as auth_router
from controller.evento_controller import router as evento_router
from controller.inscricao_controller import router as inscricao_router
from controller.participante_controller import router as participante_router
from controller.relatorio_controller import router as relatorio_router
from controller.usuario_controller import router as usuario_router
from database import SessionLocal, criar_tabelas
from security.config import settings
from service import usuario_service


def criar_admin_inicial():
    """Cria o administrador inicial a partir das variáveis ADMIN_* (se informadas)."""
    if not (settings.ADMIN_EMAIL and settings.ADMIN_SENHA):
        return
    db = SessionLocal()
    try:
        usuario_service.criar_administrador_inicial(
            db, settings.ADMIN_NOME, settings.ADMIN_EMAIL, settings.ADMIN_SENHA
        )
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    criar_tabelas()
    criar_admin_inicial()
    yield


app = FastAPI(
    title="API de Eventos Acadêmicos",
    description=(
        "API RESTful para gerenciamento de eventos, participantes e inscrições, "
        "com persistência em SQLite, relatórios consolidados, autenticação JWT "
        "e controle de acesso por perfis."
    ),
    version="3.0.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(usuario_router)
app.include_router(evento_router)
app.include_router(participante_router)
app.include_router(inscricao_router)
app.include_router(relatorio_router)


@app.get("/", tags=["Sistema"])
def inicio():
    return {
        "mensagem": "API de Eventos Acadêmicos funcionando!",
        "documentacao": "/docs",
    }
