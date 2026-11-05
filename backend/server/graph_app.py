import os
from contextlib import AsyncExitStack

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from agente.agente import build_graph


def get_database_url() -> str:
    """Busca a URL do banco em ambiente de forma simples."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return db_url


def build_agent_graph(checkpointer: AsyncPostgresSaver):
    """Recria o agente padrão já com checkpointer configurado."""
    return build_graph(checkpointer=checkpointer)


async def open_checkpointer() -> tuple[AsyncExitStack, AsyncPostgresSaver]:
    """Cria e mantém um AsyncPostgresSaver ativo até o fechamento."""
    stack = AsyncExitStack()
    cm = AsyncPostgresSaver.from_conn_string(get_database_url())
    saver = await stack.enter_async_context(cm)
    return stack, saver
