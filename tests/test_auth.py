"""Testes de autenticação, JWT e autorização por perfil (APS 4)."""
from datetime import timedelta

import jwt
from fastapi.testclient import TestClient

from main import app
from model.usuario import Usuario
from security.config import settings
from security.security import criar_token_acesso

EVENTO = {
    "titulo": "Workshop", "descricao": "Descrição", "data": "2026-10-15",
    "horario": "19:00:00", "local": "Lab", "capacidade": 5, "categoria": "Workshop",
}


def com_token(token):
    cliente = TestClient(app)
    cliente.headers.update({"Authorization": f"Bearer {token}"})
    return cliente


# ---------- cadastro de usuários ----------
def test_cadastro_usuario_retorna_sem_senha_e_perfil_usuario(anon):
    r = anon.post("/usuarios", json={"nome": "Aluno", "email": "A@Exemplo.com", "senha": "senha_segura"})
    assert r.status_code == 201
    corpo = r.json()
    assert corpo == {"id": 1, "nome": "Aluno", "email": "a@exemplo.com", "perfil": "usuario"}
    assert "senha" not in corpo and "senha_hash" not in corpo


def test_senha_armazenada_como_hash(anon, session_factory):
    anon.post("/usuarios", json={"nome": "Aluno", "email": "a@exemplo.com", "senha": "senha_segura"})
    with session_factory() as db:
        u = db.query(Usuario).one()
        assert u.senha_hash != "senha_segura"
        assert u.senha_hash.startswith("$argon2")
        assert "senha_segura" not in u.senha_hash


