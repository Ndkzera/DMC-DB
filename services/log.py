"""Registro centralizado de ações dos usuários (auditoria) — SQLite."""

from datetime import datetime
from services.database import get_conn

_MAX = 5000

_FORCA = {
    "DESENVOLVEDOR":           5,
    "ADMINISTRADOR":           4,
    "FUNCIONÁRIO PRIORITÁRIO": 3,
    "FUNCIONÁRIO":             2,
    "FUNCIONÁRIO CAMPO":       1,
}

ACOES = {
    "criar":    ("add_circle",                   "#4ADE80"),
    "editar":   ("edit",                          "#FBBF24"),
    "excluir":  ("delete_forever",                "#F87171"),
    "renomear": ("drive_file_rename_outline",     "#60A5FA"),
    "upload":   ("cloud_upload",                  "#A78BFA"),
    "pasta":    ("create_new_folder",             "#34D399"),
}

ENTIDADES = {
    "cliente":  "person",
    "tecnico":  "engineering",
    "obra":     "construction",
    "arquivo":  "insert_drive_file",
    "pasta":    "folder",
    "ponto":    "fingerprint",
}


def log_action(
    usuario: str,
    perfil: str,
    acao: str,
    entidade: str,
    nome: str,
    caminho: str = "",
    detalhe: str = "",
) -> None:
    now = datetime.now()
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO audit_log(timestamp,data,hora,usuario,perfil,forca,"
            "acao,entidade,nome,caminho,detalhe) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                now.isoformat(timespec="seconds"),
                now.strftime("%d/%m/%Y"),
                now.strftime("%H:%M:%S"),
                usuario or "—",
                perfil  or "—",
                _FORCA.get(perfil, 0),
                acao, entidade, nome, caminho, detalhe,
            ),
        )
        # Mantém apenas os últimos _MAX registros
        conn.execute(
            "DELETE FROM audit_log WHERE id NOT IN "
            "(SELECT id FROM audit_log ORDER BY id DESC LIMIT ?)",
            (_MAX,),
        )
        conn.commit()
        print(f"[log] {now.strftime('%d/%m/%Y')} {now.strftime('%H:%M:%S')} "
              f"| {perfil} | {acao} {entidade}: {nome}")
    except Exception as e:
        print(f"[log] erro ao registrar: {e}")
    finally:
        conn.close()


def load_logs(limit: int = 500, perfil_minimo: str = "") -> list:
    conn = get_conn()
    try:
        if perfil_minimo:
            forca_min = _FORCA.get(perfil_minimo, 0)
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE forca>=? ORDER BY id DESC LIMIT ?",
                (forca_min, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
