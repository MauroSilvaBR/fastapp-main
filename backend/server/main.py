
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from contextlib import asynccontextmanager

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)

from .db import (
    close_pool,
    ensure_threads_table,
    get_thread_created_at,
    init_pool,
    insert_thread,
    list_threads,
)
from .auth import login_with_passkey, require_token
from .graph_app import build_agent_graph, open_checkpointer
from .models import (
    LoginRequest,
    LoginResponse,
    RunRequest,
    RunResponse,
    RunResult,
    ThreadObj,
    ThreadSearchRequest,
)
from .utils import lc_messages_to_list


from dotenv import load_dotenv


# Carrega variáveis de ambiente de backend/.env quando rodando local
load_dotenv()


# CORS (configurado via ALLOW_ORIGINS e ALLOW_CREDENTIALS do .env)
allow_origins_str = os.getenv("ALLOW_ORIGINS", "*")
if allow_origins_str == "*":
    allow_origins: List[str] = ["*"]
else:
    allow_origins = [origin.strip() for origin in allow_origins_str.split(",") if origin.strip()]

allow_credentials = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

compiled_graph = None
active_checkpointer = None
checkpointer_stack = None
legal_headers = {
    "X-TopHaws-License": "LICENCA-COMUNIDADE-TOPHAWKS",
    "X-TopHaws-Author": "Ronnald Hawk",
    "X-TopHaws-Site": "https://www.rhawk.pro/",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Abre recursos críticos no startup e fecha no shutdown."""
    global compiled_graph, active_checkpointer, checkpointer_stack
    await init_pool()
    await ensure_threads_table()
    checkpointer_stack, active_checkpointer = await open_checkpointer()
    await active_checkpointer.setup()
    compiled_graph = build_agent_graph(active_checkpointer)
    try:
        yield
    finally:
        await close_pool()
        if checkpointer_stack is not None:
            await checkpointer_stack.aclose()
            checkpointer_stack = None
            active_checkpointer = None


app = FastAPI(title="TOP HAWKS API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_attribution_headers(request, call_next):
    """Adiciona cabeçalhos de atribuição/licença para sinalização discreta."""
    response = await call_next(request)
    for key, value in legal_headers.items():
        if key not in response.headers:
            response.headers[key] = value
    return response


@app.get("/health")
async def health() -> Dict[str, str]:
    """Retorna status simples para monitoramento."""
    return {"status": "ok"}


@app.post("/auth/login", response_model=LoginResponse)
async def auth_login(body: LoginRequest) -> LoginResponse:
    """Endpoint de login: valida passkey e retorna token com expiração."""
    token, expires_at = login_with_passkey(body.passkey)
    return LoginResponse(token=token, expires_at=expires_at.isoformat())


def convert_to_lc_messages(raw: List[Dict[str, Any]]) -> List[BaseMessage]:
    """Traduz objetos vindos do frontend para mensagens do LangChain."""
    msgs: List[BaseMessage] = []
    for message in raw:
        role = message.get("role")
        content = message.get("content")
        if not isinstance(content, str):
            content = str(content)
        if role == "user":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant":
            msgs.append(AIMessage(content=content))
        elif role == "system":
            msgs.append(SystemMessage(content=content))
    return msgs


def build_run_config(thread_id: str, body: RunRequest) -> Dict[str, Any]:
    """Monta config enviando thread_id e overrides opcionais."""
    configurable: Dict[str, Any] = {"thread_id": thread_id}
    if body.config and isinstance(body.config.configurable, dict):
        configurable.update(body.config.configurable)
    return {"configurable": configurable}


def chunk_to_text(chunk: Any) -> str:
    """Extrai string utilizável a partir de pedaços do modelo."""
    if isinstance(chunk, AIMessageChunk):
        content = chunk.content
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text", "")))
                else:
                    parts.append(str(item))
            return "".join(parts)
        if isinstance(content, str):
            return content
    if hasattr(chunk, "content"):
        value = getattr(chunk, "content")
        if isinstance(value, str):
            return value
    return str(chunk)


def sse_payload(data: Dict[str, Any]) -> str:
    """Formato básico text/event-stream."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/threads")
async def create_thread(token_claims: Dict[str, Any] = Depends(require_token)) -> ThreadObj:
    """Cria um identificador novo para conversas no banco."""
    thread_id = str(uuid.uuid4())
    await insert_thread(thread_id)
    created = await get_thread_created_at(thread_id)
    return ThreadObj(thread_id=thread_id, created_at=created, values={"messages": []})


@app.post("/threads/search")
async def search_threads(
    req: ThreadSearchRequest,
    token_claims: Dict[str, Any] = Depends(require_token),
) -> List[ThreadObj]:
    """Lista threads recentes para permitir seleção no frontend."""
    rows = await list_threads(limit=req.limit or 50)
    return [ThreadObj(thread_id=t, created_at=ts, values={"messages": []}) for t, ts in rows]


