"""Testes das funcionalidades da APS 3 (eventos, participantes, inscrições e relatórios),
agora executados por um usuário administrador autenticado.

Execute na raiz do projeto:  pytest -v
"""
import pytest


@pytest.fixture()
def client(admin_client):
    """Nos testes da APS 3 usamos um cliente autenticado como administrador."""
    return admin_client


def novo_evento(client, titulo="Workshop de Python", capacidade=2, categoria="Workshop"):
    r = client.post("/eventos", json={
        "titulo": titulo, "descricao": "Descrição", "data": "2026-10-15",
        "horario": "19:00:00", "local": "Lab 2", "capacidade": capacidade,
        "categoria": categoria,
    })
    assert r.status_code == 201
    return r.json()


def novo_participante(client, email="joao@email.com", curso="ADS"):
    r = client.post("/participantes", json={"nome": "João", "email": email, "curso": curso})
    assert r.status_code == 201
    return r.json()


def test_crud_evento(client):
    e = novo_evento(client)
    assert client.get(f"/eventos/{e['id']}").json()["titulo"] == "Workshop de Python"
    r = client.put(f"/eventos/{e['id']}", json={**e, "titulo": "Novo título"})
    assert r.status_code == 200 and r.json()["titulo"] == "Novo título"
    assert client.delete(f"/eventos/{e['id']}").status_code == 204
    assert client.get(f"/eventos/{e['id']}").status_code == 404


def test_validacoes(client):
    r = client.post("/eventos", json={
        "titulo": "x", "descricao": "d", "data": "2026-10-15", "horario": "19:00:00",
        "local": "l", "capacidade": 0, "categoria": "Workshop"})
    assert r.status_code == 422
    r = client.post("/participantes", json={"nome": "A", "email": "invalido", "curso": "ADS"})
    assert r.status_code == 422


def test_email_duplicado(client):
    novo_participante(client)
    r = client.post("/participantes", json={"nome": "B", "email": "JOAO@email.com", "curso": "ADS"})
    assert r.status_code == 409
    assert r.json()["detail"] == "Já existe um participante cadastrado com este e-mail."


def test_inscricao_fluxo_e_erros(client):
    e = novo_evento(client, capacidade=1)
    p1 = novo_participante(client)
    p2 = novo_participante(client, email="maria@email.com")

    r = client.post(f"/eventos/{e['id']}/inscricoes/{p1['id']}")
    assert r.status_code == 201

    r = client.post(f"/eventos/{e['id']}/inscricoes/{p1['id']}")
    assert r.status_code == 409 and "já está inscrito" in r.json()["detail"]

    r = client.post(f"/eventos/{e['id']}/inscricoes/{p2['id']}")
    assert r.status_code == 409 and "vagas" in r.json()["detail"]

    assert client.post(f"/eventos/999/inscricoes/{p1['id']}").status_code == 404
    assert client.post(f"/eventos/{e['id']}/inscricoes/999").status_code == 404

    inscritos = client.get(f"/eventos/{e['id']}/inscricoes").json()
    assert [i["id"] for i in inscritos] == [p1["id"]]


def test_capacidade_nao_pode_ficar_menor_que_inscritos(client):
    e = novo_evento(client, capacidade=2)
    p = novo_participante(client)
    client.post(f"/eventos/{e['id']}/inscricoes/{p['id']}")
    p2 = novo_participante(client, email="b@b.com")
    client.post(f"/eventos/{e['id']}/inscricoes/{p2['id']}")
    r = client.put(f"/eventos/{e['id']}", json={**e, "capacidade": 1})
    assert r.status_code == 409


def test_exclusao_remove_inscricoes(client):
    e = novo_evento(client)
    p = novo_participante(client)
    client.post(f"/eventos/{e['id']}/inscricoes/{p['id']}")
    assert client.delete(f"/participantes/{p['id']}").status_code == 204
    assert client.get(f"/eventos/{e['id']}/inscricoes").json() == []
    assert client.get("/relatorios/eventos/ocupacao").json()[0]["total_inscritos"] == 0


def test_relatorios_vazios(client):
    for rota in ("eventos/ocupacao", "eventos/categorias", "participantes/cursos"):
        r = client.get(f"/relatorios/{rota}")
        assert r.status_code == 200 and r.json() == []


def test_relatorios_consolidados(client):
    e1 = novo_evento(client, titulo="A", capacidade=4, categoria="Workshop")
    e2 = novo_evento(client, titulo="B", capacidade=10, categoria="Workshop")
    e3 = novo_evento(client, titulo="C", capacidade=5, categoria="Palestra")  # sem inscrições
    p1 = novo_participante(client, email="a@a.com", curso="ADS")
    p2 = novo_participante(client, email="b@b.com", curso="ADS")
    p3 = novo_participante(client, email="c@c.com", curso="ES")
    novo_participante(client, email="d@d.com", curso="Direito")  # sem inscrições

    for ev, ps in ((e1, (p1, p2, p3)), (e2, (p1,))):
        for p in ps:
            assert client.post(f"/eventos/{ev['id']}/inscricoes/{p['id']}").status_code == 201

    ocupacao = {o["evento_id"]: o for o in client.get("/relatorios/eventos/ocupacao").json()}
    assert ocupacao[e1["id"]] == {
        "evento_id": e1["id"], "titulo": "A", "capacidade": 4, "total_inscritos": 3,
        "vagas_disponiveis": 1, "percentual_ocupacao": 75.0}
    assert ocupacao[e3["id"]]["total_inscritos"] == 0
    assert ocupacao[e3["id"]]["percentual_ocupacao"] == 0.0

    cats = {c["categoria"]: c for c in client.get("/relatorios/eventos/categorias").json()}
    assert cats["Workshop"] == {
        "categoria": "Workshop", "total_eventos": 2, "capacidade_total": 14, "total_inscricoes": 4}
    assert cats["Palestra"] == {
        "categoria": "Palestra", "total_eventos": 1, "capacidade_total": 5, "total_inscricoes": 0}

    cursos = {c["curso"]: c for c in client.get("/relatorios/participantes/cursos").json()}
    assert cursos["ADS"] == {"curso": "ADS", "total_participantes": 2, "total_inscricoes": 3}
    assert cursos["ES"]["total_inscricoes"] == 1
    assert cursos["Direito"] == {"curso": "Direito", "total_participantes": 1, "total_inscricoes": 0}
