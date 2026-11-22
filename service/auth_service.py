from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from model.usuario import Usuario
from schema.usuario_schema import LoginRequest, TokenResponse
from security.security import (
    HASH_FALSO,
    criar_token_acesso,
    verificar_senha,
)
from service import usuario_service


def autenticar(db: Session, dados: LoginRequest) -> Usuario:
    usuario = usuario_service.buscar_por_email(db, str(dados.email))

    # Sempre verifica um hash, mesmo sem usuário, para não revelar se o e-mail existe.
    hash_comparado = usuario.senha_hash if usuario is not None else HASH_FALSO
    senha_correta = verificar_senha(dados.senha, hash_comparado)

    if usuario is None or not senha_correta:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def login(db: Session, dados: LoginRequest) -> TokenResponse:
    usuario = autenticar(db, dados)
    return TokenResponse(access_token=criar_token_acesso(usuario.id), token_type="bearer")
