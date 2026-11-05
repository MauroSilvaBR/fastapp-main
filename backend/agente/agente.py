"""Agente simples (KISS) usando LangChain 1.0.

Mantém as funções públicas: `tavily_search`, `create_agent_graph`, `build_graph`, `graph`.
Traz troca dinâmica de modelo/ferramentas via SystemMessage e runtime config,
com um middleware pequeno e direto.
"""

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Iterable, List, Optional

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from agente.tools import tavily_search
from agente.middleware import DynamicSettingsMiddleware


load_dotenv()

# Configuração simples por variáveis de ambiente
DEBUG_AGENT_LOGS = os.getenv("DEBUG_AGENT_LOGS", "false").strip().lower() in {"1", "true", "yes"}

STUDIO_MODEL_NAME = os.getenv("STUDIO_MODEL_NAME")
STUDIO_USE_TAVILY = os.getenv("STUDIO_USE_TAVILY")

DEFAULT_MODEL_NAME = STUDIO_MODEL_NAME or os.getenv("DEFAULT_MODEL_NAME", "google/gemini-2.5-flash")
DEFAULT_USE_TAVILY = (STUDIO_USE_TAVILY or os.getenv("DEFAULT_USE_TAVILY", "false")).strip().lower() in {"1", "true", "yes"}

# Data atual no fuso de São Paulo (Brasil), formato DD/MM/AAAA
DATA_ATUAL_SP = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")

DEFAULT_SYSTEM_PROMPT = os.getenv(
    "DEFAULT_SYSTEM_PROMPT",
    (
        f"Você é um copiloto que auxilia o time TopHawks. Hoje é {DATA_ATUAL_SP} (fuso de São Paulo). "
        "Quando perguntarem a data de hoje, responda usando essa data de forma direta, sem dizer que não tem acesso a informações em tempo real. "
        "Se pedirem a hora exata, responda que só dispõe da data."
    ),
)

DEFAULT_OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
SUMMARY_MODEL_NAME = "google/gemini-2.0-flash-001"


def dbg(*args):
    """Imprime logs simples quando `DEBUG_AGENT_LOGS` estiver habilitado.

    Parâmetros:
    - args: valores a serem impressos (serão convertidos para string).
    """
    if DEBUG_AGENT_LOGS:
        try:
            print(*args, flush=True)
        except Exception:
            pass

def create_agent_graph(
    model_name: str,
    system_prompt: str,
    use_tavily: bool = False,
    tools: Optional[Iterable[BaseTool]] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
    temperature: float = 0.2,
    checkpointer: Optional[BaseCheckpointSaver] = None,
):
    """Cria e retorna um agente simples com o modelo e ferramentas informados.

    Conceito (Factory): esta função é uma "fábrica". Ela recebe
    parâmetros, monta as dependências (modelo, ferramentas, middleware)
    e devolve um objeto pronto (o agente Runnable). Ou seja, ela não
    executa o agente; apenas constrói e retorna uma instância configurada
    para ser usada depois.

    Dica: você pode passar os parâmetros por nome (recomendado para clareza)
    ou por posição, como preferir.

    Parâmetros:
    - model_name: nome do modelo no provedor (ex.: "openai/gpt-4o-mini").
    - system_prompt: instruções iniciais do agente.
    - use_tavily: quando True, ativa a ferramenta de busca Tavily.
    - tools: outras ferramentas a adicionar (iterável de BaseTool).
    - openrouter_api_key: chave da API do OpenRouter (fallback para env `OPENROUTER_API_KEY`).
    - openrouter_base_url: URL base da API do OpenRouter.
    - temperature: temperatura do modelo (criatividade).

    Retorno:
    - Runnable do agente criado pelo LangChain (compatível com LangGraph).
    """

    api_key = openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Defina OPENROUTER_API_KEY para inicializar o agente.")

    agent_tools: List[BaseTool] = list(tools or [])
    # Sempre registre ferramenta para evitar erro de "unknown tool"
    try:
        has_tavily = any(getattr(t, "name", None) == getattr(tavily_search, "name", "tavily_search") for t in agent_tools)
        if not has_tavily:
            agent_tools.append(tavily_search)
    except Exception:
        pass

    model = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base=openrouter_base_url,
    )

    dbg(f"[AGENT] model={model_name} tavily={use_tavily} tools={len(agent_tools)}")

    # Middleware simples para troca dinâmica via SystemMessage e runtime config
    middlewares = [DynamicSettingsMiddleware()]

    # Middleware extra que resume histórico quando conversa ficar extensa
    summarizer_model = ChatOpenAI(
        model=SUMMARY_MODEL_NAME,
        temperature=0.0,
        openai_api_key=api_key,
        openai_api_base=openrouter_base_url,
    )
    middlewares.append(
        SummarizationMiddleware(
            model=summarizer_model,
            max_tokens_before_summary=10000,
            messages_to_keep=12,
        )
    )

    return create_agent(
        model=model,
        tools=agent_tools,
        system_prompt=system_prompt,
        state_schema=AgentState,
        middleware=middlewares,
        checkpointer=checkpointer,
    )

# Pequeno helper para reconstruir o grafo com parâmetros customizados
def build_graph(
    *,
    model_name: Optional[str] = None,
    system_prompt: Optional[str] = None,
    use_tavily: Optional[bool] = None,
    checkpointer: Optional[BaseCheckpointSaver] = None,
    tools: Optional[Iterable[BaseTool]] = None,
    openrouter_api_key: Optional[str] = None,
    openrouter_base_url: str = DEFAULT_OPENROUTER_BASE_URL,
    temperature: float = 0.2,
):
    return create_agent_graph(
        model_name=model_name or DEFAULT_MODEL_NAME,
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        use_tavily=DEFAULT_USE_TAVILY if use_tavily is None else use_tavily,
        tools=tools,
        openrouter_api_key=openrouter_api_key,
        openrouter_base_url=openrouter_base_url,
        temperature=temperature,
        checkpointer=checkpointer,
    )

# Objeto exportado para langgraph.json e uso direto
# Criado pela factory acima com valores padrão do ambiente.
graph = create_agent_graph(
    model_name=DEFAULT_MODEL_NAME,
    system_prompt=DEFAULT_SYSTEM_PROMPT,
    use_tavily=DEFAULT_USE_TAVILY,
)
