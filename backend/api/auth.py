import os
import hashlib
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


def _make_token(password: str) -> str:
    secret = os.getenv("SECRET_KEY", "botty-secret-2024")
    return hashlib.sha256(f"{password}:{secret}".encode()).hexdigest()


def verify_token(token: str) -> bool:
    password = os.getenv("ADMIN_PASSWORD", "")
    if not password:
        return True  # dev mode — no password set
    if not token:
        return False
    return token == _make_token(password)


class LoginRequest(BaseModel):
    password: str


@router.post("/auth/login")
async def login(body: LoginRequest):
    expected = os.getenv("ADMIN_PASSWORD", "")
    if not expected:
        # Dev mode — no password configured, allow all
        return {"token": "dev-mode", "ok": True}
    if body.password != expected:
        raise HTTPException(401, "Contraseña incorrecta")
    return {"token": _make_token(body.password), "ok": True}
