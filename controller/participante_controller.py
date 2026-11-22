from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schema.participante_schema import (
    ParticipanteCreate,
    ParticipanteResponse,
    ParticipanteUpdate,
)
from security.dependencies import get_usuario_atual, requer_administrador
from service import participante_service

router = APIRouter(prefix="/participantes", tags=["Participantes"])


# Qualquer usuário autenticado (o usuário comum precisa de um cadastro de participante para se inscrever)
@router.post(
    "",
    response_model=ParticipanteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_usuario_atual)],
)
def cadastrar_participante(dados: ParticipanteCreate, db: Session = Depends(get_db)):
    return participante_service.cadastrar_participante(db, dados)


@router.get(
    "",
    response_model=list[ParticipanteResponse],
    dependencies=[Depends(get_usuario_atual)],
)
def listar_participantes(db: Session = Depends(get_db)):
    return participante_service.listar_participantes(db)


@router.get(
    "/{participante_id}",
    response_model=ParticipanteResponse,
    dependencies=[Depends(get_usuario_atual)],
)
def consultar_participante(participante_id: int, db: Session = Depends(get_db)):
    return participante_service.buscar_participante(db, participante_id)


# Administrador
@router.put(
    "/{participante_id}",
    response_model=ParticipanteResponse,
    dependencies=[Depends(requer_administrador)],
)
def atualizar_participante(
    participante_id: int, dados: ParticipanteUpdate, db: Session = Depends(get_db)
):
    return participante_service.atualizar_participante(db, participante_id, dados)


@router.delete(
    "/{participante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requer_administrador)],
)
def excluir_participante(participante_id: int, db: Session = Depends(get_db)):
    participante_service.excluir_participante(db, participante_id)
