"""CRUD de registros de ponto — persistência em SQLite."""

import uuid
from services.database import get_conn, _insert_ponto
from services.log import log_action


def load_ponto() -> list:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM ponto ORDER BY data, hora"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_ponto(registros: list) -> None:
    """Substitui toda a tabela (mantido para compatibilidade)."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM ponto")
        for r in registros:
            _insert_ponto(conn, r)
        conn.commit()
    finally:
        conn.close()


def add_registro(registro: dict, usuario: str = "", perfil: str = "") -> None:
    if not registro.get("id"):
        registro["id"] = str(uuid.uuid4())
    conn = get_conn()
    try:
        _insert_ponto(conn, registro)
        conn.commit()
    finally:
        conn.close()
    tipo_label = "Check-in" if registro.get("tipo") == "checkin" else "Check-out"
    log_action(
        usuario or registro.get("usuario", ""),
        perfil,
        "criar", "ponto",
        f"{tipo_label} — {registro.get('usuario', '')}",
        registro.get("obra", ""),
    )


def delete_registro(reg_id: str, usuario: str = "", perfil: str = "") -> None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM ponto WHERE id=?", (reg_id,)).fetchone()
        conn.execute("DELETE FROM ponto WHERE id=?", (reg_id,))
        conn.commit()
    finally:
        conn.close()
    if row:
        tipo_label = "Check-in" if row["tipo"] == "checkin" else "Check-out"
        log_action(
            usuario, perfil,
            "excluir", "ponto",
            f"{tipo_label} — {row['usuario']}",
            row["obra"],
        )
