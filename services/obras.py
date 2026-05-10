"""CRUD de obras — persistência em SQLite."""

import uuid
from datetime import datetime
from services.database import get_conn, _insert_obra
from services.log import log_action


def load_obras() -> list:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM obras ORDER BY data_criacao DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_obras(obras: list) -> None:
    """Substitui toda a tabela (mantido para compatibilidade)."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM obras")
        for o in obras:
            _insert_obra(conn, o)
        conn.commit()
    finally:
        conn.close()


def add_obra(obra: dict, usuario: str = "", perfil: str = "") -> None:
    if not obra.get("id"):
        obra["id"] = str(uuid.uuid4())
    conn = get_conn()
    try:
        _insert_obra(conn, obra)
        conn.commit()
    finally:
        conn.close()
    log_action(usuario, perfil, "criar", "obra",
               obra.get("cliente_nome", ""), obra.get("obra_log", ""))


def update_obra_status(obra_id: str, status: str,
                       usuario: str = "", perfil: str = "") -> None:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE obras SET status=?, data_atualizacao=? WHERE id=?",
            (status, agora, obra_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT cliente_nome, obra_log FROM obras WHERE id=?", (obra_id,)
        ).fetchone()
    finally:
        conn.close()
    if row:
        log_action(usuario, perfil, "editar", "obra",
                   row["cliente_nome"], row["obra_log"], f"Status → {status}")


def delete_obra(obra_id: str, nome: str = "", usuario: str = "", perfil: str = "") -> None:
    conn = get_conn()
    try:
        if not nome:
            row = conn.execute(
                "SELECT cliente_nome FROM obras WHERE id=?", (obra_id,)
            ).fetchone()
            nome = row["cliente_nome"] if row else obra_id
        conn.execute("DELETE FROM obras WHERE id=?", (obra_id,))
        conn.commit()
    finally:
        conn.close()
    log_action(usuario, perfil, "excluir", "obra", nome)
