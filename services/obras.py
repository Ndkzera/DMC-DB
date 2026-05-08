"""CRUD de obras — persistência em JSON."""

import json
from datetime import datetime
from config import OBRAS_FILE
from services.log import log_action


def load_obras() -> list:
    try:
        return json.loads(OBRAS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_obras(obras: list) -> None:
    OBRAS_FILE.write_text(
        json.dumps(obras, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_obra(obra: dict, usuario: str = "", perfil: str = "") -> None:
    obras = load_obras()
    obras.append(obra)
    save_obras(obras)
    log_action(usuario, perfil, "criar", "obra",
               obra.get("cliente_nome", ""), obra.get("obra_log", ""))


def update_obra_status(obra_id: str, status: str,
                       usuario: str = "", perfil: str = "") -> None:
    obras = load_obras()
    for o in obras:
        if o.get("id") == obra_id:
            o["status"] = status
            o["data_atualizacao"] = datetime.now().strftime("%d/%m/%Y %H:%M")
            save_obras(obras)
            log_action(usuario, perfil, "editar", "obra",
                       o.get("cliente_nome", ""), o.get("obra_log", ""),
                       f"Status → {status}")
            return


def delete_obra(obra_id: str, nome: str = "", usuario: str = "", perfil: str = "") -> None:
    obras = load_obras()
    obra_nome = nome
    if not obra_nome:
        for o in obras:
            if o.get("id") == obra_id:
                obra_nome = o.get("cliente_nome", obra_id)
                break
    obras = [o for o in obras if o.get("id") != obra_id]
    save_obras(obras)
    log_action(usuario, perfil, "excluir", "obra", obra_nome)
