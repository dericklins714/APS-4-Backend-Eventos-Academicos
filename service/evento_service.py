from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.evento import Evento
from model.inscricao import Inscricao
from schema.evento_schema import EventoCreate, EventoUpdate
from service.utils import salvar


def cadastrar_evento(db: Session, dados: EventoCreate) -> Evento:
    evento = Evento(**dados.model_dump())
    db.add(evento)
    salvar(db)
    db.refresh(evento)
    return evento


def listar_eventos(db: Session) -> list[Evento]:
    return list(db.scalars(select(Evento).order_by(Evento.id)).all())


def buscar_evento(db: Session, evento_id: int) -> Evento:
    evento = db.get(Evento, evento_id)
    if evento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento não encontrado.",
        )
    return evento


def atualizar_evento(db: Session, evento_id: int, dados: EventoUpdate) -> Evento:
    evento = buscar_evento(db, evento_id)

    total_inscritos = db.scalar(
        select(func.count(Inscricao.id)).where(Inscricao.evento_id == evento_id)
    )
    if dados.capacidade < total_inscritos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A capacidade não pode ser menor que o número de inscritos no evento.",
        )

    for campo, valor in dados.model_dump().items():
        setattr(evento, campo, valor)

    salvar(db)
    db.refresh(evento)
    return evento


def excluir_evento(db: Session, evento_id: int) -> None:
    """Exclui o evento e, em cascata, as inscrições relacionadas."""
    evento = buscar_evento(db, evento_id)
    db.delete(evento)
    salvar(db)
