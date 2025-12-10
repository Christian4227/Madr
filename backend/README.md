# Sistema de Gerenciamento de Romancistas — Backend

Este backend gerencia **romancistas**, **livros**, **usuários** e **autenticação JWT**.  
A equipe de frontend pode usar essa API para desenvolver dashboards, sites e apps logados.

Toda a execução é baseada no **uv** — ambiente gerenciado, rápido e reprodutível.

---

## 🚀 Como rodar o projeto

### 1. Instale o uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Crie o ambiente
```bash
uv venv
```

### 3. Ative o ambiente
```bash
source .venv/bin/activate
```

### 4. Instale as dependências
```bash
uv pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz:

```
SECRET_KEY=sua_chave_segura
ALGORITHM=HS256
DATABASE_URL=postgresql+psycopg://user:senha@localhost:5432/romancistas
```

### 6. Execute as migrações (se houver)
```bash
uv run alembic upgrade head
```

### 7. Rode a API
```bash
uv run task run
```

A API ficará disponível em:  
👉 http://localhost:8000

Documentação automática:  
👉 http://localhost:8000/docs  
👉 http://localhost:8000/redoc

---

## 🧪 Rodando testes

```bash
uv run task test
```

Com relatório de cobertura:

```bash
uv run task test --cov=madr  
```

---

## 📦 Estrutura do projeto (simplificada)

```
.
├── README.md
├── alembic.ini
├── compose.yml
├── database.db
├── madr
│   ├── __init__.py
│   ├── api
│   ├── app.py
│   ├── config.py
│   ├── core
│   ├── dependecies.py
│   ├── main.py
│   ├── models
│   └── schemas
├── migrations
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
├── pyproject.toml
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── database
│   ├── test_app.py
│   └── test_user.py
└── uv.lock
```

---

## 🔐 Autenticação

A autenticação segue o padrão OAuth2 com JWT.

Fluxo básico:

1. Enviar `username` e `password` para `/token`
2. Receber `access_token`
3. Enviar o token no header:

```
Authorization: Bearer <token>
```

---

## 👥 Perfis gerenciados

- **Usuários**
- **Romancistas**
- **Livros**

Cada rota segue arquitetura REST.

---

## 🤝 Para o time de frontend

- Todas as respostas seguem padrão JSON
- Tokens expiram em tempo configurado no backend
- CORS já configurado (se necessário, ajustar no arquivo principal)
- Paginação padrão (caso implementada) estará nos endpoints `/novelists` e `/books`

---

## 📄 Licença

Projeto interno — uso restrito às equipes da empresa.

# Sistema de Gerenciamento de Romancistas — Backend (FastAPI)

Este backend gerencia **romancistas**, **livros**, **usuários** e **autenticação JWT**.

Toda a execução é baseada no **uv** — ambiente gerenciado, rápido e reprodutível.

---

## 🚀 Como rodar o projeto

### 1. Instale o uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Crie o ambiente
```bash
uv venv
```

### 3. Ative o ambiente
```bash
source .venv/bin/activate
```

### 4. Instale as dependências
```bash
uv pip install -r requirements.txt
```

### 5. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz:

```
SECRET_KEY=sua_chave_segura
ALGORITHM=HS256
DATABASE_URL=postgresql+psycopg://user:senha@localhost:5432/romancistas
```

### 6. Execute as migrações (se houver)
```bash
uv run alembic upgrade head
```

### 7. Rode a API
```bash
uv run fastapi dev madr/main.py
```

A API ficará disponível em:  
👉 http://localhost:8000

Documentação automática:  
👉 http://localhost:8000/docs  
👉 http://localhost:8000/redoc

---

## 🧪 Rodando testes

```bash
uv run task test
```

Com relatório de cobertura:

```bash
uv run task test --cov=madr
```

---

## 📦 Estrutura do projeto (simplificada)

```
.
├── README.md
├── alembic.ini
├── compose.yml
├── database.db
├── madr
│   ├── __init__.py
│   ├── api
│   ├── app.py
│   ├── config.py
│   ├── core
│   ├── dependecies.py
│   ├── main.py
│   ├── models
│   └── schemas
├── migrations
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   └── versions
├── pyproject.toml
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── database
│   ├── test_app.py
│   └── test_user.py
└── uv.lock
```

---

## 🔐 Autenticação

A autenticação segue o padrão OAuth2 com JWT.

Fluxo básico:

1. Enviar `username` e `password` para `/token`
2. Receber `access_token`
3. Enviar o token no header:

```
Authorization: Bearer <token>
```

---

## 👥 Perfis gerenciados

- **Usuários**
- **Romancistas**
- **Livros**

Cada rota segue arquitetura REST.

---

## 🤝 Para o time de frontend

- Todas as respostas seguem padrão JSON
- Tokens expiram em tempo configurado no backend
- CORS já configurado (se necessário, ajustar no arquivo principal)
- Paginação padrão (caso implementada) estará nos endpoints `/romancistas` e `/livros`

---

## 📄 Licença

Projeto interno — uso restrito às equipes da empresa.

