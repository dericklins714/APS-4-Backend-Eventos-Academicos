# API RESTful de Eventos Acadêmicos (APS 4)

API em Python/FastAPI para gerenciar eventos acadêmicos, participantes e inscrições, com dados persistidos em **SQLite + SQLAlchemy** (APS 3), relatórios consolidados e, nesta versão (APS 4), **autenticação com JWT, senhas com hash Argon2 e controle de acesso por perfis**.

## Funcionalidades

- CRUD de eventos e participantes; inscrições com controle de vagas e duplicidade;
- Relatórios: ocupação dos eventos, eventos por categoria e participação por curso;
- **Cadastro de usuários** com validação e e-mail único;
- **Senhas armazenadas somente como hash Argon2** (biblioteca `pwdlib`);
- **Login por e-mail e senha** com token **JWT** (PyJWT, HS256, com expiração);
- **Rotas protegidas** por dependências do FastAPI e **autorização por perfil** (`administrador` e `usuario`);
- Rota `GET /auth/me` com os dados do usuário autenticado.

## Estrutura do projeto

```text
api_eventos_fastapi/
├── main.py                  # App, rotas, criação das tabelas e do admin inicial
├── database.py              # Engine, sessões, Base e get_db
├── eventos.db               # Banco SQLite (gerado na 1ª execução)
├── .env.example             # Modelo das variáveis de ambiente (o .env real NÃO vai ao GitHub)
├── requirements.txt
├── README.md
│
├── controller/              # Rotas HTTP
│   ├── auth_controller.py       # /auth/login, /auth/me
│   ├── usuario_controller.py    # /usuarios
│   ├── evento_controller.py
│   ├── participante_controller.py
│   ├── inscricao_controller.py
│   └── relatorio_controller.py
│
├── model/                   # Entidades SQLAlchemy
│   ├── evento.py  participante.py  inscricao.py  usuario.py
│
├── schema/                  # Validação e respostas (Pydantic)
│   ├── evento_schema.py  participante_schema.py  inscricao_schema.py
│   ├── relatorio_schema.py  usuario_schema.py
│
├── service/                 # Regras de negócio e consultas
│   ├── evento_service.py  participante_service.py  inscricao_service.py
│   ├── relatorio_service.py  usuario_service.py  auth_service.py  utils.py
│
├── security/                # Segurança
│   ├── config.py            # Lê SECRET_KEY e demais configurações do ambiente
│   ├── security.py          # Hash de senha (Argon2) e criação/validação do JWT
│   └── dependencies.py      # get_usuario_atual e exige_perfil (autenticação/autorização)
│
└── tests/
    ├── conftest.py  test_api.py  test_auth.py
```

## Instalação

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Dependências de segurança

| Biblioteca | Uso |
|---|---|
| `pwdlib[argon2]` | Gerar e verificar hashes de senha com **Argon2** (`PasswordHash.recommended()`) |
| `PyJWT` | Criar, assinar e validar tokens JWT |
| `python-dotenv` | Ler as variáveis de ambiente do arquivo `.env` |
| `email-validator` | Validar o formato de e-mails (Pydantic `EmailStr`) |

## Configuração da chave secreta (obrigatória)

A chave que assina os tokens **não está no código**. Ela é lida da variável de ambiente `SECRET_KEY` (ou do arquivo `.env`). Sem ela, a aplicação **não inicia** e mostra uma mensagem explicando o que fazer.

1. Gere uma chave (mínimo 32 caracteres):

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Crie o arquivo `.env` a partir do modelo:

   ```bash
   # Windows
   copy .env.example .env
   # Linux/macOS
   cp .env.example .env
   ```

3. Abra o `.env` e preencha:

   ```env
   SECRET_KEY=cole_aqui_a_chave_gerada
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ADMIN_NOME=Administrador
   ADMIN_EMAIL=admin@exemplo.com
   ADMIN_SENHA=uma_senha_forte_aqui
   ```

