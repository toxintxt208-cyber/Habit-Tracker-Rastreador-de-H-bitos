"""Interfaz web del Habit Tracker con Streamlit.

Ejecuta la aplicación con:
    streamlit run app.py
"""

from __future__ import annotations

import html
import sqlite3
from datetime import date, timedelta

import streamlit as st

import database
import habit_manager as habits

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Habit Tracker",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    :root {
        --bg: #080d19;
        --card: rgba(17, 26, 46, 0.82);
        --border: rgba(148, 163, 184, 0.16);
        --text: #e8eefc;
        --muted: #94a3b8;
        --green: #34d399;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            Helvetica, Arial, sans-serif;
    }

    .stApp {
        background:
            radial-gradient(1100px 600px at 8% -10%, rgba(52, 211, 153, 0.12), transparent 60%),
            radial-gradient(900px 500px at 100% 0%, rgba(96, 165, 250, 0.10), transparent 55%),
            var(--bg);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: #0c1424;
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] hr {
        border-color: var(--border);
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    .hero {
        padding: 0.25rem 0 0.5rem 0;
    }

    .hero-kicker {
        color: var(--green);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .hero-title {
        color: var(--text);
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.1;
        margin: 0;
    }

    .hero-text {
        color: var(--muted);
        font-size: 1rem;
        margin-top: 0.45rem;
        margin-bottom: 0;
    }

    .brand {
        color: var(--text);
        font-size: 1.3rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-top: 0.4rem;
    }

    .date-caption {
        color: var(--muted);
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-align: right;
        margin-bottom: 0.2rem;
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        gap: 0.75rem;
        margin: 0.6rem 0 0.9rem 0;
    }

    .stat-card {
        background: linear-gradient(160deg, rgba(23, 34, 58, 0.95), rgba(13, 21, 38, 0.95));
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
        min-width: 0;
    }

    .stat-label {
        color: var(--muted);
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .stat-value {
        color: var(--text);
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin-top: 0.35rem;
        white-space: nowrap;
    }

    .stat-unit {
        color: var(--muted);
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0;
    }

    .stat-hint {
        color: var(--muted);
        font-size: 0.74rem;
        margin-top: 0.2rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    .stAppDeployButton {
        display: none;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--card);
        border: 1px solid var(--border) !important;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
    }

    .habit-name {
        color: var(--text);
        font-size: 1.06rem;
        font-weight: 650;
        line-height: 1.3;
        overflow-wrap: anywhere;
    }

    .habit-meta {
        color: var(--muted);
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }

    .streak-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.7rem;
    }

    .streak-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: rgba(52, 211, 153, 0.08);
        border: 1px solid rgba(52, 211, 153, 0.20);
        border-radius: 999px;
        color: var(--text);
        font-size: 0.76rem;
        padding: 0.3rem 0.65rem;
    }

    .streak-pill.best {
        background: rgba(251, 191, 36, 0.08);
        border-color: rgba(251, 191, 36, 0.20);
    }

    .streak-pill strong {
        font-weight: 700;
    }

    .side-habit {
        color: var(--text);
        font-size: 0.9rem;
        padding: 0.35rem 0;
        overflow-wrap: anywhere;
    }

    .empty-state {
        background: var(--card);
        border: 1px dashed rgba(148, 163, 184, 0.28);
        border-radius: 18px;
        padding: 2.2rem 1.6rem;
        text-align: center;
        color: var(--muted);
    }

    .empty-state strong {
        color: var(--text);
        display: block;
        font-size: 1.05rem;
        margin-bottom: 0.35rem;
    }

    .section-title {
        color: var(--text);
        font-size: 1.15rem;
        font-weight: 700;
        margin: 0.4rem 0 0.1rem 0;
    }

    .section-text {
        color: var(--muted);
        font-size: 0.86rem;
        margin-bottom: 0.9rem;
    }

    .history-grid {
        background: rgba(8, 13, 25, 0.45);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.7rem 0.9rem;
        margin-top: 0.5rem;
    }

    .history-row {
        display: grid;
        grid-template-columns: minmax(110px, 1.4fr) repeat(7, minmax(28px, 1fr));
        align-items: center;
        gap: 0.3rem;
        padding: 0.28rem 0;
    }

    .history-row + .history-row {
        border-top: 1px solid rgba(148, 163, 184, 0.08);
    }

    .history-head {
        color: var(--muted);
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .history-name {
        color: var(--text);
        font-size: 0.8rem;
        overflow-wrap: anywhere;
        padding-right: 0.25rem;
    }

    .history-day {
        display: flex;
        justify-content: center;
    }

    .day-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border-radius: 8px;
        background: rgba(148, 163, 184, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.14);
        color: #64748b;
        font-size: 0.72rem;
        font-weight: 700;
    }

    .day-mark.done {
        background: rgba(52, 211, 153, 0.16);
        border-color: rgba(52, 211, 153, 0.40);
        color: #6ee7b7;
    }

    .stButton > button,
    .stFormSubmitButton > button {
        border-radius: 11px;
        font-weight: 600;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Funciones auxiliares de la interfaz
# ---------------------------------------------------------------------------
def set_flash(message: str, level: str = "success") -> None:
    """Guarda un mensaje para mostrarlo después de recargar la página."""
    st.session_state["flash_message"] = {"message": message, "level": level}


def show_flash() -> None:
    """Muestra el mensaje pendiente, si existe."""
    flash = st.session_state.pop("flash_message", None)
    if flash:
        getattr(st, flash["level"])(flash["message"])


def days_label(amount: int) -> str:
    """Devuelve '1 día' o 'N días' correctamente."""
    return "1 día" if amount == 1 else f"{amount} días"


def short_date(day: date) -> str:
    """Fecha compacta para tablas, por ejemplo 'lun 27/10'."""
    weekdays = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
    return f"{weekdays[day.weekday()]} {day.strftime('%d/%m')}"


def stat_card(label: str, value: str, hint: str) -> str:
    """Devuelve el HTML de una tarjeta de estadística."""
    return (
        '<div class="stat-card">'
        f'<div class="stat-label">{html.escape(label)}</div>'
        f'<div class="stat-value">{value}</div>'
        f'<div class="stat-hint">{html.escape(hint)}</div>'
        "</div>"
    )


def week_grid(
    habits_list: list[dict], days: list[date], completion_map: dict[date, set[int]]
) -> str:
    """Devuelve una cuadrícula HTML con el cumplimiento de varios días."""
    header_cells = "".join(
        f'<div class="history-day">{day.strftime("%d/%m")}</div>' for day in days
    )
    rows = [
        '<div class="history-row history-head">'
        '<div class="history-name">Hábito</div>'
        f"{header_cells}</div>"
    ]

    for habit in habits_list:
        day_cells = []
        for day in days:
            completed = habit["id"] in completion_map.get(day, set())
            mark_class = "day-mark done" if completed else "day-mark"
            symbol = "✓" if completed else "·"
            day_cells.append(
                f'<div class="history-day">'
                f'<span class="{mark_class}" title="{day.strftime("%d/%m/%Y")}">'
                f"{symbol}</span></div>"
            )

        rows.append(
            '<div class="history-row">'
            f'<div class="history-name">{html.escape(habit["name"])}</div>'
            f'{"".join(day_cells)}</div>'
        )

    return f'<div class="history-grid">{"".join(rows)}</div>'


def safe_run(action, success_message: str) -> None:
    """Ejecuta una acción, informa del resultado y recarga la página."""
    try:
        action()
    except ValueError as error:
        st.error(str(error))
        return
    except sqlite3.Error:
        st.error("No se pudo guardar el cambio en la base de datos.")
        return
    except Exception:
        st.error("Ocurrió un error inesperado. Inténtalo de nuevo.")
        return

    set_flash(success_message)
    st.rerun()


# La base de datos se crea automáticamente la primera vez que se abre la app.
try:
    database.init_db()
except sqlite3.Error:
    st.error(
        "No se pudo preparar la base de datos. "
        "Comprueba que la carpeta del proyecto tenga permisos de escritura."
    )
    st.stop()


# ---------------------------------------------------------------------------
# Barra lateral: crear y eliminar hábitos
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="brand">🌱 Habit Tracker</div>', unsafe_allow_html=True)
    st.caption("Pequeños pasos, grandes cambios.")
    st.divider()

    st.markdown("**Nuevo hábito**")
    with st.form("add_habit_form", clear_on_submit=True):
        new_habit_name = st.text_input(
            "Nombre del hábito",
            max_chars=habits.MAX_NAME_LENGTH,
            placeholder="Ej: Leer 20 minutos",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(
            "+ Agregar hábito", type="primary", width="stretch"
        )

    if submitted:
        try:
            habits.add_habit(new_habit_name)
        except ValueError as error:
            st.error(str(error))
        except sqlite3.Error:
            st.error("No se pudo guardar el hábito. Inténtalo de nuevo.")
        else:
            set_flash(f'Hábito "{new_habit_name.strip()}" agregado 🌱')
            st.rerun()

    st.divider()
    st.markdown("**Mis hábitos**")

    sidebar_habits = habits.get_habits()
    if not sidebar_habits:
        st.caption("Todavía no tienes hábitos registrados.")
    else:
        for habit in sidebar_habits:
            name_column, delete_column = st.columns(
                [0.82, 0.18], vertical_alignment="center"
            )
            with name_column:
                st.markdown(
                    f'<div class="side-habit">{html.escape(habit["name"])}</div>',
                    unsafe_allow_html=True,
                )
            with delete_column:
                if st.button(
                    "🗑️",
                    key=f"delete_habit_{habit['id']}",
                    help="Eliminar hábito y todo su historial",
                    width="content",
                ):
                    try:
                        habits.delete_habit(habit["id"])
                    except sqlite3.Error:
                        st.error("No se pudo eliminar el hábito.")
                    else:
                        set_flash(f'Hábito "{habit["name"]}" eliminado.', "info")
                        st.rerun()

    st.divider()
    st.caption("Tus datos se guardan en un archivo local SQLite (habits.db).")


# ---------------------------------------------------------------------------
# Cabecera y filtro de fecha
# ---------------------------------------------------------------------------
today = date.today()

header_text, header_date = st.columns([0.68, 0.32], vertical_alignment="bottom")
with header_text:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker">Tu progreso, día a día</div>
            <h1 class="hero-title">Habit Tracker</h1>
            <p class="hero-text">
                Registra tus hábitos, mantén la constancia y celebra tus rachas.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_date:
    st.markdown('<div class="date-caption">Fecha</div>', unsafe_allow_html=True)
    selected_day = st.date_input(
        "Fecha a consultar",
        value=today,
        max_value=today,
        format="DD/MM/YYYY",
        label_visibility="collapsed",
    )

show_flash()

# ---------------------------------------------------------------------------
# Datos y estadísticas del día seleccionado
# ---------------------------------------------------------------------------
habits_list = habits.get_habits_with_stats(selected_day)
total_habits = len(habits_list)
completed_today = sum(1 for habit in habits_list if habit["completed"])
daily_percentage = (
    round(completed_today / total_habits * 100, 1) if total_habits else 0.0
)
best_streak = max((habit["best_streak"] for habit in habits_list), default=0)

st.markdown(
    '<div class="stats-grid">'
    + stat_card("Hábitos registrados", str(total_habits), "En tu lista")
    + stat_card(
        "Completados",
        f'{completed_today} <span class="stat-unit">de {total_habits}</span>',
        short_date(selected_day),
    )
    + stat_card(
        "Cumplimiento",
        f"{daily_percentage:.0f}%",
        "Del día consultado",
    )
    + stat_card("Mejor racha", days_label(best_streak), "Récord histórico")
    + "</div>",
    unsafe_allow_html=True,
)

if total_habits:
    st.progress(
        daily_percentage / 100,
        text=(
            f"{completed_today} de {total_habits} hábitos completados "
            f"({daily_percentage:.0f}%)"
        ),
    )

st.write("")

# ---------------------------------------------------------------------------
# Pestañas principales
# ---------------------------------------------------------------------------
daily_tab, stats_tab = st.tabs(["📅 Registro diario", "📊 Estadísticas"])

with daily_tab:
    st.markdown('<div class="section-title">Tus hábitos</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-text">Marca los hábitos que hayas cumplido. '
        "Cada cambio se guarda automáticamente.</div>",
        unsafe_allow_html=True,
    )

    if not habits_list:
        st.markdown(
            """
            <div class="empty-state">
                <strong>Todavía no hay hábitos</strong>
                Agrega tu primer hábito desde la barra lateral para empezar.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for habit in habits_list:
            created_label = date.fromisoformat(habit["created_on"]).strftime(
                "%d/%m/%Y"
            )
            total_label = (
                "1 día"
                if habit["total_completions"] == 1
                else f'{habit["total_completions"]} días'
            )

            with st.container(border=True):
                info_column, action_column = st.columns(
                    [0.72, 0.28], vertical_alignment="center"
                )

                with info_column:
                    st.markdown(
                        f'<div class="habit-name">{html.escape(habit["name"])}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="habit-meta">{total_label} · '
                        f"desde {created_label}</div>",
                        unsafe_allow_html=True,
                    )

                with action_column:
                    if habit["completed"]:
                        clicked = st.button(
                            "✓ Hecho",
                            key=f"uncomplete_{selected_day}_{habit['id']}",
                            type="primary",
                            help="Haz clic para desmarcar este día",
                            width="stretch",
                        )
                        if clicked:
                            safe_run(
                                lambda habit_id=habit["id"]: habits.set_habit_completed(
                                    habit_id, selected_day, False
                                ),
                                "Marca eliminada.",
                            )
                    else:
                        clicked = st.button(
                            "Completar",
                            key=f"complete_{selected_day}_{habit['id']}",
                            help="Guardar este hábito como completado",
                            width="stretch",
                        )
                        if clicked:
                            safe_run(
                                lambda habit_id=habit["id"]: habits.set_habit_completed(
                                    habit_id, selected_day, True
                                ),
                                "¡Hábito completado! Sigue así 🎉",
                            )

                st.markdown(
                    f'<div class="streak-row">'
                    f'<span class="streak-pill">🔥 Racha actual '
                    f'<strong>{days_label(habit["current_streak"])}</strong></span>'
                    f'<span class="streak-pill best">🏆 Mejor racha '
                    f'<strong>{days_label(habit["best_streak"])}</strong></span>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

with stats_tab:
    if not habits_list:
        st.markdown(
            """
            <div class="empty-state">
                <strong>Aún no hay estadísticas</strong>
                Crea un hábito y empieza a marcarlo para ver tu progreso aquí.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        history = habits.get_daily_history(days=14)
        chart_data = {
            "Cumplimiento (%)": {
                short_date(row["date"]): row["percentage"] for row in history
            }
        }

        st.markdown(
            '<div class="section-title">Cumplimiento de los últimos 14 días</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="section-text">Porcentaje de hábitos completados cada día.</div>',
            unsafe_allow_html=True,
        )
        st.bar_chart(chart_data, height=280, y_label="%", color="#34d399")

        st.write("")
        st.markdown(
            '<div class="section-title">Resumen por hábito</div>',
            unsafe_allow_html=True,
        )
        summary_data = {
            "Hábito": [habit["name"] for habit in habits_list],
            "Racha actual": [habit["current_streak"] for habit in habits_list],
            "Mejor racha": [habit["best_streak"] for habit in habits_list],
            "Días": [habit["total_completions"] for habit in habits_list],
        }
        st.dataframe(
            summary_data,
            hide_index=True,
            width="stretch",
            column_config={
                "Hábito": st.column_config.TextColumn(width="medium"),
                "Racha actual": st.column_config.NumberColumn(
                    help="Días consecutivos cumplidos hasta hoy",
                    format="%d",
                    width="small",
                ),
                "Mejor racha": st.column_config.NumberColumn(
                    help="Récord histórico de días consecutivos",
                    format="%d",
                    width="small",
                ),
                "Días": st.column_config.NumberColumn(
                    help="Total de días marcados como completados",
                    format="%d",
                    width="small",
                ),
            },
        )

        st.write("")
        with st.expander("Ver historial detallado"):
            st.markdown("**Últimos 7 días**")
            grid_start = today - timedelta(days=6)
            completion_map = habits.get_completion_map(grid_start, today)
            grid_days = [grid_start + timedelta(days=offset) for offset in range(7)]

            st.markdown(
                week_grid(habits_list, grid_days, completion_map),
                unsafe_allow_html=True,
            )

            st.write("")
            st.markdown("**Historial de los últimos 14 días**")
            history_data = {
                "Día": [short_date(row["date"]) for row in reversed(history)],
                "Completados": [
                    f"{row['completed']} de {row['total']}" for row in reversed(history)
                ],
                "Cumplimiento": [
                    f"{row['percentage']:.0f}%" for row in reversed(history)
                ],
            }
            st.dataframe(history_data, hide_index=True, width="stretch")
