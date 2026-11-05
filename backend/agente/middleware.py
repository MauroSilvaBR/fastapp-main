"""Middleware simples para troca dinâmica de modelo e ferramentas.

Controla modelo e execução de ferramentas por requisição.
Ferramentas são bindadas no create_agent; aqui filtramos a lista efetiva
e bloqueamos execução via wrap_tool_call quando desativadas.
"""

import json
import os
from typing import Optional, Callable

from dotenv import load_dotenv
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage
from agente.tools import tavily_search


load_dotenv()

DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").strip().lower() in {"1", "true", "yes"}
DEFAULT_OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_USE_TAVILY = (
    (os.getenv("STUDIO_USE_TAVILY") or os.getenv("DEFAULT_USE_TAVILY", "false")).strip().lower()
    in {"1", "true", "yes"}
)


def dbg(*args):
    if DEBUG_AGENT_LOGS:
        try:
            print(*args, flush=True)
        except Exception:
            pass


def extract_settings_from_messages(messages) -> tuple[Optional[str], Optional[bool]]:
    """Lê a última SystemMessage com JSON {"type":"settings"}.

    Parâmetros:
    - messages: lista de mensagens (LangChain), contendo mensagens do tipo "system".

    Retorno:
    - tupla (model_name, use_tavily) quando encontrados; senão (None, None).
    """
    model_name: Optional[str] = None
    use_tavily: Optional[bool] = None
    for msg in reversed(messages or []):
        try:
            if getattr(msg, "type", None) != "system":
                continue
            content = getattr(msg, "content", None)
            if not isinstance(content, str):
                continue
            data = json.loads(content)
            if isinstance(data, dict) and data.get("type") == "settings":
                if isinstance(data.get("model"), str) and data["model"].strip():
                    model_name = data["model"].strip()
                if isinstance(data.get("use_tavily"), bool):
                    use_tavily = data["use_tavily"]
                break
        except Exception:
            continue
    return model_name, use_tavily


def strip_settings_messages(messages):
    """Remove mensagens de configuração do fluxo antes do LLM.

    Parâmetros:
    - messages: lista de mensagens originais.

    Retorno:
    - nova lista sem as mensagens {"type":"settings"}.
    """
    cleaned = []
    for msg in messages or []:
        try:
            if getattr(msg, "type", None) == "system":
                content = getattr(msg, "content", None)
                if isinstance(content, str):
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict) and data.get("type") == "settings":
                            continue
                    except Exception:
                        pass
        except Exception:
            pass
        cleaned.append(msg)
    return cleaned


