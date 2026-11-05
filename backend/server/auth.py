import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Tuple

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"


def get_secret() -> str:
    """Recupera AUTH_SECRET garantindo que exista."""
    secret = os.getenv("AUTH_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="AUTH_SECRET não configurado")
    return secret


def get_passkey_sources() -> Tuple[str | None, str | None]:
    """Obtém hash e/ou valor plano configurados via ambiente."""
    hashed = os.getenv("ACCESS_KEY_HASH")
    plain = os.getenv("ACCESS_KEY")
    return hashed, plain


def is_valid_bcrypt_hash(value: str | None) -> bool:
    """Verifica formato mínimo esperado de um hash bcrypt ($2b$, $2y$, etc.)."""
    if not value:
        return False
    return value.startswith("$2a$") or value.startswith("$2b$") or value.startswith("$2y$")


def token_ttl_seconds() -> int:
    """Define a validade do token em segundos (default: 1h)."""
    raw = os.getenv("AUTH_TOKEN_TTL_SECONDS", "3600")
    try:
        ttl = int(raw)
    except ValueError:
        ttl = 3600
    return max(ttl, 60)


def verify_passkey(passkey: str) -> None:
    """Valida a passkey recebida comparando com hash ou valor simples."""
    hashed, plain = get_passkey_sources()
    if hashed and not is_valid_bcrypt_hash(hashed):
        # Ignora hash inválido para evitar travar ambientes com placeholder
        hashed = None
    if hashed:
        try:
            if bcrypt.checkpw(passkey.encode("utf-8"), hashed.encode("utf-8")):
                return
        except (ValueError, TypeError):
            # Hash presente mas inválido → cai para validação plain se existir
            hashed = None
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Passkey inválida")
    if plain:
        if secrets.compare_digest(passkey, plain):
            return
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Passkey inválida")
    raise HTTPException(status_code=500, detail="ACCESS_KEY_HASH ou ACCESS_KEY ausentes")


def issue_token(subject: str = "operator") -> Tuple[str, datetime]:
    """Gera JWT simples com expiração e retorna token + timestamp ISO."""
    secret = get_secret()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_ttl_seconds())
    payload = {"sub": subject, "exp": int(expires_at.timestamp())}
    token = jwt.encode(payload, secret, algorithm=ALGORITHM)
    return token, expires_at


def decode_token(token: str) -> Dict[str, Any]:
    """Decodifica e valida o token recebido no header Authorization."""
    secret = get_secret()
    try:
        return jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc


async def require_token(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Dict[str, Any]:
    """Dependência usada nas rotas protegidas."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    return decode_token(credentials.credentials)


def login_with_passkey(passkey: str) -> Tuple[str, datetime]:
    """Processa o login verificando a chave e emitindo novo token."""
    if not passkey:
        raise HTTPException(status_code=400, detail="Passkey obrigatória")
    verify_passkey(passkey)
    return issue_token()
