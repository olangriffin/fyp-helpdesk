import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:  # pragma: no cover
    from app.models.user import User

settings = get_settings()


def _pbkdf2(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000).hex()


def hash_password(password: str) -> Dict[str, str]:
    salt = secrets.token_bytes(16)
    return {"hash": _pbkdf2(password, salt), "salt": salt.hex()}


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt), stored_hash)


def validate_password_strength(password: str) -> None:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if password.lower() == password or password.upper() == password:
        raise ValueError("Password must include both uppercase and lowercase letters")
    if not any(ch.isdigit() for ch in password):
        raise ValueError("Password must include at least one digit")


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def _sign_data(data: str) -> str:
    return hmac.new(settings.secret_key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session_token(user: "User", expires_minutes: Optional[int] = None) -> str:
    expiry_minutes = expires_minutes or settings.session_expiration_minutes
    expiry = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    payload = {
        "user_id": user.id,
        "role": user.primary_role,
        "exp": int(expiry.timestamp()),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")
    signature = _sign_data(encoded)
    return f"{encoded}.{signature}"


def decode_session_token(token: str) -> Optional[Dict[str, str]]:
    try:
        encoded, signature = token.split(".", 1)
    except ValueError:
        return None
    expected_signature = _sign_data(encoded)
    if not hmac.compare_digest(signature, expected_signature):
        return None
    try:
        raw = base64.urlsafe_b64decode(encoded.encode("utf-8")).decode("utf-8")
        payload = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("exp") and payload["exp"] < int(datetime.utcnow().timestamp()):
        return None
    return payload
