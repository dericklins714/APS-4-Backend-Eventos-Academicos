from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schema.inscricao_schema import InscricaoResponse
from schema.participante_schema import ParticipanteResponse
from security.dependencies import get_usuario_atual, requer_administrador
from service import inscricao_service

router = APIRouter(prefix="/eventos", tags=["Inscrições"])


# Qualquer usuário autenticado
@router.post(
    "/{evento_id}/inscricoes/{participante_id}",
    response_model=InscricaoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_usuario_atual)],
)
def inscrever_participante(evento_id: int, participante_id: int, db: Session = Depends(get_db)):
    inscricao = inscricao_service.inscrever_participante(db, evento_id, participante_id)
    return InscricaoResponse(
        mensagem="Inscrição realizada com sucesso.",
        id=inscricao.id,
        evento_id=inscricao.evento_id,
        participante_id=inscricao.participante_id,
        data_inscricao=inscricao.data_inscricao,
    )


# Administrador (a lista expõe dados pessoais dos inscritos)
@router.get(
    "/{evento_id}/inscricoes",
    response_model=list[ParticipanteResponse],
    dependencies=[Depends(requer_administrador)],
)
def listar_inscritos(evento_id: int, db: Session = Depends(get_db)):
    return inscricao_service.listar_inscritos(db, evento_id)
