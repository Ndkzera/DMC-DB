"""Gerenciador de conexão SQLite, schema e migração de JSON."""

import json
import sqlite3
import uuid
from pathlib import Path

_DB_PATH: Path | None = None


def db_path() -> Path:
    global _DB_PATH
    if _DB_PATH is None:
        from config import CONFIG_DIR
        _DB_PATH = CONFIG_DIR / "dmc.db"
    return _DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


_SCHEMA = """
CREATE TABLE IF NOT EXISTS clientes (
    cpf         TEXT PRIMARY KEY,
    tipo        TEXT NOT NULL DEFAULT 'PF',
    nome        TEXT NOT NULL DEFAULT '',
    telefone    TEXT DEFAULT '',
    end_log     TEXT DEFAULT '',
    end_num     TEXT DEFAULT '',
    end_comp    TEXT DEFAULT '',
    end_bairro  TEXT DEFAULT '',
    end_cidade  TEXT DEFAULT '',
    end_estado  TEXT DEFAULT '',
    end_cep     TEXT DEFAULT '',
    end_maps    TEXT DEFAULT '',
    obra_mesmo  INTEGER DEFAULT 1,
    obra_log    TEXT DEFAULT '',
    obra_num    TEXT DEFAULT '',
    obra_comp   TEXT DEFAULT '',
    obra_bairro TEXT DEFAULT '',
    obra_cidade TEXT DEFAULT '',
    obra_estado TEXT DEFAULT '',
    obra_cep    TEXT DEFAULT '',
    obra_maps   TEXT DEFAULT '',
    data        TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tecnicos (
    id        TEXT PRIMARY KEY,
    cpf       TEXT UNIQUE NOT NULL,
    nome      TEXT NOT NULL DEFAULT '',
    cft       TEXT DEFAULT '',
    telefone  TEXT DEFAULT '',
    email     TEXT DEFAULT '',
    endereco  TEXT DEFAULT '',
    data      TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS obras (
    id               TEXT PRIMARY KEY,
    cliente_nome     TEXT DEFAULT '',
    cliente_cpf      TEXT DEFAULT '',
    obra_log         TEXT DEFAULT '',
    obra_num         TEXT DEFAULT '',
    obra_bairro      TEXT DEFAULT '',
    obra_cidade      TEXT DEFAULT '',
    obra_estado      TEXT DEFAULT '',
    status           TEXT DEFAULT 'Planejamento',
    descricao        TEXT DEFAULT '',
    data_inicio      TEXT DEFAULT '',
    data_fim         TEXT DEFAULT '',
    data_criacao     TEXT DEFAULT '',
    data_atualizacao TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS ponto (
    id          TEXT PRIMARY KEY,
    data        TEXT DEFAULT '',
    hora        TEXT DEFAULT '',
    tipo        TEXT DEFAULT '',
    usuario     TEXT DEFAULT '',
    obra        TEXT DEFAULT '',
    modificador TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS usuarios (
    id         TEXT PRIMARY KEY,
    nome       TEXT NOT NULL DEFAULT '',
    email      TEXT UNIQUE NOT NULL,
    telefone   TEXT DEFAULT '',
    cargo      TEXT DEFAULT '',
    senha_hash TEXT NOT NULL DEFAULT '',
    perfil     TEXT NOT NULL DEFAULT 'FUNCIONÁRIO',
    admin      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS acesso (
    perfil TEXT PRIMARY KEY,
    config TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    data      TEXT DEFAULT '',
    hora      TEXT DEFAULT '',
    usuario   TEXT DEFAULT '',
    perfil    TEXT DEFAULT '',
    forca     INTEGER DEFAULT 0,
    acao      TEXT DEFAULT '',
    entidade  TEXT DEFAULT '',
    nome      TEXT DEFAULT '',
    caminho   TEXT DEFAULT '',
    detalhe   TEXT DEFAULT ''
);
"""


def init_db() -> None:
    """Cria tabelas e migra dados dos JSONs existentes (executa uma vez)."""
    with get_conn() as conn:
        conn.executescript(_SCHEMA)
    _migrate_json()


# ── Migração ─────────────────────────────────────────────────────────────────

