from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.evento import Evento
from model.inscricao import Inscricao
from model.participante import Participante


def relatorio_ocupacao_eventos(db: Session) -> list[dict]:
    """Ocupação de cada evento (inclui eventos sem inscrições)."""
    total_inscritos = func.count(Inscricao.id)

    consulta = (
        select(
            Evento.id,
            Evento.titulo,
            Evento.capacidade,
            total_inscritos.label("total_inscritos"),
        )
        .outerjoin(Inscricao, Inscricao.evento_id == Evento.id)
        .group_by(Evento.id, Evento.titulo, Evento.capacidade)
        .order_by(Evento.id)
    )

    resultado = []
    for linha in db.execute(consulta).all():
        capacidade = linha.capacidade
        inscritos = linha.total_inscritos
        percentual = round(inscritos / capacidade * 100, 2) if capacidade > 0 else 0.0
        resultado.append(
            {
                "evento_id": linha.id,
                "titulo": linha.titulo,
                "capacidade": capacidade,
                "total_inscritos": inscritos,
                "vagas_disponiveis": max(capacidade - inscritos, 0),
                "percentual_ocupacao": percentual,
            }
        )
    return resultado


def relatorio_eventos_por_categoria(db: Session) -> list[dict]:
    """Consolida eventos por categoria.

    As inscrições são contadas primeiro por evento (subconsulta) para que a
    capacidade não seja multiplicada pelo JOIN.
    """
    inscricoes_por_evento = (
        select(
            Inscricao.evento_id.label("evento_id"),
            func.count(Inscricao.id).label("qtd"),
        )
        .group_by(Inscricao.evento_id)
        .subquery()
    )

    consulta = (
        select(
            Evento.categoria,
            func.count(Evento.id).label("total_eventos"),
            func.coalesce(func.sum(Evento.capacidade), 0).label("capacidade_total"),
            func.coalesce(func.sum(inscricoes_por_evento.c.qtd), 0).label("total_inscricoes"),
        )
        .outerjoin(inscricoes_por_evento, inscricoes_por_evento.c.evento_id == Evento.id)
        .group_by(Evento.categoria)
        .order_by(Evento.categoria)
    )

    return [
        {
            "categoria": linha.categoria,
            "total_eventos": int(linha.total_eventos),
            "capacidade_total": int(linha.capacidade_total),
            "total_inscricoes": int(linha.total_inscricoes),
        }
        for linha in db.execute(consulta).all()
    ]


def relatorio_participacao_por_curso(db: Session) -> list[dict]:
    """Participantes e inscrições por curso.

    COUNT(DISTINCT participante.id) evita contar o mesmo participante
    várias vezes quando ele possui diversas inscrições.
    """
    consulta = (
        select(
            Participante.curso,
            func.count(func.distinct(Participante.id)).label("total_participantes"),
            func.count(Inscricao.id).label("total_inscricoes"),
        )
        .outerjoin(Inscricao, Inscricao.participante_id == Participante.id)
        .group_by(Participante.curso)
        .order_by(Participante.curso)
    )

    return [
        {
            "curso": linha.curso,
            "total_participantes": int(linha.total_participantes),
            "total_inscricoes": int(linha.total_inscricoes),
        }
        for linha in db.execute(consulta).all()
    ]
