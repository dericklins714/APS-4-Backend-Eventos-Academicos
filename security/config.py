"""Configurações de segurança lidas de variáveis de ambiente (ou do arquivo .env)."""
import os

from dotenv import load_dotenv

# Lê o arquivo .env (se existir). Variáveis já definidas no ambiente têm prioridade.
load_dotenv()

TAMANHO_MINIMO_CHAVE = 32


class Settings:
    def __init__(self):
        self.SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
        if len(self.SECRET_KEY) < TAMANHO_MINIMO_CHAVE:
            raise RuntimeError(
                "Variável de ambiente SECRET_KEY ausente ou curta demais "
                f"(mínimo {TAMANHO_MINIMO_CHAVE} caracteres). Copie o arquivo .env.example "
                "para .env e preencha a chave. Para gerar uma: "
                'python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )

        self.JWT_ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

        # Administrador inicial (opcional)
        self.ADMIN_NOME = os.getenv("ADMIN_NOME", "Administrador").strip() or "Administrador"
        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip().lower()
        self.ADMIN_SENHA = os.getenv("ADMIN_SENHA", "")


settings = Settings()
