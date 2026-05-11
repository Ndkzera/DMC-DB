"""Autenticação — usuários em SQLite, senhas com sha256."""

import hashlib
import time
import uuid
from nicegui import app
from services.database import get_conn, _insert_usuario

PERFIS = [
    "DESENVOLVEDOR",
    "ADMINISTRADOR",
    "FUNCIONÁRIO PRIORITÁRIO",
    "FUNCIONÁRIO",
    "FUNCIONÁRIO CAMPO",
]

PERFIL_CORES = {
    "DESENVOLVEDOR":           ("#C4B5FD", "rgba(196,181,253,.12)", "rgba(196,181,253,.3)"),
    "ADMINISTRADOR":           ("#FBBF24", "rgba(251,191,36,.10)",  "rgba(251,191,36,.28)"),
    "FUNCIONÁRIO PRIORITÁRIO": ("#60A5FA", "rgba(96,165,250,.10)",  "rgba(96,165,250,.28)"),
    "FUNCIONÁRIO":             ("#4ADE80", "rgba(74,222,128,.08)",  "rgba(74,222,128,.25)"),
    "FUNCIONÁRIO CAMPO":       ("#34D399", "rgba(52,211,153,.08)",  "rgba(52,211,153,.25)"),
}


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _row_to_user(row) -> dict:
    d = dict(row)
    d["admin"] = bool(d.get("admin", 0))
    return d


def _load() -> list:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM usuarios").fetchall()
        return [_row_to_user(r) for r in rows]
    finally:
        conn.close()


def _save(users: list) -> None:
    """Substitui toda a tabela (mantido para compatibilidade)."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM usuarios")
        for u in users:
            _insert_usuario(conn, u)
        conn.commit()
    finally:
        conn.close()


_DEFAULT_EMAIL = "n_dk@live.com"
_DEFAULT_NOME  = "Nilton Jr"


def ensure_default_user() -> None:
    conn = get_conn()
    try:
        default = conn.execute(
            "SELECT * FROM usuarios WHERE perfil='DESENVOLVEDOR' OR admin=1 LIMIT 1"
        ).fetchone()
        if default is None:
            conn.execute(
                "INSERT OR IGNORE INTO usuarios VALUES(?,?,?,?,?,?,?,?)",
                (
                    str(uuid.uuid4()), _DEFAULT_NOME, _DEFAULT_EMAIL,
                    "", "Desenvolvedor", _hash("1234"), "DESENVOLVEDOR", 1,
                ),
            )
            conn.commit()
            return
        changed = False
        updates = {}
        if default["email"] != _DEFAULT_EMAIL:
            updates["email"] = _DEFAULT_EMAIL
            changed = True
        if default["nome"] != _DEFAULT_NOME:
            updates["nome"] = _DEFAULT_NOME
            changed = True
        if not default["perfil"]:
            updates["perfil"] = "DESENVOLVEDOR"
            changed = True
        if changed:
            for col, val in updates.items():
                conn.execute(
                    f"UPDATE usuarios SET {col}=? WHERE id=?",
                    (val, default["id"]),
                )
            conn.commit()
    finally:
        conn.close()


def check_login(email_or_nome: str, senha: str) -> dict | None:
    h = _hash(senha)
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM usuarios WHERE (email=? OR nome=?) AND senha_hash=?",
            (email_or_nome, email_or_nome, h),
        ).fetchone()
        return _row_to_user(row) if row else None
    finally:
        conn.close()


def is_authenticated() -> bool:
    return bool(app.storage.user.get("dmc_logged_in"))


def mark_active(email: str, nome: str) -> None:
    """Registra/renova sessão ativa em storage.general (compartilhado entre todos)."""
    online: dict = app.storage.general.get("online", {})
    online[email] = {"nome": nome, "ts": time.time()}
    app.storage.general["online"] = online


def mark_inactive(email: str) -> None:
    """Remove sessão ativa do storage.general."""
    online: dict = app.storage.general.get("online", {})
    online.pop(email, None)
    app.storage.general["online"] = online


def get_active_users() -> list[dict]:
    """Retorna usuários com heartbeat nos últimos 2 minutos."""
    cutoff = time.time() - 120
    return [
        v for v in app.storage.general.get("online", {}).values()
        if v.get("ts", 0) >= cutoff
    ]


def get_active_count() -> int:
    return len(get_active_users())


def login_user(user: dict) -> None:
    app.storage.user["dmc_logged_in"] = True
    app.storage.user["dmc_user_nome"]   = user.get("nome", "")
    app.storage.user["dmc_user_email"]  = user.get("email", "")
    app.storage.user["dmc_user_perfil"] = user.get("perfil", "FUNCIONÁRIO")
    app.storage.user["dmc_user_admin"]  = user.get("admin", False)
    mark_active(user.get("email", ""), user.get("nome", ""))


def logout_user() -> None:
    email = app.storage.user.get("dmc_user_email", "")
    if email:
        mark_inactive(email)
    app.storage.user["dmc_logged_in"] = False
    for k in ("dmc_user_nome", "dmc_user_email", "dmc_user_perfil", "dmc_user_admin"):
        app.storage.user.pop(k, None)


def current_user_name() -> str:
    return app.storage.user.get("dmc_user_nome", "")


def current_user_perfil() -> str:
    return app.storage.user.get("dmc_user_perfil", "FUNCIONÁRIO")


def current_user_label() -> str:
    nome = app.storage.user.get("dmc_user_nome", "").strip()
    if nome:
        return nome
    email = app.storage.user.get("dmc_user_email", "").strip()
    if email:
        return email.split("@")[0]
    return app.storage.user.get("dmc_user_perfil", "Usuário")
