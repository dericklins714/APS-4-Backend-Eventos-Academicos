from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schema.relatorio_schema import (
    CategoriaResponse,
    CursoResponse,
    OcupacaoEventoResponse,
)
from security.dependencies import requer_administrador
from service import relatorio_service

# Todas as rotas de relatório exigem perfil administrador.
router = APIRouter(
    prefix="/relatorios",
    tags=["Relatórios"],
    dependencies=[Depends(requer_administrador)],
)


@router.get("/eventos/ocupacao", response_model=list[OcupacaoEventoResponse])
def relatorio_ocupacao(db: Session = Depends(get_db)):
    return relatorio_service.relatorio_ocupacao_eventos(db)


@router.get("/eventos/categorias", response_model=list[CategoriaResponse])
def relatorio_categorias(db: Session = Depends(get_db)):
    return relatorio_service.relatorio_eventos_por_categoria(db)


@router.get("/participantes/cursos", response_model=list[CursoResponse])
def relatorio_cursos(db: Session = Depends(get_db)):
    return relatorio_service.relatorio_participacao_por_curso(db)
