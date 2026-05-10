"""CRUD de técnicos — persistência em SQLite."""

import uuid
from services.database import get_conn, _insert_tecnico
from services.log import log_action


def load_tecnicos() -> list:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM tecnicos ORDER BY nome").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def save_tecnicos(tecnicos: list) -> None:
    """Substitui toda a tabela (mantido para compatibilidade)."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM tecnicos")
        for t in tecnicos:
            _insert_tecnico(conn, t)
        conn.commit()
    finally:
        conn.close()


def add_tecnico(tecnico: dict, usuario: str = "", perfil: str = "") -> None:
    if not tecnico.get("id"):
        tecnico["id"] = str(uuid.uuid4())
    conn = get_conn()
    try:
        _insert_tecnico(conn, tecnico)
        conn.commit()
    finally:
        conn.close()
    log_action(usuario, perfil, "criar", "tecnico", tecnico.get("nome", ""))


def update_tecnico(original_cpf: str, updated: dict,
                   usuario: str = "", perfil: str = "") -> None:
    conn = get_conn()
    try:
        exists = conn.execute(
            "SELECT id FROM tecnicos WHERE cpf=?", (original_cpf,)
        ).fetchone()
        if not updated.get("id"):
            updated["id"] = exists["id"] if exists else str(uuid.uuid4())
        _insert_tecnico(conn, updated)
        conn.commit()
    finally:
        conn.close()
    acao = "editar" if exists else "criar"
    log_action(usuario, perfil, acao, "tecnico", updated.get("nome", ""))


def delete_tecnico(cpf: str, nome: str = "", usuario: str = "", perfil: str = "") -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM tecnicos WHERE cpf=?", (cpf,))
        conn.commit()
    finally:
        conn.close()
    log_action(usuario, perfil, "excluir", "tecnico", nome or cpf)