def _migrate_json() -> None:
    from config import (
        CLIENTES_FILE, TECNICOS_FILE, OBRAS_FILE, PONTO_FILE, CONFIG_DIR,
    )

    conn = get_conn()
    try:
        if conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
            _import_list(conn, CLIENTES_FILE, "clientes", _insert_cliente)

        if conn.execute("SELECT COUNT(*) FROM tecnicos").fetchone()[0] == 0:
            _import_list(conn, TECNICOS_FILE, "técnicos", _insert_tecnico)

        if conn.execute("SELECT COUNT(*) FROM obras").fetchone()[0] == 0:
            _import_list(conn, OBRAS_FILE, "obras", _insert_obra)

        if conn.execute("SELECT COUNT(*) FROM ponto").fetchone()[0] == 0:
            _import_list(conn, PONTO_FILE, "registros de ponto", _insert_ponto)

        usuarios_file = CONFIG_DIR / "usuarios.json"
        if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
            _import_list(conn, usuarios_file, "usuários", _insert_usuario)

        acesso_file = CONFIG_DIR / "acesso.json"
        if conn.execute("SELECT COUNT(*) FROM acesso").fetchone()[0] == 0:
            _import_acesso(conn, acesso_file)

        log_file = CONFIG_DIR / "audit_log.json"
        if conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0] == 0:
            _import_audit_log(conn, log_file)

    finally:
        conn.close()


def _import_list(conn, path: Path, label: str, fn) -> None:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        for row in rows:
            fn(conn, row)
        conn.commit()
        print(f"[db] migrados {len(rows)} {label}")
    except Exception as e:
        print(f"[db] migração {label}: {e}")


def _import_acesso(conn, path: Path) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for perfil, config in data.items():
            conn.execute(
                "INSERT OR REPLACE INTO acesso(perfil, config) VALUES(?,?)",
                (perfil, json.dumps(config, ensure_ascii=False)),
            )
        conn.commit()
        print(f"[db] migrado acesso ({len(data)} perfis)")
    except Exception as e:
        print(f"[db] migração acesso: {e}")


def _import_audit_log(conn, path: Path) -> None:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        conn.executemany(
            "INSERT INTO audit_log(timestamp,data,hora,usuario,perfil,forca,"
            "acao,entidade,nome,caminho,detalhe) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    r.get("timestamp", ""), r.get("data", ""), r.get("hora", ""),
                    r.get("usuario", ""), r.get("perfil", ""), r.get("forca", 0),
                    r.get("acao", ""), r.get("entidade", ""), r.get("nome", ""),
                    r.get("caminho", ""), r.get("detalhe", ""),
                )
                for r in rows
            ],
        )
        conn.commit()
        print(f"[db] migrado audit_log ({len(rows)} entradas)")
    except Exception as e:
        print(f"[db] migração audit_log: {e}")


# ── Inserção (usada na migração) ──────────────────────────────────────────────

def _insert_cliente(conn, c: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO clientes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            c.get("cpf", ""), c.get("tipo", "PF"), c.get("nome", ""),
            c.get("telefone", ""),
            c.get("end_log", ""), c.get("end_num", ""), c.get("end_comp", ""),
            c.get("end_bairro", ""), c.get("end_cidade", ""), c.get("end_estado", ""),
            c.get("end_cep", ""), c.get("end_maps", ""),
            1 if c.get("obra_mesmo") else 0,
            c.get("obra_log", ""), c.get("obra_num", ""), c.get("obra_comp", ""),
            c.get("obra_bairro", ""), c.get("obra_cidade", ""), c.get("obra_estado", ""),
            c.get("obra_cep", ""), c.get("obra_maps", ""),
            c.get("data", ""),
        ),
    )


def _insert_tecnico(conn, t: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO tecnicos VALUES(?,?,?,?,?,?,?,?)",
        (
            t.get("id") or str(uuid.uuid4()),
            t.get("cpf", ""), t.get("nome", ""), t.get("cft", ""),
            t.get("telefone", ""), t.get("email", ""),
            t.get("endereco", ""), t.get("data", ""),
        ),
    )


def _insert_obra(conn, o: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO obras VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            o.get("id") or str(uuid.uuid4()),
            o.get("cliente_nome", ""), o.get("cliente_cpf", ""),
            o.get("obra_log", ""), o.get("obra_num", ""), o.get("obra_bairro", ""),
            o.get("obra_cidade", ""), o.get("obra_estado", ""),
            o.get("status", "Planejamento"), o.get("descricao", ""),
            o.get("data_inicio", ""), o.get("data_fim", ""),
            o.get("data_criacao", ""), o.get("data_atualizacao", ""),
        ),
    )


def _insert_ponto(conn, r: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO ponto VALUES(?,?,?,?,?,?,?)",
        (
            r.get("id") or str(uuid.uuid4()),
            r.get("data", ""), r.get("hora", ""),
            r.get("tipo", ""), r.get("usuario", ""), r.get("obra", ""),
            r.get("modificador", ""),
        ),
    )


def _insert_usuario(conn, u: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO usuarios VALUES(?,?,?,?,?,?,?,?)",
        (
            u.get("id") or str(uuid.uuid4()),
            u.get("nome", ""), u.get("email", ""),
            u.get("telefone", ""), u.get("cargo", ""),
            u.get("senha_hash", ""), u.get("perfil", "FUNCIONÁRIO"),
            1 if u.get("admin") else 0,
        ),
    )
