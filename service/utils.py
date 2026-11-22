from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session


def salvar(db: Session, mensagem_conflito: str = "Operação não permitida: conflito de integridade dos dados."):
    """Confirma a transação tratando falhas de persistência.

    Nenhuma mensagem técnica do banco é devolvida ao cliente.
    """
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=mensagem_conflito,
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao acessar o banco de dados.",
        )
