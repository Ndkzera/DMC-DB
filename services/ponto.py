"""CRUD de registros de ponto — persistência em JSON."""

import json
from datetime import datetime
from config import PONTO_FILE


def load_ponto() -> list:
    try:
        return json.loads(PONTO_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_ponto(registros: list) -> None:
    PONTO_FILE.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_registro(registro: dict) -> None:
    registros = load_ponto()
    registros.append(registro)
    save_ponto(registros)


def delete_registro(reg_id: str) -> None:
    registros = [r for r in load_ponto() if r.get("id") != reg_id]
    save_ponto(registros)
