"""
DMC Topografia — Servidor de Arquivos v3.0
Nilton Jr · NDKZera

Ponto de entrada da aplicação. Execute:
    python app.py

Variáveis de ambiente opcionais:
    DMC_ROOT      — pasta raiz dos arquivos
    DMC_CONFIG    — pasta de configurações
    DMC_TRASH     — pasta de arquivos deletados
    DMC_PORT      — porta HTTP (padrão: 8080)
    DMC_BASE_URL  — URL pública para links de compartilhamento
"""

import re as _re

import httpx
from fastapi import File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from nicegui import app, ui

from config import BASE_URL, FOTOS_PONTO_DIR, PORT, ROOT_DIR, TRASH_DIR
from services.files import safe, san

# Servir arquivos estáticos
app.add_static_files("/files", str(ROOT_DIR))
app.add_static_files("/fotos_ponto", str(FOTOS_PONTO_DIR))

# ── Rotas FastAPI ────────────────────────────────────────────────────

@app.get("/info")
async def info_endpoint():
    return JSONResponse({"base_url": BASE_URL, "root_dir": str(ROOT_DIR)})


@app.post("/upload")
async def upload_endpoint(file: UploadFile = File(...), path: str = Form("")):
    """Upload via XHR (drag-drop do painel lateral)."""
    current_path = ROOT_DIR
    if path:
        candidate = Path(path)
        if candidate.is_dir() and safe(candidate):
            current_path = candidate

    fname = san(file.filename or "arquivo")
    dest  = current_path / fname
    if not safe(dest):
        return JSONResponse({"error": "caminho inválido"}, status_code=400)

    if dest.exists():
        stem, suf = dest.stem, dest.suffix
        i = 1
        while dest.exists():
            dest = current_path / f"{stem}_{i}{suf}"
            i += 1

    try:
        content = await file.read()
        dest.write_bytes(content)
        return JSONResponse({"ok": True, "name": dest.name})
    except OSError as ex:
        return JSONResponse({"error": str(ex)}, status_code=500)


@app.post("/upload-modelo")
async def upload_modelo_endpoint(file: UploadFile = File(...)):
    """Upload de modelo .docx para MODELOS_DIR."""
    from config import MODELOS_DIR
    fname = san(file.filename or "modelo.docx")
    if not fname.lower().endswith(".docx"):
        return JSONResponse({"error": "apenas .docx aceito"}, status_code=400)
    dest = MODELOS_DIR / fname
    try:
        content = await file.read()
        dest.write_bytes(content)
        return JSONResponse({"ok": True, "name": dest.name})
    except OSError as ex:
        return JSONResponse({"error": str(ex)}, status_code=500)


@app.get("/api/trash/{filename}")
async def trash_download(filename: str):
    """Serve arquivo da lixeira com nome original (sem timestamp)."""
    p = TRASH_DIR / filename
    if not p.exists() or not p.is_file():
        return JSONResponse({"error": "not found"}, status_code=404)
    try:
        p.resolve().relative_to(TRASH_DIR.resolve())
    except ValueError:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    _TS_RE = _re.compile(r"__\d{8}_\d{6}$")
    base = p.stem if p.suffix else p.name
    orig = _TS_RE.sub("", base) + p.suffix
    return FileResponse(str(p), filename=orig, media_type="application/octet-stream")


@app.get("/api/cep/{cep}")
async def cep_endpoint(cep: str):
    cep = "".join(c for c in cep if c.isdigit())[:8]
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(f"https://viacep.com.br/ws/{cep}/json/")
            return JSONResponse(r.json())
    except Exception as ex:
        return JSONResponse({"erro": True, "detail": str(ex)}, status_code=502)


@app.get("/api/cnpj/{cnpj}")
async def cnpj_endpoint(cnpj: str):
    cnpj = "".join(c for c in cnpj if c.isdigit())[:14]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"https://www.receitaws.com.br/v1/cnpj/{cnpj}",
                headers={"Accept": "application/json"},
            )
            return JSONResponse(r.json())
    except Exception as ex:
        return JSONResponse({"status": "ERROR", "detail": str(ex)}, status_code=502)


# ── Usuário padrão ───────────────────────────────────────────────────
from services.auth import ensure_default_user
ensure_default_user()

# ── Registra páginas ─────────────────────────────────────────────────
import pages.login     # noqa: F401, E402  (registra @ui.page("/login"))
import pages.contas    # noqa: F401, E402  (registra @ui.page("/contas"))
import pages.main      # noqa: F401, E402  (registra @ui.page("/"))
import pages.cadastro  # noqa: F401, E402  (registra @ui.page("/cliente/cadastrar"))
import pages.campo     # noqa: F401, E402  (registra @ui.page("/campo"))
import pages.mobile    # noqa: F401, E402  (registra @ui.page("/mobile"))
import pages.acesso    # noqa: F401, E402  (registra @ui.page("/acesso"))
import pages.lixeira   # noqa: F401, E402  (registra @ui.page("/lixeira"))

# ── Inicialização ────────────────────────────────────────────────────
if __name__ == "__main__":
    ui.run(
        title="DMC Topografia · Drive",
        dark=True,
        port=PORT,
        reload=False,
        storage_secret="dmc-topo-2025-xk9mN3",
        favicon="🗺️",
    )
