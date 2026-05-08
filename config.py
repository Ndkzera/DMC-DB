"""
Configuração central — sobrescreva via variáveis de ambiente.

  DMC_ROOT   — pasta raiz dos arquivos
  DMC_CONFIG — pasta de configurações (clientes.json, etc.)
  DMC_TRASH  — pasta de arquivos deletados
  DMC_PORT   — porta HTTP (padrão 8080)
  DMC_BASE_URL — URL pública para links de compartilhamento
"""

import os
import socket
from pathlib import Path

ROOT_DIR   = Path(os.getenv("DMC_ROOT",   "/media/niltonjr/Novo volume/BACKUP DMC/Arquivos")).resolve()
CONFIG_DIR = Path(os.getenv("DMC_CONFIG", "/media/niltonjr/Novo volume/BACKUP DMC/Arquivos de configuração")).resolve()
TRASH_DIR  = Path(os.getenv("DMC_TRASH",  "/media/niltonjr/Novo volume/BACKUP DMC/Arquivos deletados")).resolve()

for _d in (ROOT_DIR, CONFIG_DIR, TRASH_DIR):
    _d.mkdir(parents=True, exist_ok=True)

CLIENTES_FILE = CONFIG_DIR / "clientes.json"
if not CLIENTES_FILE.exists():
    CLIENTES_FILE.write_text("[]", encoding="utf-8")

TECNICOS_FILE = CONFIG_DIR / "tecnicos.json"
if not TECNICOS_FILE.exists():
    TECNICOS_FILE.write_text("[]", encoding="utf-8")

OBRAS_FILE = CONFIG_DIR / "obras.json"
if not OBRAS_FILE.exists():
    OBRAS_FILE.write_text("[]", encoding="utf-8")

PONTO_FILE = CONFIG_DIR / "ponto.json"
if not PONTO_FILE.exists():
    PONTO_FILE.write_text("[]", encoding="utf-8")

MODELOS_DIR = Path(__file__).parent / "modelos"
MODELOS_DIR.mkdir(exist_ok=True)

FOTOS_PONTO_DIR = CONFIG_DIR / "fotos_ponto"
FOTOS_PONTO_DIR.mkdir(exist_ok=True)

CLIENTES_DIR = ROOT_DIR / "#CLIENTES"
CLIENTES_DIR.mkdir(exist_ok=True)

HIDDEN_NAMES  = {".DS_Store", "Thumbs.db", "desktop.ini", "events.json", "plot.log"}
HIDDEN_EXT    = {".log", ".tmp"}
HIDDEN_PREFIX = (".", "__")

PORT = int(os.getenv("DMC_PORT", "8080"))


def get_base_url() -> str:
    env = os.environ.get("DMC_BASE_URL", "").strip().rstrip("/")
    if env:
        return env
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:{PORT}"
    except Exception:
        return f"http://localhost:{PORT}"


BASE_URL = get_base_url()
