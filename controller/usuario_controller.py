from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schema.usuario_schema import UsuarioCreate, UsuarioResponse
from service import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(dados: UsuarioCreate, db: Session = Depends(get_db)):
    """Rota pública. O perfil do novo usuário é sempre `usuario`."""
    return usuario_service.cadastrar_usuario(db, dados)
