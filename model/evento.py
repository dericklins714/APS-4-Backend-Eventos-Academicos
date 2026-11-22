from datetime import date, time

from sqlalchemy import Date, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Evento(Base):
    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    horario: Mapped[time] = mapped_column(Time, nullable=False)
    local: Mapped[str] = mapped_column(String(150), nullable=False)
    capacidade: Mapped[int] = mapped_column(Integer, nullable=False)
    categoria: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Excluir um evento exclui também as suas inscrições (evita registros órfãos).
    inscricoes: Mapped[list["Inscricao"]] = relationship(  # noqa: F821
        back_populates="evento",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
