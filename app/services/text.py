import sqlite3
import unicodedata

from sqlalchemy import event
from sqlalchemy.engine import Engine


def normalize(text):
    """Minúsculas y sin tildes: 'García' -> 'garcia'."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", str(text))
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


@event.listens_for(Engine, "connect")
def _register_norm(dbapi_connection, _record):
    """Expone normalize() como función SQL `norm()` en cada conexión SQLite."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.create_function("norm", 1, normalize, deterministic=True)