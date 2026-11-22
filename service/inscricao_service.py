from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.inscricao import Inscricao
from model.participante import Participante
from service import evento_service, participante_service
from service.utils import salvar


def inscrever_participante(db: Session, evento_id: int, participante_id: int) -> Inscricao:
    # 1 e 2. Evento e participante precisam existir (levantam 404 caso contrário).
    evento = evento_service.buscar_evento(db, evento_id)
    participante_service.buscar_participante(db, participante_id)

    # 3. Inscrição duplicada.
    ja_inscrito = db.scalar(
        select(Inscricao.id).where(
            Inscricao.evento_id == evento_id,
            Inscricao.participante_id == participante_id,
        )
    )
    if ja_inscrito is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Participante já está inscrito neste evento.",
        )

    # 4. Vagas disponíveis.
    total_inscritos = db.scalar(
        select(func.count(Inscricao.id)).where(Inscricao.evento_id == evento_id)
    )
    if total_inscritos >= evento.capacidade:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não existem vagas disponíveis para este evento.",
        )

    inscricao = Inscricao(evento_id=evento_id, participante_id=participante_id)
    db.add(inscricao)
    # A UniqueConstraint do banco cobre o caso de requisições simultâneas.
    salvar(db, "Participante já está inscrito neste evento.")
    db.refresh(inscricao)
    return inscricao


def listar_inscritos(db: Session, evento_id: int) -> list[Participante]:
    evento_service.buscar_evento(db, evento_id)

    consulta = (
        select(Participante)
        .join(Inscricao, Inscricao.participante_id == Participante.id)
        .where(Inscricao.evento_id == evento_id)
        .order_by(Participante.nome)
    )
    return list(db.scalars(consulta).all())
