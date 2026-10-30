"""Configuración y administración de la base de datos SQLite.

Este módulo se encarga únicamente de crear la base de datos y de abrir
conexiones seguras. La lógica de los hábitos vive en ``habit_manager.py``.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# La base de datos se guarda junto al código del proyecto, sin importar
# desde qué carpeta se ejecute Streamlit.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "habits.db"

# Tablas del proyecto:
# - habits: los hábitos que crea el usuario.
# - habit_records: un registro por hábito y día completado.
SCHEMA = """
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS habit_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id INTEGER NOT NULL,
    record_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (habit_id, record_date),
    FOREIGN KEY (habit_id) REFERENCES habits (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_records_date
    ON habit_records (record_date);

CREATE INDEX IF NOT EXISTS idx_records_habit
    ON habit_records (habit_id, record_date);
"""


def get_connection() -> sqlite3.Connection:
    """Abre una conexión a SQLite con filas accesibles por nombre."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    # Sin esta opción, SQLite no elimina los registros de un hábito borrado.
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def db_connection() -> Iterator[sqlite3.Connection]:
    """Entrega una conexión y confirma o revierte los cambios automáticamente."""
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    """Crea la base de datos y las tablas si todavía no existen."""
    with db_connection() as connection:
        connection.executescript(SCHEMA)
