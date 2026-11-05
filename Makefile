SHELL := /bin/zsh

ENV_FILE ?= backend/.env

.PHONY: help studio frontend api test-api test-api-curl docker-build-run

help:
	@echo "Uso: make <alvo>"
	@echo "Alvos disponíveis:"
	@echo "  studio    Inicia o LangGraph Studio em ./backend"
	@echo "  frontend  Inicia o servidor Next.js em ./frontend"
	@echo "  api       Inicia o backend FastAPI (server) em ./backend"
	@echo "  test-api  Roda os testes de integração do backend em ./backend"
	@echo "  test-api-curl  Dispara um POST real via curl (requer make api rodando)"
	@echo "  docker-build-run  Builda e roda a imagem do backend localmente (usa backend/.env)"

studio:
	@echo "[backend] Iniciando backend LangGraph Studio..."
	@cd backend && langgraph dev

frontend:
	@echo "[frontend] Starting Next.js dev server..."
	@cd frontend && npm run dev

api:
	@echo "[backend] Starting FastAPI server..."
	@cd backend && . .venv/bin/activate && if [ -f .env ]; then set -a; source .env; set +a; fi; uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

test-api:
	@echo "[backend] Running FastAPI integration tests..."
	@cd backend && . .venv/bin/activate && if [ -f .env ]; then set -a; source .env; set +a; fi; PYTHONPATH=. pytest tests/test_server_integration.py

test-api-curl:
	@echo "[curl] Certifique-se de que 'make api' está executando antes deste teste."
	@if [ -f $(ENV_FILE) ]; then set -a; source $(ENV_FILE); set +a; fi; \
	PASSKEY=$${TEST_PASSKEY:-$${ACCESS_KEY:-}}; \
	if [ -z "$$PASSKEY" ]; then echo "Defina TEST_PASSKEY ou ACCESS_KEY no backend/.env para usar make test-api-curl." && exit 1; fi; \
	PYTHON=$$(command -v python || command -v python3); \
	if [ -z "$$PYTHON" ]; then echo "Python não encontrado (python ou python3). Instale para rodar test-api-curl." && exit 1; fi; \
	TOKEN=$$(curl -s -X POST "http://0.0.0.0:8000/auth/login" \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d "{\"passkey\":\"$$PASSKEY\"}" \
		| $$PYTHON -c 'import json,sys; data=json.load(sys.stdin); print(data.get("token",""))'); \
	if [ -z "$$TOKEN" ]; then echo "Falha ao obter token. Verifique passkey." && exit 1; fi; \
	curl -s -X POST "http://0.0.0.0:8000/threads/demo-curl/runs/wait" \
		-H "accept: application/json" \
		-H "Authorization: Bearer $$TOKEN" \
		-H "Content-Type: application/json" \
		-d '{"assistant_id":"curl-demo","input":{"messages":[{"role":"user","content":"Dê um oi rápido aos TopHawks."}]}}' \
	| $$PYTHON -m json.tool

docker-build-run:
	@echo "[docker] Buildando imagem local do backend..."
	@docker build -t tophawks -f backend/Dockerfile backend
	@echo "[docker] Subindo container com env de backend/.env (Ctrl+C para parar)..."
	@docker rm -f Protocolo-Genesis >/dev/null 2>&1 || true
	@docker run --rm --name Protocolo-Genesis --env-file backend/.env -p 8000:8000 tophawks
