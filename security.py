"""Credential hashing for trading PINs and passwords.

Stored secrets were plain `TEXT`, so anything that could read a `users` row —
a leaked key, a screenshot, a backup — read the credential itself. Secrets are
now stored as PBKDF2-HMAC-SHA256 digests with a per-user random salt.

Legacy plaintext rows still verify. On a successful login the caller should
re-write the row through `hash_secret()` (see main.api_login_user), so the
database migrates itself as people sign in rather than needing a reset.

Honest limitation: a 4-digit PIN has only 10,000 possible values, so a stolen
digest is recoverable offline by brute force no matter which KDF is used. That
makes the *primary* controls for the PIN "never disclose it" (no endpoint
returns it) and "rate-limit guessing" (see main._check_rate_limit). Hashing is
defence in depth, not the fix on its own.
"""

import base64
import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 200_000


def hash_secret(secret: str, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Return a self-describing digest: algorithm$iterations$salt$hash."""
    value = (secret or "")
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", value.encode("utf-8"), salt, iterations)
    return "$".join([
        ALGORITHM,
        str(iterations),
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(derived).decode("ascii"),
    ])


def is_hashed(stored: str) -> bool:
    return isinstance(stored, str) and stored.startswith(ALGORITHM + "$")


def verify_secret(secret: str, stored: str) -> bool:
    """Constant-time check of `secret` against a stored value.

    A value that is not in the hashed format is treated as a legacy plaintext
    row and compared as-is, which is what lets existing accounts keep working.
    """
    if not stored:
        return False
    if not is_hashed(stored):
        return hmac.compare_digest((secret or ""), stored)
    try:
        _, iterations, salt_b64, digest_b64 = stored.split("$", 3)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        rounds = int(iterations)
    except Exception:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", (secret or "").encode("utf-8"), salt, rounds)
    return hmac.compare_digest(derived, expected)


def needs_rehash(stored: str) -> bool:
    """True when a stored secret is still in the legacy plaintext form."""
    return bool(stored) and not is_hashed(stored)
