from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ParticipanteBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    curso: str = Field(..., min_length=1, max_length=150)

    @field_validator("nome", "curso")
    @classmethod
    def nao_pode_ser_vazio(cls, valor: str):
        valor = valor.strip()
        if not valor:
            raise ValueError("O campo não pode ser vazio.")
        return valor


class ParticipanteCreate(ParticipanteBase):
    pass


class ParticipanteUpdate(ParticipanteBase):
    pass


class ParticipanteResponse(ParticipanteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
