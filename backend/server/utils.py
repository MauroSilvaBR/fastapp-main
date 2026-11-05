from typing import Any, Dict, List
from langchain_core.messages import BaseMessage


def lc_message_to_dict(msg: BaseMessage) -> Dict[str, Any]:
    # Converte BaseMessage para dict serializável similar ao esperado pelo frontend
    data: Dict[str, Any] = {
        "id": getattr(msg, "id", None),
        "type": getattr(msg, "type", None),
        "content": getattr(msg, "content", None),
    }
    # Campos adicionais comuns
    resp = getattr(msg, "response_metadata", None)
    if resp is not None:
        data["response_metadata"] = resp
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls is not None:
        data["tool_calls"] = tool_calls
    add = getattr(msg, "additional_kwargs", None)
    if add is not None:
        data["additional_kwargs"] = add
    created = getattr(msg, "created_at", None)
    if created is not None:
        data["created_at"] = str(created)
    return data


def lc_messages_to_list(msgs: List[BaseMessage]) -> List[Dict[str, Any]]:
    return [lc_message_to_dict(m) for m in msgs]