@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str, token_claims: Dict[str, Any] = Depends(require_token)) -> ThreadObj:
    """Retorna histórico salvo para um thread específico."""
    if active_checkpointer is None:
        raise HTTPException(status_code=500, detail="Checkpointer not initialized")
    created = await get_thread_created_at(thread_id)
    cfg = {"configurable": {"thread_id": thread_id}}
    try:
        tup = await active_checkpointer.aget_tuple(cfg)
        msgs: List[BaseMessage] = []
        if tup and tup.checkpoint:
            msgs = tup.checkpoint.get("channel_values", {}).get("messages", []) or []
    except Exception as e:
        # Em caso de erro, mantém mensagens vazias
        msgs = []
    return ThreadObj(
        thread_id=thread_id,
        created_at=created,
        values={"messages": lc_messages_to_list(msgs)},
    )


@app.post("/threads/{thread_id}/runs/wait", response_model=RunResponse)
async def run_and_wait(
    thread_id: str,
    body: RunRequest,
    token_claims: Dict[str, Any] = Depends(require_token),
) -> RunResponse:
    """Fluxo síncrono: aguarda o LangGraph concluir (ainvoke) e só então responde."""
    if compiled_graph is None:
        raise HTTPException(status_code=500, detail="Graph not initialized")
    if active_checkpointer is None:
        raise HTTPException(status_code=500, detail="Checkpointer not initialized")

    # Converte mensagens de entrada (system+user) para canal de mensagens
    in_msgs = convert_to_lc_messages([m.model_dump() for m in body.input.messages])

    # Prepara config, preservando valores enviados pelo frontend
    cfg = build_run_config(thread_id, body)

    # Invoca o grafo completo; ainvoke bloqueia até o checkpointer salvar o resultado
    await compiled_graph.ainvoke({"messages": in_msgs}, config=cfg)

    # Busca estado atualizado no checkpointer
    tup = await active_checkpointer.aget_tuple({"configurable": {"thread_id": thread_id}})
    msgs: List[BaseMessage] = []
    if tup and tup.checkpoint:
        msgs = tup.checkpoint.get("channel_values", {}).get("messages", []) or []

    return RunResponse(result=RunResult(messages=lc_messages_to_list(msgs)))


@app.post("/threads/{thread_id}/runs/stream")
async def run_and_stream(
    thread_id: str,
    body: RunRequest,
    token_claims: Dict[str, Any] = Depends(require_token),
):
    """Fluxo assíncrono: envia SSE (Server-Sent Events) com tokens parciais e resumo final."""
    if compiled_graph is None:
        raise HTTPException(status_code=500, detail="Graph not initialized")
    if active_checkpointer is None:
        raise HTTPException(status_code=500, detail="Checkpointer not initialized")

    # Entrada representa apenas mensagens novas; histórico vem do checkpointer
    in_msgs = convert_to_lc_messages([m.model_dump() for m in body.input.messages])
    cfg = build_run_config(thread_id, body)

    async def event_iterator():
        """Traduz eventos do LangGraph em mensagens SSE (chunk/final/done)."""
        try:
            # Primeiro: faz streaming dos chunks para o frontend
            async for event in compiled_graph.astream_events(
                {"messages": in_msgs},
                config=cfg,
            ):
                event_name = event.get("event")
                if event_name == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    text = chunk_to_text(chunk) if chunk is not None else ""
                    if not text:
                        continue
                    # Cada pedaço do modelo vira um evento chunk no SSE
                    yield sse_payload({"event": "chunk", "thread_id": thread_id, "text": text})
            
            # IMPORTANTE: O loop acima só termina quando astream_events() completar TOTALMENTE,
            # incluindo a persistência no checkpointer. Não damos break antecipado.
            
            # Agora sim, busca as mensagens já salvas no checkpointer
            tup = await active_checkpointer.aget_tuple({"configurable": {"thread_id": thread_id}})
            msgs: List[BaseMessage] = []
            if tup and tup.checkpoint:
                msgs = tup.checkpoint.get("channel_values", {}).get("messages", []) or []
            
            # Evento final entrega o histórico completo já salvo no Postgres/checkpointer
            yield sse_payload(
                {
                    "event": "final",
                    "thread_id": thread_id,
                    "messages": lc_messages_to_list(msgs),
                }
            )
            # Evento done apenas sinaliza encerramento da stream
            yield sse_payload({"event": "done", "thread_id": thread_id})
        except Exception as exc:
            yield sse_payload({"event": "error", "detail": str(exc), "thread_id": thread_id})

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_iterator(), media_type="text/event-stream", headers=headers)


def app_factory():
    """Factory simples usada em runtimes que esperam callable."""
    return app


@app.get("/legal/license")
async def get_license() -> Dict[str, Any]:
    """Exibe a LICENÇA DA COMUNIDADE TOPHAWKS para referência externa e bots."""
    return {
        "name": "LICENÇA DA COMUNIDADE TOPHAWKS",
        "author": "Ronnald Hawk",
        "site": "https://www.rhawk.pro/",
        "text": "Licença não embutida no backend. Consulte a fonte oficial.",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server.main:app", host="0.0.0.0", port=port, reload=True)
