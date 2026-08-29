"""
FreeStack Core Framework

A production-grade, modular full-stack development framework.
"""

__version__ = "0.1.0"
__author__ = "FreeStack Contributors"
__email__ = "dev@freestack.dev"

from .config import settings, Settings
from .database import get_db, init_db, close_db
from .logging import setup_logging, get_logger
from .auth import create_access_token, verify_token, get_password_hash, verify_password
from .events import event_bus, Event, EventHandler
from .health import health_check, readiness_check

__all__ = [
    "settings",
    "Settings",
    "get_db",
    "init_db",
    "close_db",
    "setup_logging",
    "get_logger",
    "create_access_token",
    "verify_token",
    "get_password_hash",
    "verify_password",
    "event_bus",
    "Event",
    "EventHandler",
    "health_check",
    "readiness_check",
]