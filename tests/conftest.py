"""Shared pytest configuration and fixtures."""
from __future__ import annotations

import os

# Use in-memory SQLite for all tests unless overridden
os.environ.setdefault("BIOMETRIC_DB_URL", "sqlite:///:memory:")