O `.env` está no `.gitignore` e **nunca deve ser enviado ao GitHub**. Se a chave for trocada, todos os tokens já emitidos deixam de valer.

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SECRET_KEY` | Sim | Chave de assinatura dos tokens (≥ 32 caracteres) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Não (padrão 30) | Validade do token em minutos |
| `ADMIN_NOME`, `ADMIN_EMAIL`, `ADMIN_SENHA` | Não | Criam o administrador inicial |

## Execução

```bash
uvicorn main:app --reload
```

- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

O banco `eventos.db` fica na raiz do projeto e é criado automaticamente (a tabela `usuarios` é adicionada às existentes).

## Como cadastrar usuários e obter tokens

### Usuário comum

`POST /usuarios` (rota pública). O perfil é **sempre `usuario`**, definido pelo servidor; enviar o campo `perfil` (ou qualquer campo extra) resulta em `422`.

```json
{ "nome": "Aluno Exemplo", "email": "aluno@exemplo.com", "senha": "senha_segura" }
```

Resposta `201` (sem senha e sem hash):

```json
{ "id": 1, "nome": "Aluno Exemplo", "email": "aluno@exemplo.com", "perfil": "usuario" }
```

Regras: nome e e-mail obrigatórios, e-mail válido e único (sem diferenciar maiúsculas/minúsculas), senha com **no mínimo 8 caracteres** e que não seja só espaços.

### Administrador (estratégia de criação inicial)

Não existe rota pública para criar administradores. O administrador inicial é criado **na inicialização da aplicação** a partir das variáveis `ADMIN_EMAIL`, `ADMIN_SENHA` (e `ADMIN_NOME`) do `.env`. Se já existir um usuário com esse e-mail, nada é alterado. A senha também é armazenada como hash.

### Obter o token

`POST /auth/login`

```json
{ "email": "aluno@exemplo.com", "senha": "senha_segura" }
```

Resposta `200`:

```json
{ "access_token": "eyJhbGciOi...", "token_type": "bearer" }
```

Credenciais inválidas (e-mail inexistente **ou** senha errada) retornam a mesma resposta `401`: `{"detail": "E-mail ou senha inválidos."}`.

### Usar o token

Envie o cabeçalho `Authorization: Bearer <token>`. No Swagger: clique em **Authorize** (cadeado), cole **apenas o token** (sem a palavra "Bearer") e confirme.

O token (JWT assinado com HS256) contém `sub` (id do usuário), `iat` (emissão) e `exp` (expiração). A API verifica assinatura e expiração e depois carrega o usuário no banco; tokens inválidos, adulterados, expirados ou de usuários removidos retornam `401`.

## Rotas públicas e protegidas

| Método | Rota | Acesso |
|---|---|---|
| GET | `/` | Público |
| POST | `/usuarios` | Público |
| POST | `/auth/login` | Público |
| GET | `/auth/me` | Autenticado |
| GET | `/eventos`, `/eventos/{id}` | Autenticado (qualquer perfil) |
| POST | `/eventos` | **Administrador** |
| PUT | `/eventos/{id}` | **Administrador** |
| DELETE | `/eventos/{id}` | **Administrador** |
| GET | `/participantes`, `/participantes/{id}` | Autenticado (qualquer perfil) |
| POST | `/participantes` | Autenticado (qualquer perfil) |
| PUT | `/participantes/{id}` | **Administrador** |
| DELETE | `/participantes/{id}` | **Administrador** |
| POST | `/eventos/{evento_id}/inscricoes/{participante_id}` | Autenticado (qualquer perfil) |
| GET | `/eventos/{evento_id}/inscricoes` | **Administrador** |
| GET | `/relatorios/eventos/ocupacao` | **Administrador** |
| GET | `/relatorios/eventos/categorias` | **Administrador** |
| GET | `/relatorios/participantes/cursos` | **Administrador** |

## Perfis e permissões

| Operação | `administrador` | `usuario` |
|---|:--:|:--:|
| Cadastrar, atualizar e excluir eventos | ✅ | ❌ (403) |
| Consultar eventos | ✅ | ✅ |
| Consultar participantes | ✅ | ✅ |
| Cadastrar participante | ✅ | ✅ |
| Atualizar e excluir participantes | ✅ | ❌ (403) |
| Realizar inscrições | ✅ | ✅ |
| Consultar inscritos de um evento | ✅ | ❌ (403) |
| Consultar relatórios consolidados | ✅ | ❌ (403) |
| Consultar os próprios dados (`/auth/me`) | ✅ | ✅ |

Regras adicionais definidas pela equipe:

- O usuário comum pode cadastrar participantes porque precisa de um participante para realizar inscrições;
- A lista de inscritos e os relatórios ficam restritos ao administrador por exporem dados consolidados e pessoais;
- A autorização é verificada **no servidor** a cada requisição, a partir do usuário identificado pelo token; o perfil nunca é lido de dados enviados pelo cliente.

## Como a segurança está organizada

- `security/security.py`: `gerar_hash_senha`, `verificar_senha` (Argon2), `criar_token_acesso`, `decodificar_token`;
- `security/dependencies.py`: `get_usuario_atual` (autenticação) e `exige_perfil` / `requer_administrador` (autorização), aplicadas nas rotas com `Depends(...)`, sem repetir lógica em cada rota;
- `service/auth_service.py`: verifica as credenciais (sempre compara um hash, mesmo se o e-mail não existir, para não revelar quais e-mails estão cadastrados);
- Nenhuma resposta inclui `senha` ou `senha_hash` (os schemas de resposta não possuem esses campos).

## Erros

| Situação | Código | `detail` |
|---|---|---|
| Credenciais inválidas no login | 401 | "E-mail ou senha inválidos." |
| Token ausente, inválido ou expirado | 401 | "Não foi possível validar as credenciais." |
| Sem permissão para a operação | 403 | "Você não possui permissão para executar esta operação." |
| E-mail de usuário já cadastrado | 409 | "Já existe um usuário cadastrado com este e-mail." |
| Dados inválidos (e-mail, senha curta, campo extra etc.) | 422 | Detalhes do Pydantic |
| Evento/participante inexistente | 404 | "Evento não encontrado." / "Participante não encontrado." |
| Inscrição duplicada / sem vagas / e-mail de participante duplicado | 409 | Mensagens da APS 3 |

## Funcionalidades da APS 3 (preservadas)

Persistência em SQLite (`eventos.db` na raiz do projeto), relacionamentos Evento–Inscrição–Participante, inscrição única por participante/evento, exclusão em cascata das inscrições e os três relatórios:

- `GET /relatorios/eventos/ocupacao`: capacidade, inscritos, vagas e percentual de ocupação por evento;
- `GET /relatorios/eventos/categorias`: eventos, capacidade total e inscrições por categoria;
- `GET /relatorios/participantes/cursos`: participantes (sem repetição) e inscrições por curso.

Agora todas as rotas acima exigem autenticação conforme a tabela de acesso.

## Como reproduzir os testes

### Testes manuais no Swagger (`/docs`)

Prepare o `.env` (com `SECRET_KEY` e `ADMIN_*`) e inicie a API.

1. **Cadastrar usuário:** `POST /usuarios` com nome, e-mail e senha → `201`, sem senha/hash na resposta.
2. **Senha armazenada como hash:** com a API parada, execute na raiz do projeto
   `python -c "import sqlite3; print(sqlite3.connect('eventos.db').execute('select email, senha_hash from usuarios').fetchall())"`
   e confira que `senha_hash` começa com `$argon2`.
3. **E-mail duplicado:** repita o cadastro → `409`.
4. **Login válido:** `POST /auth/login` → `200` com `access_token`.
5. **Login inválido:** senha errada, e depois e-mail inexistente → `401` com a mesma mensagem.
6. **Sem token:** `GET /eventos` sem Authorize → `401`.
7. **Token válido:** clique em Authorize, cole o token e repita `GET /eventos` → `200`.
8. **Token inválido/expirado:** Authorize com um texto qualquer (ex.: `abc.def.ghi`) → `401`. Para expirado, defina `ACCESS_TOKEN_EXPIRE_MINUTES=1` no `.env`, reinicie, faça login, espere 1 minuto e use o token → `401`.
9. **Usuário comum em rota administrativa:** com o token do usuário comum, `POST /eventos` ou `GET /relatorios/eventos/ocupacao` → `403`.
10. **Administrador:** faça login com `ADMIN_EMAIL`/`ADMIN_SENHA`, use o token e execute `POST /eventos` → `201`.
11. **`GET /auth/me`:** retorna os dados do dono do token (sem senha/hash).
12. **Funcionalidades da APS 3:** como administrador, percorra inscrição, inscrição duplicada, sem vagas, exclusões e os três relatórios, conferindo que se atualizam com os dados.

### Testes automatizados

```bash
pytest -v
```

Usam banco SQLite em memória e uma chave de teste própria, sem alterar `eventos.db` nem depender do `.env`. Cobrem: cadastro e validações de usuário, tentativa de se auto-definir administrador, hash Argon2 no banco, e-mail duplicado, login válido/inválido, token ausente/inválido/adulterado/expirado/de usuário inexistente, `/auth/me`, permissões por perfil (403 vs. sucesso), rotas públicas e protegidas, além de todos os testes da APS 3 executados com um administrador autenticado.
