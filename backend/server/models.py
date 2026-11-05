from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ThreadObj(BaseModel):
    thread_id: str
    created_at: Optional[str] = None
    values: Optional[Dict[str, Any]] = None


class ThreadSearchRequest(BaseModel):
    limit: Optional[int] = Field(default=50, ge=1, le=500)


class MessageInput(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class RunInput(BaseModel):
    messages: List[MessageInput]


class RunConfig(BaseModel):
    configurable: Dict[str, Any] = Field(default_factory=dict)


class RunRequest(BaseModel):
    assistant_id: Optional[str] = None
    input: RunInput
    config: Optional[RunConfig] = None


class RunResult(BaseModel):
    messages: List[Dict[str, Any]]


class RunResponse(BaseModel):
    result: RunResult


class LoginRequest(BaseModel):
    passkey: str


class LoginResponse(BaseModel):
    token: str
    expires_at: str
