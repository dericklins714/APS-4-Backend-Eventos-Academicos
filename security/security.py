"""Hash de senhas (Argon2 via pwdlib) e geração/validação de tokens JWT (PyJWT)."""
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from security.config import settings

# PasswordHash.recommended() usa Argon2 com parâmetros seguros e salt aleatório.
_password_hash = PasswordHash.recommended()


class TokenInvalido(Exception):
    """Token ausente, malformado, adulterado, expirado ou sem as informações necessárias."""


def gerar_hash_senha(senha: str) -> str:
    return _password_hash.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return _password_hash.verify(senha, senha_hash)
    except Exception:
        return False


# Hash usado para gastar o mesmo tempo de verificação quando o e-mail não existe,
# dificultando descobrir por tempo de resposta quais e-mails estão cadastrados.
HASH_FALSO = gerar_hash_senha("senha-falsa-para-igualar-tempo-de-resposta")


def criar_token_acesso(usuario_id: int, expira_em: timedelta | None = None) -> str:
    agora = datetime.now(timezone.utc)
    validade = expira_em if expira_em is not None else timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(usuario_id),  # identificador do usuário
        "iat": agora,            # emitido em
        "exp": agora + validade, # expira em
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decodificar_token(token: str) -> int:
    """Valida assinatura e expiração e devolve o id do usuário do token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise TokenInvalido()
