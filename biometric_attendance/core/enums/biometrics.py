"""Enums for the Biometrics domain."""
from enum import Enum


class FingerType(str, Enum):
    LEFT_THUMB = "Left Thumb"
    LEFT_INDEX = "Left Index"
    LEFT_MIDDLE = "Left Middle"
    LEFT_RING = "Left Ring"
    LEFT_LITTLE = "Left Little"
    RIGHT_THUMB = "Right Thumb"
    RIGHT_INDEX = "Right Index"
    RIGHT_MIDDLE = "Right Middle"
    RIGHT_RING = "Right Ring"
    RIGHT_LITTLE = "Right Little"


class DeviceStatus(str, Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
    UNKNOWN = "Unknown"


class BiometricLogType(str, Enum):
    CONNECTION_TEST = "Connection Test"
    SYNC = "Sync"
    PUSH_USER = "Push User"
    PULL_LOGS = "Pull Logs"
    ERROR = "Error"
