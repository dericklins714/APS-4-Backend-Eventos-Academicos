from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.participante import Participante
from schema.participante_schema import ParticipanteCreate, ParticipanteUpdate
from service.utils import salvar


def _email_em_uso(db: Session, email: str, ignorar_id: int | None = None) -> bool:
    consulta = select(Participante.id).where(func.lower(Participante.email) == email)
    if ignorar_id is not None:
        consulta = consulta.where(Participante.id != ignorar_id)
    return db.scalar(consulta) is not None


def cadastrar_participante(db: Session, dados: ParticipanteCreate) -> Participante:
    email = str(dados.email).lower()

    if _email_em_uso(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um participante cadastrado com este e-mail.",
        )

    participante = Participante(**{**dados.model_dump(), "email": email})
    db.add(participante)
    # A restrição UNIQUE do banco protege contra condições de corrida.
    salvar(db, "Já existe um participante cadastrado com este e-mail.")
    db.refresh(participante)
    return participante


def listar_participantes(db: Session) -> list[Participante]:
    return list(db.scalars(select(Participante).order_by(Participante.id)).all())


def buscar_participante(db: Session, participante_id: int) -> Participante:
    participante = db.get(Participante, participante_id)
    if participante is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participante não encontrado.",
        )
    return participante


def atualizar_participante(
    db: Session, participante_id: int, dados: ParticipanteUpdate
) -> Participante:
    participante = buscar_participante(db, participante_id)
    novo_email = str(dados.email).lower()

    if _email_em_uso(db, novo_email, ignorar_id=participante_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe outro participante com este e-mail.",
        )

    participante.nome = dados.nome
    participante.email = novo_email
    participante.curso = dados.curso

    salvar(db, "Já existe outro participante com este e-mail.")
    db.refresh(participante)
    return participante


def excluir_participante(db: Session, participante_id: int) -> None:
    """Exclui o participante e, em cascata, as suas inscrições."""
    participante = buscar_participante(db, participante_id)
    db.delete(participante)
    salvar(db)
