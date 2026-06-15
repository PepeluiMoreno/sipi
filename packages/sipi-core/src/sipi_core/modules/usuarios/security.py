"""Hashing de contraseñas sin dependencias externas (stdlib PBKDF2-HMAC-SHA256).

Formato almacenado: ``pbkdf2_sha256$<iteraciones>$<salt_b64>$<hash_b64>``. Compatible
con verificación constante (`hmac.compare_digest`). Suficiente para SIPI mientras no
haya un IdP/servicio de identidad; sustituible por passlib/argon2 más adelante.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 240_000
_SALT_BYTES = 16


def hash_password(plain: str, *, iterations: int = _ITERATIONS) -> str:
    """Devuelve el hash codificado de una contraseña en claro."""
    if not plain:
        raise ValueError("La contraseña no puede estar vacía")
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
    return f"{_ALGO}${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica una contraseña en claro contra el hash almacenado."""
    try:
        algo, iters, salt_b64, hash_b64 = hashed.split("$")
        if algo != _ALGO:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, int(iters))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# --------------------------------------------------------------------------
# Tokens de acceso JWT (HS256) sin dependencias externas
# --------------------------------------------------------------------------

def get_jwt_secret() -> str:
    """Secreto de firma. En prod debe venir de `SIPI_JWT_SECRET` (env/secret)."""
    return os.getenv("SIPI_JWT_SECRET") or "dev-insecure-secret-change-me"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def create_access_token(sub: str, secret: str, *, expires_seconds: int = 8 * 3600,
                        extra: Optional[dict] = None) -> str:
    """JWT firmado HS256 con `sub` (id de usuario), `iat` y `exp`."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + expires_seconds}
    if extra:
        payload.update(extra)
    seg = (_b64url(json.dumps(header, separators=(",", ":")).encode())
           + "." + _b64url(json.dumps(payload, separators=(",", ":")).encode()))
    sig = hmac.new(secret.encode(), seg.encode("ascii"), hashlib.sha256).digest()
    return seg + "." + _b64url(sig)


def decode_access_token(token: str, secret: str) -> Optional[dict]:
    """Devuelve el payload si la firma es válida y no ha expirado; si no, None."""
    try:
        seg_h, seg_p, seg_s = token.split(".")
        expected = hmac.new(secret.encode(), f"{seg_h}.{seg_p}".encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64url_decode(seg_s)):
            return None
        payload = json.loads(_b64url_decode(seg_p))
        if payload.get("exp") and int(time.time()) > int(payload["exp"]):
            return None
        return payload
    except Exception:
        return None
