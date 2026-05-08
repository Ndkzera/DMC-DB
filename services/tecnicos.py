"""CRUD de técnicos — persistência em JSON."""

import json
from datetime import datetime

from config import TECNICOS_FILE
from services.log import log_action


def load_tecnicos() -> list:
    try:
        return json.loads(TECNICOS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_tecnicos(tecnicos: list) -> None:
    TECNICOS_FILE.write_text(
        json.dumps(tecnicos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_tecnico(tecnico: dict, usuario: str = "", perfil: str = "") -> None:
    tecnicos = load_tecnicos()
    tecnicos.append(tecnico)
    save_tecnicos(tecnicos)
    log_action(usuario, perfil, "criar", "tecnico", tecnico.get("nome", ""))


def update_tecnico(original_cpf: str, updated: dict,
                   usuario: str = "", perfil: str = "") -> None:
    tecnicos = load_tecnicos()
    for i, t in enumerate(tecnicos):
        if t.get("cpf") == original_cpf:
            tecnicos[i] = updated
            save_tecnicos(tecnicos)
            log_action(usuario, perfil, "editar", "tecnico", updated.get("nome", ""))
            return
    tecnicos.append(updated)
    save_tecnicos(tecnicos)
    log_action(usuario, perfil, "criar", "tecnico", updated.get("nome", ""))


def delete_tecnico(cpf: str, nome: str = "", usuario: str = "", perfil: str = "") -> None:
    tecnicos = [t for t in load_tecnicos() if t.get("cpf") != cpf]
    save_tecnicos(tecnicos)
    log_action(usuario, perfil, "excluir", "tecnico", nome or cpf)
