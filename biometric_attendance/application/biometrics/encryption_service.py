"""Encryption service for biometric templates."""
import os
from pathlib import Path

from cryptography.fernet import Fernet


class BiometricEncryptionService:
    def __init__(self, key_path: str = "config/.biometric_key"):
        self._key_path = Path(key_path)
        self._fernet = None

    def _ensure_key(self) -> bytes:
        # Check environment variable first
        env_key = os.getenv("BIOMETRIC_ENCRYPTION_KEY")
        if env_key:
            return env_key.encode()

        # Otherwise read/generate from file
        if self._key_path.exists():
            return self._key_path.read_bytes().strip()
        else:
            self._key_path.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            self._key_path.write_bytes(key)
            return key

    def _get_fernet(self) -> Fernet:
        if self._fernet is None:
            key = self._ensure_key()
            self._fernet = Fernet(key)
        return self._fernet

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt the given bytes."""
        return self._get_fernet().encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt the given bytes."""
        return self._get_fernet().decrypt(data)
