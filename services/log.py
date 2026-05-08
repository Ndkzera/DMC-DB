"""Registro centralizado de ações dos usuários (auditoria)."""

import json
from datetime import datetime

from config import CONFIG_DIR

LOG_FILE = CONFIG_DIR / "audit_log.json"
_MAX = 5000

# Hierarquia de perfis (maior = mais forte)
_FORCA = {
    "DESENVOLVEDOR":           5,
    "ADMINISTRADOR":           4,
    "FUNCIONÁRIO PRIORITÁRIO": 3,
    "FUNCIONÁRIO":             2,
    "FUNCIONÁRIO CAMPO":       1,
}

ACOES = {
    "criar":    ("add_circle",       "#4ADE80"),
    "editar":   ("edit",             "#FBBF24"),
    "excluir":  ("delete_forever",   "#F87171"),
    "renomear": ("drive_file_rename_outline", "#60A5FA"),
    "upload":   ("cloud_upload",     "#A78BFA"),
    "pasta":    ("create_new_folder","#34D399"),
}

ENTIDADES = {
    "cliente":  "person",
    "tecnico":  "engineering",
    "obra":     "construction",
    "arquivo":  "insert_drive_file",
    "pasta":    "folder",
    "ponto":    "fingerprint",
}


def _load() -> list:
    try:
        return json.loads(LOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def log_action(
    usuario: str,
    perfil: str,
    acao: str,      # "criar" | "editar" | "excluir" | "renomear" | "upload" | "pasta"
    entidade: str,  # "cliente" | "tecnico" | "obra" | "arquivo" | "pasta" | "ponto"
    nome: str,
    caminho: str = "",
    detalhe: str = "",
) -> None:
    now = datetime.now()
    entry = {
        "timestamp": now.isoformat(timespec="seconds"),
        "data":      now.strftime("%d/%m/%Y"),
        "hora":      now.strftime("%H:%M:%S"),
        "usuario":   usuario or "—",
        "perfil":    perfil  or "—",
        "forca":     _FORCA.get(perfil, 0),
        "acao":      acao,
        "entidade":  entidade,
        "nome":      nome,
        "caminho":   caminho,
        "detalhe":   detalhe,
    }
    try:
        entries = _load()
        entries.append(entry)
        LOG_FILE.write_text(
            json.dumps(entries[-_MAX:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[log] {entry['data']} {entry['hora']} | {perfil} | {acao} {entidade}: {nome}")
    except Exception as e:
        print(f"[log] erro ao registrar: {e}")


def load_logs(limit: int = 500, perfil_minimo: str = "") -> list:
    """Retorna os últimos registros em ordem decrescente.
    Se perfil_minimo fornecido, filtra só ações de usuários com força >= perfil_minimo."""
    entries = _load()
    if perfil_minimo:
        forca_min = _FORCA.get(perfil_minimo, 0)
        entries = [e for e in entries if e.get("forca", 0) >= forca_min]
    return list(reversed(entries[-limit:]))