class DynamicSettingsMiddleware(AgentMiddleware):
    """Troca dinâmica de modelo e controle de ferramentas por requisição."""

    def _inject_guardrail(self, messages, desired):
        if desired:
            return messages
        try:
            guardrail = SystemMessage(
                content=(
                    "A ferramenta de busca 'tavily_search' está desabilitada para esta "
                    "requisição. Não invente ou suponha resultados de pesquisa. Se o "
                    "usuário solicitar pesquisa na web, responda explicitamente que a "
                    "pesquisa está desabilitada e peça para habilitar Tavily."
                )
            )
            return list(messages) + [guardrail]
        except Exception:
            return messages

    def _desired_use_tavily(self, request) -> bool:
        """Resolve o valor final de use_tavily para a requisição atual.

        Ordem de precedência:
        - runtime.config.configurable.use_tavily
        - runtime.context.use_tavily
        - SystemMessage {type:"settings"}
        - DEFAULT_USE_TAVILY (env)
        """
        desired = DEFAULT_USE_TAVILY
        try:
            runtime = getattr(request, "runtime", None)
            # config.configurable
            runtime_cfg = getattr(runtime, "config", None)
            if isinstance(runtime_cfg, dict):
                cfg = runtime_cfg.get("configurable", {}) or {}
                if isinstance(cfg.get("use_tavily"), bool):
                    desired = cfg["use_tavily"]
            # context
            ctx = getattr(runtime, "context", None)
            if isinstance(ctx, dict) and isinstance(ctx.get("use_tavily"), bool):
                desired = ctx["use_tavily"]
        except Exception:
            pass
        # system message (se ainda presente no state)
        try:
            state = getattr(request, "state", None)
            messages = []
            if isinstance(state, dict):
                messages = state.get("messages", [])
            _, sm_tavily = extract_settings_from_messages(messages)
            if isinstance(sm_tavily, bool):
                desired = sm_tavily
        except Exception:
            pass
        return desired

    def _resolve_prefs(self, request: ModelRequest) -> tuple[Optional[str], bool, list]:
        messages = getattr(request, "messages", None) or []
        model_name, use_tavily = extract_settings_from_messages(messages)
        runtime = getattr(request, "runtime", None)
        try:
            runtime_cfg = getattr(runtime, "config", None)
            if isinstance(runtime_cfg, dict):
                cfg = runtime_cfg.get("configurable", {}) or {}
                if isinstance(cfg.get("model_name"), str) and cfg["model_name"].strip():
                    model_name = cfg["model_name"].strip()
                if isinstance(cfg.get("use_tavily"), bool):
                    use_tavily = cfg["use_tavily"]
            ctx = getattr(runtime, "context", None)
            if isinstance(ctx, dict):
                if isinstance(ctx.get("model_name"), str) and ctx["model_name"].strip():
                    model_name = ctx["model_name"].strip()
                if isinstance(ctx.get("use_tavily"), bool):
                    use_tavily = ctx["use_tavily"]
        except Exception:
            pass
        desired = DEFAULT_USE_TAVILY if use_tavily is None else use_tavily
        tools = list(getattr(request, "tools", []) or [])
        return model_name, desired, tools

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        model_name, desired, tools = self._resolve_prefs(request)

        tavily_name = getattr(tavily_search, "name", "tavily_search")
        tools_filtered = [t for t in tools if getattr(t, "name", None) != tavily_name]
        if desired and any(getattr(t, "name", None) == tavily_name for t in tools):
            tools_filtered.append(tavily_search)

        cleaned = strip_settings_messages(getattr(request, "messages", []) or [])
        cleaned = self._inject_guardrail(cleaned, desired)

        new_model = getattr(request, "model", None)
        try:
            if model_name:
                new_model = ChatOpenAI(
                    model=model_name,
                    temperature=0.2,
                    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                    openai_api_base=os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL),
                )
        except Exception as e:
            dbg(f"[SETTINGS] erro ao aplicar modelo: {e}")

        request.model = new_model
        request.messages = cleaned
        request.tools = tools_filtered
        dbg(
            f"[MIDDLEWARE] Model resolved: {model_name or 'default'} | "
            f"Tavily enabled: {desired} | tools before={len(tools)} after={len(tools_filtered)}"
        )
        return handler(request)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        model_name, desired, tools = self._resolve_prefs(request)

        tavily_name = getattr(tavily_search, "name", "tavily_search")
        tools_filtered = [t for t in tools if getattr(t, "name", None) != tavily_name]
        if desired and any(getattr(t, "name", None) == tavily_name for t in tools):
            tools_filtered.append(tavily_search)

        cleaned = strip_settings_messages(getattr(request, "messages", []) or [])
        cleaned = self._inject_guardrail(cleaned, desired)

        new_model = getattr(request, "model", None)
        try:
            if model_name:
                new_model = ChatOpenAI(
                    model=model_name,
                    temperature=0.2,
                    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                    openai_api_base=os.getenv("OPENROUTER_BASE_URL", DEFAULT_OPENROUTER_BASE_URL),
                )
        except Exception as e:
            dbg(f"[SETTINGS-ASYNC] erro ao aplicar modelo: {e}")

        request.model = new_model
        request.messages = cleaned
        request.tools = tools_filtered
        dbg(
            f"[MIDDLEWARE-ASYNC] Model resolved: {model_name or 'default'} | "
            f"Tavily enabled: {desired} | tools before={len(tools)} after={len(tools_filtered)}"
        )
        return await handler(request)

    def wrap_tool_call(self, request, handler):
        try:
            tool = getattr(request, "tool", None)
            tool_name = getattr(tool, "name", None) if tool is not None else None
            if tool_name is None:
                tool_call = getattr(request, "tool_call", None)
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get("name")
                else:
                    tool_name = getattr(tool_call, "name", None)

            tavily_name = getattr(tavily_search, "name", "tavily_search")
            if tool_name == tavily_name:
                desired = self._desired_use_tavily(request)
                if not desired:
                    tool_call = getattr(request, "tool_call", None)
                    tool_call_id = None
                    if isinstance(tool_call, dict):
                        tool_call_id = tool_call.get("id")
                    else:
                        tool_call_id = getattr(tool_call, "id", None)
                    return ToolMessage(
                        content="Tavily search está desabilitada para esta requisição.",
                        tool_call_id=str(tool_call_id or "tavily-disabled"),
                        status="error",
                    )
        except Exception:
            pass
        return handler(request)

    async def awrap_tool_call(self, request, handler):
        try:
            tool = getattr(request, "tool", None)
            tool_name = getattr(tool, "name", None) if tool is not None else None
            if tool_name is None:
                tool_call = getattr(request, "tool_call", None)
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get("name")
                else:
                    tool_name = getattr(tool_call, "name", None)

            tavily_name = getattr(tavily_search, "name", "tavily_search")
            if tool_name == tavily_name:
                desired = self._desired_use_tavily(request)
                if not desired:
                    tool_call = getattr(request, "tool_call", None)
                    tool_call_id = None
                    if isinstance(tool_call, dict):
                        tool_call_id = tool_call.get("id")
                    else:
                        tool_call_id = getattr(tool_call, "id", None)
                    return ToolMessage(
                        content="Tavily search está desabilitada para esta requisição.",
                        tool_call_id=str(tool_call_id or "tavily-disabled"),
                        status="error",
                    )
        except Exception:
            pass
        return await handler(request)
