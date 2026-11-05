# TopHawks - Protocolo Genesis (parte 2)


Sistema completo de agente conversacional com LangChain 1.0, suporte a múltiplos modelos via OpenRouter, busca web com Tavily, e deploy em produção. Este repositório representa a evolução da Parte 1 (execução local via LangGraph Studio) para um sistema pronto para produção com API própria, autenticação, persistência em banco de dados e deploy na Railway e Vercel.

![Tela de Login](./img/login.png)

## Licença e Termos

O projeto é licenciado sob a **LICENÇA DA COMUNIDADE TOPHAWKS** (arquivo `LICENSE` na raiz).

### Resumo dos Termos

- Apenas membros verificados podem usar/alterar o código
- Membros podem criar soluções próprias (inclusive comerciais) com atribuição
- É proibido reempacotar como curso/material concorrente
- É proibido remover avisos de atribuição
- Violação implica rescisão imediata e possibilidade de indenização/tutela judicial
- Repositórios derivados devem permanecer privados ou com acesso restrito a membros

### Página de Termos

O frontend inclui página pública de termos em `/termos`, acessível mesmo sem autenticação.

## Sobre o Curso

Este projeto é a base prática da **Parte 2** do curso de sistemas de IA da comunidade TopHawks. A Parte 1 focou em execução local com LangGraph Studio; aqui expandimos para:

- API FastAPI customizada substituindo o LangGraph Studio
- Sistema de autenticação com passkey e JWT
- Persistência de conversas em PostgreSQL
- Streaming Server-Sent Events (SSE) real
- Deploy do backend na Railway
- Frontend Next.js 15 com React 19
- Deploy do frontend na Vercel

Após completar este curso, você terá:

- Sistema de IA completo em produção
- Conhecimento de deploy e infraestrutura
- Base para criar seus próprios agentes customizados
- Experiência com LangChain, LangGraph e FastAPI

## Visão Geral do Sistema

### Backend (`backend/`)
- Agente LangChain 1.0 usando `create_agent` com suporte a ferramentas
- API FastAPI e compatibilidade com LangGraph Studio para desenvolvimento isolado
- Middleware customizado para seleção dinâmica de modelo e Tavily
- Middleware de sumarização de threads
- Checkpointer PostgreSQL para persistência de threads
- Autenticação JWT com passkey compartilhada
- Streaming SSE para respostas em tempo real

### Frontend (`frontend/`)
- Next.js 15 com App Router e React 19
- Interface de chat com histórico de conversas
- Seleção dinâmica de modelos via `models.yaml`
- Sistema de autenticação integrado
- Suporte a streaming de respostas

### Recursos Principais

**Seleção de Modelos**

![Seleção de Modelos](./img/selecao_modelos.png)

Interface para escolher entre diversos modelos LLM via OpenRouter, com configuração de busca web Tavily.

**Gerenciamento de Threads**

![Seleção de Thread](./img/selecao_thread.png)

Criação e navegação entre múltiplas conversas persistentes.

**Autenticação**

![Tela de Login](./img/login.png)

Sistema de autenticação com passkey compartilhada e JWT.

**Interface de Chat**

![Chat em Ação](./img/chat.png)

Interface conversacional com suporte a markdown, code highlighting e streaming.

## Pré-requisitos

### Ferramentas Necessárias
- **Node.js** ≥ 18 (LTS recomendado)
- **npm** ≥ 9 (incluído com Node.js)
- **Python** ≥ 3.11
- **LangGraph CLI** 1.0+ (`pip install langgraph-cli`)
- **make** (macOS/Linux; Windows: Git Bash/MSYS2/WSL)

