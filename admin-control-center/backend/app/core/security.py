import base64
import hashlib
import hmac
import os
import struct
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.core.config import get_admin_settings

settings = get_admin_settings()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def generate_totp_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode("ascii").rstrip("=")


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    if not secret or not code or not code.isdigit() or len(code) != 6:
        return False
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded.upper())
    counter = int(time.time() // 30)
    for offset in range(-window, window + 1):
        msg = struct.pack(">Q", counter + offset)
        digest = hmac.new(key, msg, hashlib.sha1).digest()
        pos = digest[-1] & 0x0F
        truncated = struct.unpack(">I", digest[pos : pos + 4])[0] & 0x7FFFFFFF
        if f"{truncated % 1000000:06d}" == code:
            return True
    return False


def create_admin_token(
    subject: str,
    admin_role: str,
    mfa_verified: bool = True,
    expires_minutes: Optional[int] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or settings.ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: Dict[str, Any] = {
        "sub": subject,
        "scope": "admin_control_center",
        "admin_role": admin_role,
        "mfa_verified": mfa_verified,
        "iat": now,
        "exp": exp,
    }
    return jwt.encode(payload, settings.ADMIN_JWT_SECRET_KEY, algorithm=settings.ADMIN_JWT_ALGORITHM)


def decode_admin_token(token: str) -> Dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.ADMIN_JWT_SECRET_KEY,
        algorithms=[settings.ADMIN_JWT_ALGORITHM],
    )
    if payload.get("scope") != "admin_control_center":
        raise jwt.InvalidTokenError("Invalid admin token scope")
    return payload
