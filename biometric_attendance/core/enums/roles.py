"""Role definitions from 02-AUTHENTICATION-AUTHORIZATION.md §4."""
from enum import StrEnum


class RoleName(StrEnum):
    ADMINISTRATOR = "Administrator"
    HR = "HR"
    SUPERVISOR = "Supervisor"
    KIOSK = "Kiosk"
