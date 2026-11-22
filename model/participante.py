from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Participante(Base):
    __tablename__ = "participantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    curso: Mapped[str] = mapped_column(String(150), nullable=False, index=True)

    # Excluir um participante exclui também as suas inscrições (evita registros órfãos).
    inscricoes: Mapped[list["Inscricao"]] = relationship(  # noqa: F821
        back_populates="participante",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
