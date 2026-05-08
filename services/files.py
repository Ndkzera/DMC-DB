"""Operações de sistema de arquivos — listagem, validação, URL e exclusão."""

import json
import shutil
import urllib.parse
from datetime import datetime
from pathlib import Path

from config import HIDDEN_EXT, HIDDEN_NAMES, HIDDEN_PREFIX, ROOT_DIR, TRASH_DIR

_TRASH_META = TRASH_DIR / ".meta"

_FILE_TYPES: dict[str, tuple[str, str, str, str]] = {
    ".dwg":  ("architecture",   "#FBBF24", "DWG",  "cad"),
    ".dxf":  ("architecture",   "#FBBF24", "DXF",  "cad"),
    ".dgn":  ("architecture",   "#FBBF24", "DGN",  "cad"),
    ".pdf":  ("picture_as_pdf", "#F87171", "PDF",  "pdf"),
    ".doc":  ("description",    "#60A5FA", "DOC",  "office"),
    ".docx": ("description",    "#60A5FA", "DOCX", "office"),
    ".xls":  ("table_chart",    "#34D399", "XLS",  "office"),
    ".xlsx": ("table_chart",    "#34D399", "XLSX", "office"),
    ".ppt":  ("slideshow",      "#FB923C", "PPT",  "office"),
    ".pptx": ("slideshow",      "#FB923C", "PPTX", "office"),
    ".png":  ("image",          "#C4B5FD", "PNG",  "image"),
    ".jpg":  ("image",          "#C4B5FD", "JPG",  "image"),
    ".jpeg": ("image",          "#C4B5FD", "JPEG", "image"),
    ".webp": ("image",          "#C4B5FD", "WEBP", "image"),
    ".tif":  ("image",          "#C4B5FD", "TIF",  "image"),
    ".tiff": ("image",          "#C4B5FD", "TIFF", "image"),
    ".gif":  ("gif",            "#F472B6", "GIF",  "image"),
    ".svg":  ("image",          "#C4B5FD", "SVG",  "image"),
    ".zip":  ("folder_zip",     "#FDE68A", "ZIP",  "archive"),
    ".rar":  ("folder_zip",     "#FDE68A", "RAR",  "archive"),
    ".7z":   ("folder_zip",     "#FDE68A", "7Z",   "archive"),
    ".shp":  ("map",            "#34D399", "SHP",  "gis"),
    ".kml":  ("map",            "#34D399", "KML",  "gis"),
    ".kmz":  ("map",            "#34D399", "KMZ",  "gis"),
    ".gpx":  ("map",            "#34D399", "GPX",  "gis"),
    ".txt":  ("article",        "#94A3B8", "TXT",  "text"),
    ".csv":  ("grid_on",        "#94A3B8", "CSV",  "text"),
}


def fmt_size(b: float) -> str:
    for u in ["B", "KB", "MB", "GB"]:
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


def safe(target: Path) -> bool:
    try:
        target.resolve().relative_to(ROOT_DIR.resolve())
        return True
    except ValueError:
        return False


def san(name: str) -> str:
    return "".join(c for c in name if c not in set('/\\:*?"<>|')).strip()[:200]


def cat(ext: str) -> dict:
    ic, co, lb, gr = _FILE_TYPES.get(
        ext.lower(),
        ("insert_drive_file", "#64748B", ext.upper().lstrip(".") or "FILE", "other"),
    )
    return {"icon": ic, "color": co, "label": lb, "group": gr}


def vtype(ext: str) -> str | None:
    e = ext.lower()
    if e == ".pdf":
        return "pdf"
    if e in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".tif", ".tiff"}:
        return "image"
    if e in {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}:
        return "office"
    return None


def list_dir(path: Path, search: str = "") -> tuple[list, list]:
    folders, files = [], []
    search = search.lower().strip()
    try:
        it = path.rglob("*") if search else path.iterdir()
        for item in it:
            if (
                item.name in HIDDEN_NAMES
                or any(item.name.startswith(p) for p in HIDDEN_PREFIX)
                or item.suffix.lower() in HIDDEN_EXT
            ):
                continue
            if search and search not in item.name.lower():
                continue
            try:
                st = item.stat()
                entry = {
                    "name": item.name,
                    "path": item,
                    "mtime_str": datetime.fromtimestamp(st.st_mtime).strftime("%d/%m/%Y"),
                }
                if item.is_dir():
                    try:
                        cnt = sum(1 for _ in item.iterdir() if not _.name.startswith("."))
                    except OSError:
                        cnt = 0
                    entry["count"] = cnt
                    folders.append(entry)
                else:
                    entry["size"] = fmt_size(st.st_size)
                    entry["size_bytes"] = st.st_size
                    entry["ext"] = item.suffix.lower()
                    entry["cat"] = cat(item.suffix.lower())
                    files.append(entry)
            except OSError:
                continue
    except OSError as ex:
        print(f"[ERRO] {ex}")
    folders.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())
    return folders, files


def file_url(path: Path) -> str:
    return "/files/" + urllib.parse.quote(
        str(path.relative_to(ROOT_DIR)).replace("\\", "/")
    )


def breadcrumbs(path: Path) -> list[tuple[str, Path]]:
    parts, p = [], path
    while True:
        parts.append((p.name if p != ROOT_DIR else "Raiz", p))
        if p == ROOT_DIR:
            break
        p = p.parent
    return list(reversed(parts))


def delete_item(path: Path, deleted_by: str = "", perfil: str = "") -> bool:
    """Move item para TRASH_DIR e grava metadados. Retorna True em sucesso."""
    from services.log import log_action
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = TRASH_DIR / (
            f"{path.name}__{ts}" if path.is_dir()
            else f"{path.stem}__{ts}{path.suffix}"
        )
        shutil.move(str(path), str(dest))

        try:
            _TRASH_META.mkdir(parents=True, exist_ok=True)
            try:
                origin = str(path.parent.relative_to(ROOT_DIR))
            except ValueError:
                origin = str(path.parent)
            meta = {
                "original_name": path.name,
                "origin":        origin,
                "deleted_by":    deleted_by or "—",
                "deleted_at":    datetime.now().isoformat(timespec="seconds"),
            }
            (_TRASH_META / f"{dest.name}.json").write_text(
                json.dumps(meta, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass  # metadados são opcionais, não falhar por isso

        entidade = "pasta" if path.is_dir() else "arquivo"
        log_action(deleted_by, perfil, "excluir", entidade, path.name, origin)
        return True
    except Exception as ex:
        from nicegui import ui
        ui.notify(f"Erro ao deletar '{path.name}': {ex}", type="negative")
        return False


def read_trash_meta(dest_name: str) -> dict:
    """Lê metadados de um item da lixeira. Retorna dict vazio se não houver."""
    try:
        f = _TRASH_META / f"{dest_name}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}
