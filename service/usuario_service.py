from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from model.usuario import PerfilUsuario, Usuario
from schema.usuario_schema import UsuarioCreate
from security.security import gerar_hash_senha
from service.utils import salvar

MENSAGEM_EMAIL_DUPLICADO = "Já existe um usuário cadastrado com este e-mail."


def buscar_por_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))


def criar_usuario(
    db: Session, nome: str, email: str, senha: str, perfil: PerfilUsuario
) -> Usuario:
    email = email.lower()

    if buscar_por_email(db, email) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=MENSAGEM_EMAIL_DUPLICADO)

    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=gerar_hash_senha(senha),  # somente o hash é armazenado
        perfil=perfil.value,
    )
    db.add(usuario)
    salvar(db, MENSAGEM_EMAIL_DUPLICADO)
    db.refresh(usuario)
    return usuario


def cadastrar_usuario(db: Session, dados: UsuarioCreate) -> Usuario:
    """Cadastro público: o perfil é sempre 'usuario', definido pelo servidor."""
    return criar_usuario(db, dados.nome, str(dados.email), dados.senha, PerfilUsuario.USUARIO)


def criar_administrador_inicial(db: Session, nome: str, email: str, senha: str) -> Usuario | None:
    """Cria o administrador inicial se ainda não existir um usuário com esse e-mail."""
    if buscar_por_email(db, email) is not None:
        return None
    return criar_usuario(db, nome, email, senha, PerfilUsuario.ADMINISTRADOR)
