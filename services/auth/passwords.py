"""Bcrypt's budget is UTF-8 bytes, never characters or a truncated prefix."""

MAX_PASSWORD_BYTES = 72


def password_bytes(password: str) -> bytes:
    """Encode the exact password or reject it without disclosing its content."""
    if not password:
        raise ValueError("Password cannot be empty")
    try:
        encoded = password.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError("Password must be valid UTF-8") from exc
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError("Password must be at most 72 UTF-8 bytes")
    return encoded
