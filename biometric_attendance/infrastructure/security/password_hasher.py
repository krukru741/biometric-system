"""bcrypt password hashing wrapper.

Keeps all bcrypt calls in one place so the algorithm can be swapped
without touching application or domain code.
"""
from __future__ import annotations

import bcrypt


class PasswordHasher:
    """Wraps bcrypt for password hashing and verification."""

    _ROUNDS = 12

    def hash(self, plaintext: str) -> str:
        """Return a bcrypt hash string for the given plaintext password."""
        salt = bcrypt.gensalt(rounds=self._ROUNDS)
        return bcrypt.hashpw(plaintext.encode("utf-8"), salt).decode("utf-8")

    def verify(self, plaintext: str, hashed: str) -> bool:
        """Return True if plaintext matches the stored hash."""
        try:
            return bcrypt.checkpw(
                plaintext.encode("utf-8"),
                hashed.encode("utf-8"),
            )
        except Exception:
            return False
