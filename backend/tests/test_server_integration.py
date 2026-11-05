import json
import uuid
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient
import pytest

# Garante que variáveis do backend/.env estejam carregadas
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

from server.main import app  # noqa: E402  (carrega após .env)


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def auth_headers(client: TestClient) -> dict[str, str]:
    passkey = os.getenv("ACCESS_KEY") or os.getenv("TEST_PASSKEY")
    if not passkey:
        raise RuntimeError("Defina ACCESS_KEY (texto puro) ou TEST_PASSKEY para executar os testes de autenticação.")
    resp = client.post("/auth/login", json={"passkey": passkey})
    assert resp.status_code == 200, f"Falha no login: {resp.text}"
    token = resp.json().get("token")
    assert token, "Resposta de login não retornou token"
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_run_wait_real_flow(client: TestClient, auth_headers: dict[str, str]):
    # Cria thread real no Postgres/checkpointer
    thread_resp = client.post("/threads", headers=auth_headers)
    assert thread_resp.status_code == 200
    thread_id = thread_resp.json()["thread_id"]

    payload = {
        "input": {
            "messages": [
                {"role": "system", "content": "Seja sucinto."},
                {"role": "user", "content": "Diga oi e mencione os TopHawks."},
            ]
        },
        "config": {"configurable": {"test_run_id": str(uuid.uuid4())}},
    }

    resp = client.post(f"/threads/{thread_id}/runs/wait", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    messages = data["result"]["messages"]

    assert messages, "Esperava mensagens retornadas pelo agente real"
    assert any(m.get("type") == "human" for m in messages)

    ai_msgs = [m for m in messages if m.get("type") == "ai"]
    assert ai_msgs, "Esperava pelo menos uma mensagem do agente"
    assert ai_msgs[-1].get("content"), "Conteúdo da resposta do agente não pode ser vazio"


def test_run_stream_sse_response(client: TestClient, auth_headers: dict[str, str]):
    # Reutiliza fluxo completo para validar SSE (/runs/stream)
    thread_resp = client.post("/threads", headers=auth_headers)
    assert thread_resp.status_code == 200
    thread_id = thread_resp.json()["thread_id"]

    payload = {
        "input": {
            "messages": [
                {"role": "system", "content": "Seja sucinto."},
                {"role": "user", "content": "Diga oi em português."},
            ]
        }
    }

    resp = client.post(f"/threads/{thread_id}/runs/stream", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    body = resp.text.strip()
    events = [line.strip()[6:] for line in body.split("\n\n") if line.startswith("data: ")]
    assert events, "Fluxo SSE deveria retornar ao menos um evento"

    final_event = None
    done_event = False
    for raw in events:
        data = json.loads(raw)
        if data.get("event") == "final":
            final_event = data
        if data.get("event") == "done":
            done_event = True

    assert done_event, "Esperava evento 'done' encerrando a stream"
    assert final_event is not None, "Esperava evento 'final' com mensagens"
    assert final_event["thread_id"] == thread_id
    messages = final_event["messages"]
    assert messages, "Evento final deve carregar mensagens do histórico"