def test_email_duplicado(anon):
    dados = {"nome": "A", "email": "a@exemplo.com", "senha": "senha_segura"}
    assert anon.post("/usuarios", json=dados).status_code == 201
    r = anon.post("/usuarios", json={**dados, "email": "A@EXEMPLO.com"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Já existe um usuário cadastrado com este e-mail."


def test_validacoes_cadastro(anon):
    base = {"nome": "A", "email": "a@exemplo.com", "senha": "senha_segura"}
    assert anon.post("/usuarios", json={**base, "nome": "   "}).status_code == 422
    assert anon.post("/usuarios", json={**base, "email": "invalido"}).status_code == 422
    assert anon.post("/usuarios", json={**base, "senha": ""}).status_code == 422
    assert anon.post("/usuarios", json={**base, "senha": "curta"}).status_code == 422
    assert anon.post("/usuarios", json={**base, "senha": "         "}).status_code == 422
    assert anon.post("/usuarios", json={"nome": "A", "senha": "senha_segura"}).status_code == 422


def test_nao_e_possivel_se_definir_administrador(anon):
    r = anon.post("/usuarios", json={
        "nome": "Hacker", "email": "h@exemplo.com", "senha": "senha_segura", "perfil": "administrador"})
    assert r.status_code == 422


# ---------- login ----------
def test_login_valido(anon):
    anon.post("/usuarios", json={"nome": "A", "email": "a@exemplo.com", "senha": "senha_segura"})
    r = anon.post("/auth/login", json={"email": "a@exemplo.com", "senha": "senha_segura"})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert r.json()["access_token"]


def test_login_invalido_mensagem_igual(anon):
    anon.post("/usuarios", json={"nome": "A", "email": "a@exemplo.com", "senha": "senha_segura"})
    senha_errada = anon.post("/auth/login", json={"email": "a@exemplo.com", "senha": "errada123"})
    email_errado = anon.post("/auth/login", json={"email": "x@exemplo.com", "senha": "senha_segura"})
    assert senha_errada.status_code == email_errado.status_code == 401
    assert senha_errada.json() == email_errado.json() == {"detail": "E-mail ou senha inválidos."}


# ---------- token ----------
def test_rota_protegida_sem_token(anon):
    r = anon.get("/eventos")
    assert r.status_code == 401
    assert r.json()["detail"] == "Não foi possível validar as credenciais."


def test_token_invalido_adulterado_e_chave_errada(anon, user_client):
    assert com_token("abc.def.ghi").get("/eventos").status_code == 401

    token_valido = user_client.headers["Authorization"].split(" ")[1]
    adulterado = token_valido[:-3] + ("AAA" if not token_valido.endswith("AAA") else "BBB")
    assert com_token(adulterado).get("/eventos").status_code == 401

    outra_chave = jwt.encode({"sub": "1", "iat": 1, "exp": 9999999999}, "outra-chave-" * 4, algorithm="HS256")
    assert com_token(outra_chave).get("/eventos").status_code == 401


def test_token_expirado(user_client):
    token = criar_token_acesso(1, expira_em=timedelta(seconds=-10))
    r = com_token(token).get("/eventos")
    assert r.status_code == 401
    assert r.json()["detail"] == "Não foi possível validar as credenciais."


def test_token_sem_usuario_correspondente(anon):
    token = criar_token_acesso(9999)
    assert com_token(token).get("/auth/me").status_code == 401


def test_token_valido_e_me(user_client):
    assert user_client.get("/eventos").status_code == 200
    r = user_client.get("/auth/me")
    assert r.status_code == 200
    assert r.json() == {"id": 1, "nome": "Aluno", "email": "aluno@exemplo.com", "perfil": "usuario"}


def test_me_sem_token(anon):
    assert anon.get("/auth/me").status_code == 401


def test_token_contem_sub_iat_exp(user_client):
    token = user_client.headers["Authorization"].split(" ")[1]
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == "1" and "iat" in payload and "exp" in payload


# ---------- autorização por perfil ----------
def test_usuario_comum_nao_executa_operacoes_administrativas(admin_client, user_client):
    evento = admin_client.post("/eventos", json=EVENTO).json()

    assert user_client.post("/eventos", json=EVENTO).status_code == 403
    assert user_client.put(f"/eventos/{evento['id']}", json=EVENTO).status_code == 403
    assert user_client.delete(f"/eventos/{evento['id']}").status_code == 403
    for rota in ("eventos/ocupacao", "eventos/categorias", "participantes/cursos"):
        r = user_client.get(f"/relatorios/{rota}")
        assert r.status_code == 403
        assert r.json()["detail"] == "Você não possui permissão para executar esta operação."
    assert user_client.get(f"/eventos/{evento['id']}/inscricoes").status_code == 403
    assert admin_client.get(f"/eventos/{evento['id']}").status_code == 200  # nada foi alterado


def test_administrador_executa_operacoes_administrativas(admin_client):
    r = admin_client.post("/eventos", json=EVENTO)
    assert r.status_code == 201
    evento_id = r.json()["id"]
    assert admin_client.put(f"/eventos/{evento_id}", json={**EVENTO, "titulo": "Novo"}).status_code == 200
    assert admin_client.get(f"/eventos/{evento_id}/inscricoes").status_code == 200
    for rota in ("eventos/ocupacao", "eventos/categorias", "participantes/cursos"):
        assert admin_client.get(f"/relatorios/{rota}").status_code == 200
    assert admin_client.delete(f"/eventos/{evento_id}").status_code == 204


def test_usuario_comum_pode_cadastrar_participante_e_se_inscrever(admin_client, user_client):
    evento = admin_client.post("/eventos", json=EVENTO).json()
    p = user_client.post("/participantes", json={"nome": "João", "email": "j@e.com", "curso": "ADS"})
    assert p.status_code == 201
    r = user_client.post(f"/eventos/{evento['id']}/inscricoes/{p.json()['id']}")
    assert r.status_code == 201
    assert user_client.get("/participantes").status_code == 200
    # atualizar/excluir participante é restrito ao administrador
    assert user_client.put(f"/participantes/{p.json()['id']}",
                           json={"nome": "X", "email": "j@e.com", "curso": "ADS"}).status_code == 403
    assert user_client.delete(f"/participantes/{p.json()['id']}").status_code == 403


def test_rotas_publicas(anon):
    assert anon.get("/").status_code == 200
    assert anon.get("/docs").status_code == 200
    assert anon.get("/openapi.json").status_code == 200


def test_rotas_protegidas_sem_token(anon):
    protegidas = [
        ("post", "/eventos"), ("put", "/eventos/1"), ("delete", "/eventos/1"),
        ("post", "/participantes"), ("put", "/participantes/1"), ("delete", "/participantes/1"),
        ("post", "/eventos/1/inscricoes/1"), ("get", "/eventos/1/inscricoes"),
        ("get", "/relatorios/eventos/ocupacao"), ("get", "/relatorios/eventos/categorias"),
        ("get", "/relatorios/participantes/cursos"), ("get", "/participantes"), ("get", "/auth/me"),
    ]
    for metodo, rota in protegidas:
        assert getattr(anon, metodo)(rota).status_code == 401, (metodo, rota)