### Contas e Chaves de API
- Conta no [OpenRouter](https://openrouter.ai/) com créditos
- Chave API do [Tavily](https://tavily.com/) (opcional, para busca web)
- Conta no [LangSmith](https://langsmith.com/) (opcional, para observabilidade)
- Conta na [Railway](https://railway.app/) (para deploy do backend em produção)
- Conta na [Vercel](https://vercel.com/) (para deploy do frontend em produção)
- Domínio personalizado (opcional)

## O que precisamos para o desenvolvimento e deploy

1.  **Langsmith**: [https://smith.langchain.com/](https://smith.langchain.com/)
2.  **Railway**: [https://railway.com/](https://railway.com/) ou se quiser use meu código [https://railway.com?referralCode=WO6hQi](https://railway.com?referralCode=WO6hQi) (Não sou patrocinado. Apenas acredito que o produto é bom)
3.  **Vercel**: [https://vercel.com/](https://vercel.com/)
4.  **Namecheap** para domínios: [https://www.namecheap.com/](https://www.namecheap.com/)
5.  **Dbeaver**, cliente SQL: [https://dbeaver.io/](https://dbeaver.io/)
6.  **Docker Desktop** para nosso container: [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)

## Configuração Inicial

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd fastapp
```

### 2. Configurar Backend

#### Criar Ambiente Virtual Python

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configurar Variáveis de Ambiente

Crie `backend/.env` baseado no exemplo abaixo:

```bash
# Debug e logs
DEBUG_LOGS=true
DEBUG_AGENT_LOGS=true

# Banco de Dados
# Railway: usa RAILWAY_DATABASE_URL injetado automaticamente
DATABASE_URL=postgresql://user:password@host:5432/dbname

# CORS (desenvolvimento)
ALLOW_ORIGINS=*
ALLOW_CREDENTIALS=true

# Autenticação
ACCESS_KEY=tophawks
ACCESS_KEY_HASH=$2b$12$coloque-o-hash-gerado-pelo-bcrypt-aqui
AUTH_SECRET=altere-para-um-segredo-com-32-caracteres
AUTH_TOKEN_TTL_SECONDS=3600
# Para testes automatizados (mesmo valor da passkey real)
TEST_PASSKEY=tophawks

# Modelos (padrões)
DEFAULT_MODEL_NAME=google/gemini-2.5-flash
DEFAULT_USE_TAVILY=false

# Overrides para LangGraph Studio
STUDIO_MODEL_NAME=google/gemini-2.5-flash
STUDIO_USE_TAVILY=false

# APIs Externas
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
TAVILY_API_KEY=your-tavily-api-key

# Observabilidade (opcional)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=your-langsmith-project
```

**Gerar hash bcrypt para produção:**

```bash
python -m bcrypt "minha-senha-secreta"
# Copie o hash gerado para ACCESS_KEY_HASH
```

**Gerar chave secreta segura:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copie o resultado para AUTH_SECRET
```

### 3. Configurar Frontend

Copie o arquivo de exemplo e ajuste conforme necessário:

```bash
cd frontend
cp .env.local.example .env.local
```

Conteúdo do `frontend/.env.local`:

```bash
# langgraph dev
LANGGRAPH_API_BASE=http://127.0.0.1:8000

# Endpoint prod
#LANGGRAPH_API_BASE=https://fastapp-......
```

#### Instalar Dependências do Frontend

```bash
npm install
```

## Modos de Execução

### Modo 1: Desenvolvimento Local (LangGraph Studio)

Ideal para desenvolvimento e testes rápidos. O LangGraph Studio fornece interface visual e API local.

#### Iniciar Backend (Studio)

```bash
cd backend
source .venv/bin/activate
langgraph dev
# Studio disponível em http://127.0.0.1:2024
```

#### Iniciar Frontend

Em outro terminal:

```bash
cd frontend
npm run dev
# Aplicação disponível em http://localhost:3000
```

#### Usando Makefile

```bash
make help                # Lista todos os alvos
make studio              # Backend LangGraph Studio (backend/)
make frontend            # Next.js dev server (frontend/)
make api                 # FastAPI com .env carregado (backend/)
make test-api            # Testes de integração do backend
make test-api-curl       # Requisição real via curl (precisa make api ativo)
make docker-build-run    # Build e sobe backend em Docker com backend/.env
```

> Windows: use Git Bash ou WSL para rodar `make`. Sem make, execute os comandos equivalentes manualmente (ex.: `cd backend && langgraph dev`).

### Modo 2: API Local (FastAPI) - OPCIONAL

Para testar o comportamento de produção localmente, incluindo autenticação e persistência.

#### Configurar Banco de Dados Local

```bash
# Opção 1: PostgreSQL via Docker
docker run --name postgres-fastapp \
  -e POSTGRES_PASSWORD=senha \
  -e POSTGRES_DB=fastapp \
  -p 5432:5432 \
  -d postgres:15

# Opção 2: PostgreSQL instalado localmente
# Configure DATABASE_URL no .env
```

#### Iniciar API FastAPI

```bash
cd backend
source .venv/bin/activate
uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

# Ou usando Makefile
make api
```

#### Ajustar Frontend para API Local

Edite `frontend/.env.local`:

```bash
LANGGRAPH_API_BASE=http://localhost:8000
```

Reinicie o frontend:

```bash
cd frontend
npm run dev
```

## Sistema de Autenticação

O sistema utiliza passkey compartilhada com hash bcrypt e tokens JWT de curta duração.

### Variáveis de Autenticação

- **`ACCESS_KEY`**: Passkey em texto plano (apenas desenvolvimento)
- **`ACCESS_KEY_HASH`**: Hash bcrypt da passkey (produção)
- **`AUTH_SECRET`**: Chave secreta para assinar JWTs (mínimo 32 caracteres)
- **`AUTH_TOKEN_TTL_SECONDS`**: Tempo de vida do token em segundos (padrão: 3600)
- **`TEST_PASSKEY`**: Passkey para testes automatizados

### Fluxo de Autenticação

1. Cliente envia `POST /auth/login` com `{"passkey": "..."}`
2. Backend valida contra `ACCESS_KEY_HASH` (ou `ACCESS_KEY` em dev)
3. Retorna `{"token": "...", "expires_at": "..."}`
4. Cliente inclui `Authorization: Bearer <token>` em todas as requisições
5. Frontend armazena token em `localStorage` e gerencia expiração

### Testar Autenticação Manualmente

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"passkey":"minha-senha-local"}'

# Usar token retornado
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/threads/search
```

### Configuração recomendada para Produção após o curso

1. Gere hash bcrypt forte:
   ```bash
   python -m bcrypt "senha-super-secreta-complexa"
   ```

2. Configure apenas `ACCESS_KEY_HASH` (remova `ACCESS_KEY`)

3. Use `AUTH_SECRET` aleatório e seguro:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. Distribua a passkey apenas para operadores autorizados

## Deploy na Railway

Este guia cobre o deploy completo do backend FastAPI na Railway com PostgreSQL.

### 1. Preparação

- Certifique-se de que o repositório está no GitHub
- Verifique se `backend/Dockerfile` está presente
- Confirme que `backend/requirements.txt` está atualizado

### 2. Criar Projeto na Railway

1. Acesse [railway.app](https://railway.app) e faça login
2. Clique em **"New Project"** → **"Deploy from GitHub repo"**
3. Conecte sua conta GitHub e selecione o repositório
4. Railway detectará automaticamente o `backend/Dockerfile`

### 3. Adicionar Banco de Dados PostgreSQL

1. No projeto Railway, clique em **"New Service"** → **"Add Database"**
2. Selecione **"Postgres"**
3. Railway criará o banco e fornecerá a `DATABASE_URL`
4. A URL interna será algo como: `postgresql://postgres:***@postgres.railway.internal:5432/railway`

### 4. Configurar Variáveis de Ambiente

No painel do serviço backend, vá em **"Variables"** e adicione:

**Obrigatórias:**
```bash
DATABASE_URL=postgresql://postgres:SENHA@postgres.railway.internal:5432/railway
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
ACCESS_KEY_HASH=$2b$12$...
AUTH_SECRET=chave-secreta-gerada-aleatoriamente
```

**Opcionais:**
```bash
TAVILY_API_KEY=tvly-...
DEBUG_AGENT_LOGS=false
DEBUG_LOGS=false
DEFAULT_MODEL_NAME=google/gemini-2.5-flash
DEFAULT_USE_TAVILY=false
AUTH_TOKEN_TTL_SECONDS=3600
PORT=8000
```

### 5. Deploy e Verificação

1. Após configurar as variáveis, o deploy iniciará automaticamente
2. Aguarde o build e deployment completarem (5-10 minutos)
3. A URL pública será gerada (ex: `https://fastapp-production.up.railway.app`)
4. Teste o endpoint de saúde:
   ```bash
   curl https://seu-app.railway.app/health
   ```

### 6. Configurar Frontend para Produção

#### Opção A: Deploy do Frontend na Vercel

1. Faça push do código para GitHub
2. Importe o projeto na [Vercel](https://vercel.com)
3. Configure a variável de ambiente:
   ```bash
   LANGGRAPH_API_BASE=https://seu-app.railway.app
   ```
4. Deploy automático será realizado

#### Opção B: Frontend Local Apontando para Produção

Edite `frontend/.env.local`:
```bash
LANGGRAPH_API_BASE=https://seu-app.railway.app
```

### 7. Endpoints Disponíveis

- `GET /health` - Health check do serviço
- `POST /auth/login` - Autenticação com passkey
- `POST /threads` - Criar nova thread de conversa
- `GET /threads/{thread_id}` - Buscar thread específica
- `POST /threads/search` - Listar threads com paginação
- `POST /threads/{thread_id}/runs/wait` - Execução síncrona
- `POST /threads/{thread_id}/runs/stream` - Streaming SSE

### 8. Troubleshooting Comum

**Erro 502 Bad Gateway**
- Verifique se a variável `PORT` está definida como `8000`
- Confirme que o Dockerfile expõe a porta correta

**Database connection failed**
- Verifique se `DATABASE_URL` está correta
- Confirme que o serviço PostgreSQL está rodando
- Use a URL interna (`postgres.railway.internal`) para comunicação entre serviços

**Build fails**
- Verifique logs de build no painel Railway
- Confirme que todas as dependências em `requirements.txt` são válidas
- Verifique se o Python version no Dockerfile é compatível

**Application not responding**
- Verifique os logs em tempo real no painel Railway
- Confirme que todas as variáveis de ambiente obrigatórias estão configuradas
- Teste endpoints localmente antes do deploy

**Ruído nos logs do Postgres**
- Mensagens como `invalid length of startup packet` são normais (scans/bots)
- Se o acesso público não for necessário, desative **Public Networking** do banco
- Use apenas `DATABASE_URL` interno para comunicação entre serviços

### 9. Monitoramento e Observabilidade

**Logs em Tempo Real**
- Acesse o painel do serviço na Railway
- Clique em **"Logs"** para ver output em tempo real
- Use filtros para buscar erros específicos

**Métricas de Performance**
- Railway fornece métricas de CPU, memória e rede
- Configure alertas para uso excessivo de recursos

**Logs do Agente**
- Habilite `DEBUG_AGENT_LOGS=true` para logs detalhados
- Use `DEBUG_LOGS=true` para logs gerais do backend
- Ative `LANGSMITH_TRACING=true` e defina `LANGSMITH_API_KEY`/`LANGSMITH_PROJECT` para enviar traces e logs do agente ao LangSmith (útil para depurar execuções, ferramentas e tokens)

## Estrutura do Projeto

```
fastapp/
├── backend/
│   ├── agente/
│   │   ├── __init__.py
│   │   ├── agente.py           # Definição do agente LangChain
│   │   ├── middleware.py       # Middleware para modelo/Tavily dinâmicos
│   │   └── tools.py            # Ferramentas customizadas
│   ├── server/
│   │   ├── __init__.py
│   │   ├── auth.py             # Sistema de autenticação JWT
│   │   ├── db.py               # Conexão e setup do PostgreSQL
│   │   ├── graph_app.py        # Integração LangGraph (app do agente)
│   │   ├── main.py             # FastAPI app principal
│   │   ├── models.py           # Modelos Pydantic
│   │   └── utils.py            # Utilidades do servidor
│   ├── tests/
│   │   └── test_server_integration.py
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile
│   ├── langgraph.json          # Configuração LangGraph Studio
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── hawk_azul192.png
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── globals.css
│   │   │   ├── history/
│   │   │   ├── icon.png
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx        # Página principal (chat)
│   │   │   ├── robots.ts
│   │   │   ├── sitemap.ts
│   │   │   └── termos/
│   │   ├── components/
│   │   │   ├── app/
│   │   │   │   ├── ChatPane.tsx
│   │   │   │   ├── HistoryList.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   └── TopBar.tsx
│   │   │   ├── layout/
│   │   │   │   └── AppChrome.tsx
│   │   │   └── ui/
│   │   │       ├── alert.tsx
│   │   │       ├── badge.tsx
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       └── switch.tsx
│   │   ├── lib/
│   │   │   └── config.ts
│   │   ├── mock/
│   │   │   ├── conversations.ts
│   │   │   └── models.ts
│   │   └── state/
│   │       ├── useAuth.tsx     # Context de autenticação
│   │       └── useGenesisUI.tsx # Context do agente
│   ├── .env.local.example
│   ├── models.yaml             # Catálogo de modelos
│   ├── next.config.mjs
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.mjs
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── img/
│   ├── chat.png
│   ├── login.png
│   ├── selecao_modelos.png
│   └── selecao_thread.png
├── .gitignore
├── LICENSE
├── Makefile
├── README.md
└── sistema_local.png
```

## Arquitetura do Agente

### Middleware Customizado

O middleware (`backend/agente/middleware.py`) intercepta requisições e:

1. Extrai configurações de modelo e Tavily do SystemMessage
2. Valida e sanitiza os parâmetros
3. Aplica configurações via `config.configurable`
4. Adiciona guardrails quando Tavily está desabilitado

### Checkpointer PostgreSQL

O `AsyncPostgresSaver` cria automaticamente quatro tabelas:

- **`checkpoint_migrations`**: Versão do schema do LangGraph
- **`checkpoints`**: Snapshots do estado por thread
- **`checkpoint_blobs`**: Blobs versionados por canal (mensagens, tasks)
- **`checkpoint_writes`**: Registros de writes/pending sends

Adicionalmente, criamos a tabela `threads` para listagem rápida de conversas.

### Streaming SSE

O endpoint `POST /threads/{thread_id}/runs/stream` envia eventos `text/event-stream`:

- **`chunk`**: Tokens individuais da resposta
- **`final`**: Mensagem completa ao final
- **`done`**: Sinaliza fim do stream

## Testes

### Testes Automatizados

```bash
# Testes do backend
cd backend
source .venv/bin/activate
make test-api

# Ou diretamente com pytest
pytest tests/test_server_integration.py -v
```

### Testes Manuais com cURL

```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"passkey":"minha-senha-local"}'

# Criar thread
curl -X POST http://localhost:8000/threads \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json"

# Enviar mensagem
curl -X POST http://localhost:8000/threads/<thread_id>/runs/wait \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "input": [{"role": "user", "content": "Olá!"}],
    "config": {
      "configurable": {
        "model_name": "google/gemini-2.5-flash",
        "use_tavily": false
      }
    }
  }'
```

## Consultas SQL Úteis

### Visualizar mensagens de uma thread

```sql
SELECT c.thread_id,
       c.checkpoint->'channel_values'->'messages' AS messages_json,
       c.metadata
  FROM checkpoints c
 WHERE c.thread_id = 'THREAD-ID-AQUI'
ORDER BY c.checkpoint_id DESC
 LIMIT 1;
```

### Quantidade de execuções por thread

```sql
SELECT thread_id, COUNT(*) AS total_runs
  FROM checkpoints
GROUP BY thread_id
ORDER BY total_runs DESC;
```

### Threads criadas recentemente

```sql
SELECT thread_id, created_at 
  FROM threads 
ORDER BY created_at DESC 
 LIMIT 20;
```

## Limitações Conhecidas

### Gemini + Tavily

Modelos como o Gemini 3 Pro Preview exigem que cada chamada de ferramenta tenha `thought_signature` (ver [documentação OpenRouter](https://openrouter.ai/docs/use-cases/reasoning-tokens)). Como ainda não preservamos esses "reasoning tokens", execuções com Tavily habilitado nesse modelo falham com `INVALID_ARGUMENT`.

**Solução temporária**: Use Tavily apenas em modelos que não exigem esse campo (Claude, Grok, etc.) ou desabilite a busca ao usar Gemini.

## Comandos Úteis

### Backend

```bash
make studio          # Inicia LangGraph Studio
make api             # Inicia FastAPI local
make test-api        # Executa testes automatizados
```

### Frontend

```bash
npm run dev          # Servidor de desenvolvimento
npm run build        # Build de produção
npm run start        # Servidor de produção
npm run lint         # Validação ESLint
```

### Desenvolvimento Combinado

```bash
# Terminal 1: Backend
make studio

# Terminal 2: Frontend
make frontend
```

### Testes

```bash
# Testes automatizados
make test-api

# Teste manual com cURL (requer make api rodando)
make test-api-curl
```

### Docker

```bash
# Build e execução local
make docker-build-run
```

## Observabilidade (Opcional)

Para rastreamento e debugging avançado do agente, configure o LangSmith:

### Configuração do LangSmith

1. Crie uma conta no [LangSmith](https://langsmith.com/)
2. Obtenha sua API Key no painel
3. Configure no `backend/.env`:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-langsmith-api-key
LANGSMITH_PROJECT=genesis-agent
```

### Benefícios

- **Tracing completo**: Visualize cada chamada do agente em tempo real
- **Debugging avançado**: Identifique gargalos e erros específicos
- **Métricas de performance**: Monitore latência e uso de tokens
- **Histórico de conversas**: Acompanhe interações do usuário

### Custo

O LangSmith oferece tier gratuito com limitações. Para uso em produção, considere os planos pagos.

### Notas de Release

### 2025-12-07 - Atualização de Segurança Crítica

**CVE-2025-66478** - Vulnerabilidade crítica no protocolo React Server Components

- **Impacto**: Possível Remote Code Execution (RCE) em ambientes não atualizados
- **Versão afetada**: Next.js 15.5.5 e anteriores
- **Versão corrigida**: Next.js 15.5.7
- **Ação requerida**: Atualização imediata obrigatória

[Detalhes completos da vulnerabilidade](https://nextjs.org/blog/CVE-2025-66478)

## Sugestões de Expansão

- Adicionar mais ferramentas customizadas ao agente
- Implementar sistema de usuários múltiplos
- Customizar layout
- Integrar com outros provedores de LLM
- Criar interface de administração
- Implementar rate limiting e quotas
- Adicionar testes end-to-end com Playwright

## Suporte

Para dúvidas e suporte:

- Comunidade TopHawks: [rhawk.pro/comunidade](https://www.rhawk.pro/comunidade)
- Issues no repositório (apenas para membros)
- Canal exclusivo no Discord da comunidade

---

**Desenvolvido por Ronnald Hawk para a Comunidade TopHawks**
