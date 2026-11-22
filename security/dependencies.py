"""Dependências do FastAPI para autenticação (quem é o usuário) e autorização (o que ele pode fazer)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_db
from model.usuario import PerfilUsuario, Usuario
from security.security import TokenInvalido, decodificar_token

# auto_error=False: o erro é tratado aqui para sempre devolver 401 com a nossa mensagem.
bearer_scheme = HTTPBearer(auto_error=False)


def _erro_credenciais() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_usuario_atual(
    credenciais: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Autenticação: valida o token JWT e devolve o usuário dono do token."""
    if credenciais is None:
        raise _erro_credenciais()

    try:
        usuario_id = decodificar_token(credenciais.credentials)
    except TokenInvalido:
        raise _erro_credenciais()

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:  # usuário removido depois da emissão do token
        raise _erro_credenciais()
    return usuario


def exige_perfil(*perfis: PerfilUsuario):
    """Autorização: permite a rota somente aos perfis informados (senão, 403)."""

    def verificador(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
        if usuario.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não possui permissão para executar esta operação.",
            )
        return usuario

    return verificador


requer_administrador = exige_perfil(PerfilUsuario.ADMINISTRADOR)
