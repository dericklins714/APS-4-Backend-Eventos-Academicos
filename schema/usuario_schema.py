from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from model.usuario import PerfilUsuario

TAMANHO_MINIMO_SENHA = 8


class UsuarioCreate(BaseModel):
    # extra="forbid": campos não previstos (como "perfil") são rejeitados com 422,
    # impedindo que o cliente tente se definir como administrador.
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    senha: str = Field(..., min_length=TAMANHO_MINIMO_SENHA, max_length=128)

    @field_validator("nome")
    @classmethod
    def nome_nao_vazio(cls, valor: str):
        valor = valor.strip()
        if not valor:
            raise ValueError("O campo não pode ser vazio.")
        return valor

    @field_validator("senha")
    @classmethod
    def senha_valida(cls, valor: str):
        if not valor.strip():
            raise ValueError("A senha não pode ser vazia.")
        return valor


class UsuarioResponse(BaseModel):
    """Nunca inclui senha nem hash."""

    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUsuario

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
