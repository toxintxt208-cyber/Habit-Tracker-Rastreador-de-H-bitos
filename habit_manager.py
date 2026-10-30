"""Lógica de negocio del Habit Tracker.

Aquí se gestionan los hábitos, los registros diarios y el cálculo de rachas.
La interfaz (``app.py``) solo se encarga de mostrar y recoger datos.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Iterable

from database import db_connection

# Límite de caracteres para que los nombres se vean bien en las tarjetas.
MAX_NAME_LENGTH = 60


# ---------------------------------------------------------------------------
# Gestión de hábitos
# ---------------------------------------------------------------------------
def _clean_name(name: str) -> str:
    """Quita espacios sobrantes y valida el nombre de un hábito."""
    cleaned = " ".join(name.split())

    if not cleaned:
        raise ValueError("Escribe un nombre para el hábito.")
    if len(cleaned) > MAX_NAME_LENGTH:
        raise ValueError(
            f"El nombre no puede superar los {MAX_NAME_LENGTH} caracteres."
        )
    return cleaned


def add_habit(name: str) -> int:
    """Crea un hábito nuevo y devuelve su identificador."""
    cleaned = _clean_name(name)

    try:
        with db_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO habits (name) VALUES (?)", (cleaned,)
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        raise ValueError(f'Ya existe un hábito llamado "{cleaned}".') from error


def delete_habit(habit_id: int) -> bool:
    """Elimina un hábito y todos sus registros.

    Devuelve ``True`` si el hábito existía y ``False`` si no se encontró.
    """
    with db_connection() as connection:
        cursor = connection.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        return cursor.rowcount > 0


def get_habits() -> list[dict]:
    """Devuelve todos los hábitos ordenados por fecha de creación."""
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, date(created_at) AS created_on
            FROM habits
            ORDER BY id
            """
        ).fetchall()

    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# Registro diario
# ---------------------------------------------------------------------------
def set_habit_completed(habit_id: int, day: date, completed: bool) -> None:
    """Marca o desmarca un hábito en una fecha concreta.

    El par (hábito, fecha) es único, así que nunca se guardan duplicados.
    """
    if day > date.today():
        raise ValueError("No puedes registrar un día futuro.")

    with db_connection() as connection:
        habit = connection.execute(
            "SELECT 1 FROM habits WHERE id = ?", (habit_id,)
        ).fetchone()

        if habit is None:
            raise ValueError("El hábito ya no existe.")

        if completed:
            connection.execute(
                """
                INSERT OR IGNORE INTO habit_records (habit_id, record_date)
                VALUES (?, ?)
                """,
                (habit_id, day.isoformat()),
            )
        else:
            connection.execute(
                """
                DELETE FROM habit_records
                WHERE habit_id = ? AND record_date = ?
                """,
                (habit_id, day.isoformat()),
            )


def get_completed_habit_ids(day: date) -> set[int]:
    """Devuelve los identificadores de los hábitos completados en un día."""
    with db_connection() as connection:
        rows = connection.execute(
            "SELECT habit_id FROM habit_records WHERE record_date = ?",
            (day.isoformat(),),
        ).fetchall()

    return {int(row["habit_id"]) for row in rows}


def get_completion_map(start_day: date, end_day: date) -> dict[date, set[int]]:
    """Agrupa los hábitos completados por día dentro de un rango de fechas."""
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT habit_id, record_date
            FROM habit_records
            WHERE record_date BETWEEN ? AND ?
            """,
            (start_day.isoformat(), end_day.isoformat()),
        ).fetchall()

    result: dict[date, set[int]] = {}
    for row in rows:
        record_day = date.fromisoformat(row["record_date"])
        result.setdefault(record_day, set()).add(int(row["habit_id"]))
    return result


# ---------------------------------------------------------------------------
# Rachas
# ---------------------------------------------------------------------------
def calculate_streaks(
    completed_days: Iterable[date], today: date | None = None
) -> tuple[int, int]:
    """Calcula la racha actual y la mejor racha de un hábito.

    La racha actual sigue viva si el hábito se completó hoy o ayer: todavía
    queda tiempo para completarlo hoy. Si la última vez fue antes de ayer,
    la racha se considera rota y vuelve a cero.
    """
    today = today or date.today()
    days = sorted(set(completed_days))

    if not days:
        return 0, 0

    best_streak = 1
    current_run = 1

    for previous_day, current_day in zip(days, days[1:]):
        if (current_day - previous_day).days == 1:
            current_run += 1
            best_streak = max(best_streak, current_run)
        else:
            current_run = 1

    best_streak = max(best_streak, current_run)

    # Si la última marca es de hoy o de ayer, la racha final sigue activa.
    if days[-1] < today - timedelta(days=1):
        return 0, best_streak

    return current_run, best_streak


def _get_records_by_habit() -> dict[int, list[date]]:
    """Carga todos los registros agrupados por hábito (una sola consulta)."""
    with db_connection() as connection:
        rows = connection.execute(
            "SELECT habit_id, record_date FROM habit_records ORDER BY record_date"
        ).fetchall()

    records: dict[int, list[date]] = {}
    for row in rows:
        habit_id = int(row["habit_id"])
        records.setdefault(habit_id, []).append(date.fromisoformat(row["record_date"]))
    return records


def get_habits_with_stats(day: date | None = None) -> list[dict]:
    """Devuelve cada hábito con su estado, rachas y total de cumplimientos.

    ``day`` es la fecha que se está consultando en la interfaz. Las rachas
    siempre se calculan tomando como referencia el día real de hoy.
    """
    day = day or date.today()
    records = _get_records_by_habit()
    completed_today = get_completed_habit_ids(day)

    habits_with_stats = []
    for habit in get_habits():
        completed_days = records.get(habit["id"], [])
        current_streak, best_streak = calculate_streaks(completed_days)

        habits_with_stats.append(
            {
                **habit,
                "completed": habit["id"] in completed_today,
                "current_streak": current_streak,
                "best_streak": best_streak,
                "total_completions": len(completed_days),
            }
        )

    return habits_with_stats


# ---------------------------------------------------------------------------
# Historial y estadísticas
# ---------------------------------------------------------------------------
def get_daily_history(days: int = 14, end_day: date | None = None) -> list[dict]:
    """Devuelve el cumplimiento diario de los últimos ``days`` días."""
    if days < 1:
        raise ValueError("El número de días debe ser mayor que cero.")

    end_day = end_day or date.today()
    start_day = end_day - timedelta(days=days - 1)
    total_habits = len(get_habits())
    completion_map = get_completion_map(start_day, end_day)

    history = []
    for offset in range(days):
        current_day = start_day + timedelta(days=offset)
        completed = len(completion_map.get(current_day, set()))
        percentage = round(completed / total_habits * 100, 1) if total_habits else 0.0

        history.append(
            {
                "date": current_day,
                "completed": completed,
                "total": total_habits,
                "percentage": percentage,
            }
        )

    return history
