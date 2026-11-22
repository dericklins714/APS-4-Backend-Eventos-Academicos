from pydantic import BaseModel


class OcupacaoEventoResponse(BaseModel):
    evento_id: int
    titulo: str
    capacidade: int
    total_inscritos: int
    vagas_disponiveis: int
    percentual_ocupacao: float


class CategoriaResponse(BaseModel):
    categoria: str
    total_eventos: int
    capacidade_total: int
    total_inscricoes: int


class CursoResponse(BaseModel):
    curso: str
    total_participantes: int
    total_inscricoes: int
