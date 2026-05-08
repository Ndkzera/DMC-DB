"""Página de Lixeira — /lixeira"""

import re
import shutil
from pathlib import Path

from nicegui import app as _app, ui

from config import ROOT_DIR, TRASH_DIR
from services.auth import check_login, current_user_label, current_user_perfil, is_authenticated
from services.acesso import has_access
from services.files import cat, fmt_size, read_trash_meta
from ui.styles import BOOTSTRAP_CDN, CSS, UTILS_JS

_TS_RE    = re.compile(r"__\d{8}_\d{6}$")
_TS_PARSE = re.compile(r"__(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})")

_PAGE_CSS = """
<style>
html, body, .nicegui-content,
.q-layout, .q-page-container, .q-page {
  margin: 0 !important; padding: 0 !important;
  width: 100% !important; max-width: 100% !important;
  box-sizing: border-box !important;
}

.lx-page {
  width: 100%; min-height: 100vh;
  background: var(--dmc-bg);
  display: flex; flex-direction: column;
}

/* ── topbar ── */
.lx-topbar {
  position: sticky; top: 0; z-index: 100;
  width: 100%; box-sizing: border-box;
  height: 60px; flex-shrink: 0;
  background: var(--dmc-bg2);
  border-bottom: 1px solid var(--dmc-b1);
  backdrop-filter: blur(16px);
  display: flex; align-items: center;
  padding: 0 28px; gap: 12px;
}
.lx-title {
  display: flex; align-items: center; gap: 8px;
  font: 700 15px var(--dmc-fd); color: var(--dmc-text);
  white-space: nowrap;
}
.lx-title .ico { font-size: 20px !important; color: #F87171; }
.lx-sep { width: 1px; height: 28px; background: var(--dmc-b1); flex-shrink: 0; }
.lx-spacer { flex: 1; }
.lx-stats {
  font: 12px var(--dmc-mono); color: var(--dmc-muted2);
  background: rgba(255,255,255,.04); border: 1px solid var(--dmc-b1);
  border-radius: 6px; padding: 3px 10px; white-space: nowrap;
}

/* ── view toggle ── */
.lx-view-btn {
  width: 32px; height: 32px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; border: 1px solid var(--dmc-b1);
  background: transparent; transition: background .12s, border-color .12s;
}
.lx-view-btn:hover { background: rgba(255,255,255,.06); }
.lx-view-btn.active {
  background: rgba(74,222,128,.12); border-color: rgba(74,222,128,.35);
}
.lx-view-btn .material-icons { font-size: 17px !important; color: var(--dmc-muted2); }
.lx-view-btn.active .material-icons { color: var(--dmc-green); }

/* ── body — full width ── */
.lx-body {
  flex: 1;
  width: 100%;
  box-sizing: border-box;
  padding: 28px 32px;
}

/* ── card / tabela ── */
.lx-card {
  background: var(--dmc-bg2);
  border: 1px solid var(--dmc-b1);
  border-radius: 14px;
  overflow-x: auto;
  overflow-y: hidden;
}
.lx-table {
  border-collapse: collapse; table-layout: fixed;
  min-width: 900px;
}
.lx-table thead tr { border-bottom: 1px solid var(--dmc-b1); }
.lx-table thead th {
  padding: 10px 14px;
  font: 600 10px var(--dmc-mono); color: var(--dmc-muted2);
  text-transform: uppercase; letter-spacing: .06em; white-space: nowrap;
  overflow: hidden;
}
.lx-table tbody tr {
  border-bottom: 1px solid var(--dmc-b1); transition: background .1s;
}
.lx-table tbody tr:last-child { border-bottom: none; }
.lx-table tbody tr:hover { background: rgba(255,255,255,.03); }
.lx-table tbody td { padding: 9px 14px; vertical-align: middle; overflow: hidden; }
.lx-name {
  font: 500 13px var(--dmc-fm); color: var(--dmc-text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.lx-path {
  font: 11px var(--dmc-mono); color: #60A5FA;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.lx-user {
  font: 12px var(--dmc-mono); color: var(--dmc-muted);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.lx-meta  { font: 12px var(--dmc-mono); color: var(--dmc-muted); white-space: nowrap; }
.lx-meta2 { font: 11px var(--dmc-mono); color: var(--dmc-muted2); white-space: nowrap; }

/* ── grid ── */
.lx-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 14px;
}
.lx-file-card {
  background: var(--dmc-bg2); border: 1px solid var(--dmc-b1);
  border-radius: 12px; padding: 14px 12px 10px;
  display: flex; flex-direction: column; gap: 5px;
  transition: border-color .12s; overflow: hidden;
}
.lx-file-card:hover { border-color: var(--dmc-b2); }
.lx-card-name {
  font: 500 11px/1.4 var(--dmc-fm); color: var(--dmc-text);
  display: -webkit-box; -webkit-line-clamp: 2;
  -webkit-box-orient: vertical; overflow: hidden; flex: 1;
}
.lx-card-meta  { font: 10px var(--dmc-mono); color: var(--dmc-muted2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lx-card-path  { font: 10px var(--dmc-mono); color: #60A5FA;   white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lx-card-user  { font: 10px var(--dmc-mono); color: var(--dmc-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lx-card-actions {
  display: flex; gap: 4px;
  padding-top: 8px; border-top: 1px solid var(--dmc-b1); margin-top: 4px;
}

/* ── vazio ── */
.lx-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 100px 20px; gap: 14px; color: var(--dmc-muted2);
}

/* ── dialog ── */
.lx-dlg-card {
  width: min(440px, 95vw); padding: 0;
  background: var(--dmc-bg2) !important;
  border: 1px solid var(--dmc-b2) !important;
  border-radius: 14px !important;
}
.lx-dlg-title { font: 600 14px var(--dmc-fd); color: var(--dmc-text); line-height: 1.4; word-break: break-word; }
.lx-dlg-warn  { font: 11px var(--dmc-fm); color: #F87171; margin-top: 5px; }

@media (max-width: 900px) {
  .lx-body { padding: 16px 14px; }
  .lx-topbar { padding: 0 14px; gap: 8px; }
  .hide-sm { display: none !important; }
}
</style>
"""


def _orig_name(p: Path) -> str:
    base = p.stem if p.suffix else p.name
    return _TS_RE.sub("", base) + p.suffix


def _del_date(p: Path) -> str:
    m = _TS_PARSE.search(p.name)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)} {m.group(4)}:{m.group(5)}"
    return "—"


def _items() -> list[Path]:
    try:
        return sorted(
            (p for p in TRASH_DIR.iterdir() if p.name != ".meta"),
            key=lambda p: p.stat().st_mtime, reverse=True
        )
    except OSError:
        return []


def _restore_path(orig: str) -> Path:
    dest = ROOT_DIR / orig
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    i = 1
    while dest.exists():
        dest = ROOT_DIR / f"{stem}_{i}{suffix}"
        i += 1
    return dest


@ui.page("/lixeira")
def lixeira_page():
    if not is_authenticated():
        ui.navigate.to("/login")
        return
    if not has_access(current_user_perfil() or "", "arq_lixeira"):
        ui.navigate.to("/")
        return

    ui.dark_mode().enable()
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(UTILS_JS)
    ui.add_head_html(_PAGE_CSS)

    view_state = {"v": "list"}
    dlg_state  = {"on_confirm": None}

    with ui.element("div").classes("lx-page").style("width:100%"):

        # ── Dialog de senha ── criado UMA VEZ ──────────────────────
        with ui.dialog().props("persistent") as pw_dlg:
            with ui.card().style(
                "width:min(420px,94vw);padding:0;gap:0;"
                "background:var(--dmc-bg2)!important;"
                "border:1px solid rgba(248,113,113,.35)!important;"
                "border-radius:16px!important;"
                "box-shadow:0 24px 60px rgba(0,0,0,.55)!important;"
                "overflow:hidden;"
            ):
                # cabeçalho
                with ui.element("div").style(
                    "padding:22px 24px 16px;"
                    "border-bottom:1px solid var(--dmc-b1);"
                ):
                    dlg_title = ui.html("")

                # corpo
                with ui.element("div").style(
                    "padding:20px 24px 8px;"
                    "display:flex;flex-direction:column;gap:4px;"
                ):
                    ui.html("""
                        <div style="position:relative">
                            <input
                                type="password"
                                id="lx-pw"
                                placeholder="Digite sua senha"
                                autocomplete="current-password"
                                onkeydown="if(event.key==='Enter')document.getElementById('lx-cf').click()"
                                onfocus="this.style.borderColor='rgba(248,113,113,.75)';this.style.boxShadow='0 0 0 3px rgba(248,113,113,.15)'"
                                onblur="this.style.borderColor='rgba(248,113,113,.3)';this.style.boxShadow='none'"
                                style="
                                    width:100%;height:46px;
                                    padding:0 50px 0 16px;
                                    box-sizing:border-box;
                                    background:rgba(248,113,113,.06);
                                    border:1.5px solid rgba(248,113,113,.3);
                                    border-radius:10px;
                                    color:var(--dmc-text);
                                    font:14px var(--dmc-fm);
                                    outline:none;
                                    transition:border-color .15s,box-shadow .15s;
                                "
                            >
                            <button
                                type="button"
                                id="lx-eye"
                                onclick="(function(){
                                    var i=document.getElementById('lx-pw');
                                    var s=document.getElementById('lx-eye-ico');
                                    if(i.type==='password'){i.type='text';s.textContent='visibility';}
                                    else{i.type='password';s.textContent='visibility_off';}
                                })()"
                                style="
                                    position:absolute;right:0;top:0;
                                    width:46px;height:46px;
                                    display:flex;align-items:center;justify-content:center;
                                    background:none;border:none;cursor:pointer;
                                    color:var(--dmc-muted2);
                                    border-radius:0 10px 10px 0;
                                    transition:color .12s;
                                "
                                onmouseover="this.style.color='var(--dmc-text)'"
                                onmouseout="this.style.color='var(--dmc-muted2)'"
                            >
                                <span id="lx-eye-ico" class="material-icons" style="font-size:20px;pointer-events:none">visibility_off</span>
                            </button>
                        </div>
                    """)
                    err_lbl = ui.html("").style(
                        "font:11px var(--dmc-fm);color:#F87171;min-height:18px;padding:2px 2px 0"
                    )

                # rodapé
                with ui.element("div").style(
                    "padding:16px 24px 22px;"
                    "display:flex;gap:8px;justify-content:flex-end;"
                ):
                    cx_btn = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                    with cx_btn:
                        ui.html("<span>Cancelar</span>")
                    cf_btn = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
                    cf_btn.props('id="lx-cf"')
                    with cf_btn:
                        ui.html(
                            '<span class="material-icons" style="font-size:14px">delete_forever</span>'
                            "<span>Confirmar exclusão</span>"
                        )

        def _pedir_senha(titulo: str, on_confirm) -> None:
            dlg_state["on_confirm"] = on_confirm
            dlg_title.set_content(
                f'<div style="font:600 15px var(--dmc-fd);color:var(--dmc-text);'
                f'line-height:1.45;word-break:break-word">{titulo}</div>'
                '<div style="font:12px var(--dmc-fm);color:#F87171;margin-top:7px">'
                'Esta ação é irreversível.</div>'
            )
            err_lbl.set_content("")
            pw_dlg.open()
            ui.run_javascript(
                "setTimeout(function(){"
                "  var f=document.getElementById('lx-pw');"
                "  if(f){f.value='';f.focus();}"
                "  var e=document.getElementById('lx-eye-ico');"
                "  if(e)e.textContent='visibility_off';"
                "  var i=document.getElementById('lx-pw');"
                "  if(i)i.type='password';"
                "},80)"
            )

        async def _do_confirm():
            pw_val = await ui.run_javascript(
                "document.getElementById('lx-pw')?.value ?? ''"
            )
            email = _app.storage.user.get("dmc_user_email", "")
            if not check_login(email, pw_val):
                err_lbl.set_content("Senha incorreta. Tente novamente.")
                ui.run_javascript(
                    "var f=document.getElementById('lx-pw');"
                    "if(f){f.value='';f.focus();}"
                )
                return
            pw_dlg.close()
            cb = dlg_state["on_confirm"]
            if cb:
                cb()

        cx_btn.on("click", pw_dlg.close)
        cf_btn.on("click", _do_confirm)

        # ── Topbar ───────────────────────────────────────────────────
        with ui.element("div").classes("lx-topbar"):
            with ui.element("div").classes("lx-title"):
                ui.html('<span class="material-icons ico">delete</span>')
                ui.html("<span>Lixeira</span>")
            ui.element("div").classes("lx-sep")
            stats_lbl = ui.html("")
            ui.element("div").classes("lx-spacer")

            view_btns: dict[str, ui.element] = {}
            with ui.element("div").style("display:flex;gap:4px"):
                for vv, ic in [("grid", "grid_view"), ("list", "view_list")]:
                    btn = ui.element("button").classes(
                        "lx-view-btn" + (" active" if vv == view_state["v"] else "")
                    )
                    with btn:
                        ui.html(f'<span class="material-icons">{ic}</span>')
                    view_btns[vv] = btn

            ui.element("div").classes("lx-sep")
            esvaziar_btn = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
            with esvaziar_btn:
                ui.html(
                    '<span class="material-icons" style="font-size:15px">delete_sweep</span>'
                    "<span>Esvaziar</span>"
                )
            ui.element("div").classes("lx-sep")
            back_btn = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
            with back_btn:
                ui.html('<span class="material-icons" style="font-size:16px">arrow_back</span>')
                ui.html("<span>Voltar</span>")
            back_btn.on("click", lambda: ui.navigate.to("/"))

        # ── Corpo ────────────────────────────────────────────────────
        with ui.element("div").classes("lx-body"):
            content = ui.element("div").style("width:100%")

        # ── Helpers ──────────────────────────────────────────────────

        def _item_info(p: Path):
            is_dir = p.is_dir()
            orig   = _orig_name(p)
            ddate  = _del_date(p)
            meta      = read_trash_meta(p.name)
            _raw      = meta.get("origin", "")
            origin    = "Raiz" if _raw in ("", ".", "/") else _raw
            _by       = meta.get("deleted_by", "") or ""
            # se o meta guardou o perfil (sem espaço, tudo maiúsculo) e não um nome real,
            # atualiza o arquivo e mostra o label do usuário logado
            _KNOWN_PERFIS = {"DESENVOLVEDOR", "ADMINISTRADOR", "FUNCIONÁRIO", "GERENTE"}
            if not _by or _by in _KNOWN_PERFIS:
                _by = current_user_label()
                try:
                    import json as _json
                    from config import TRASH_DIR as _TD
                    _mf = _TD / ".meta" / f"{p.name}.json"
                    _mdata = dict(meta)
                    _mdata["deleted_by"] = _by
                    _mf.parent.mkdir(parents=True, exist_ok=True)
                    _mf.write_text(_json.dumps(_mdata, ensure_ascii=False), encoding="utf-8")
                except Exception:
                    pass
            by_who = _by or "—"
            if is_dir:
                ic, co, lb = "folder", "#FBBF24", "PASTA"
                try:
                    sz_b = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                except OSError:
                    sz_b = 0
            else:
                ci = cat(p.suffix.lower())
                ic, co, lb = ci["icon"], ci["color"], ci["label"]
                try:
                    sz_b = p.stat().st_size
                except OSError:
                    sz_b = 0
            return is_dir, orig, ddate, ic, co, lb, sz_b, origin, by_who

        def _do_restore(path: Path):
            orig  = _orig_name(path)
            meta  = read_trash_meta(path.name)
            _raw  = meta.get("origin", "")
            # reconstrói pasta de origem; "" ou "." significa raiz
            if _raw and _raw not in (".", "/"):
                origin_dir = ROOT_DIR / _raw
                origin_dir.mkdir(parents=True, exist_ok=True)
            else:
                origin_dir = ROOT_DIR

            dest = origin_dir / orig
            if dest.exists():
                stem, suffix = Path(orig).stem, Path(orig).suffix
                i = 1
                while dest.exists():
                    dest = origin_dir / f"{stem}_{i}{suffix}"
                    i += 1

            try:
                shutil.move(str(path), str(dest))
                meta_f = TRASH_DIR / ".meta" / f"{path.name}.json"
                if meta_f.exists():
                    meta_f.unlink()
                folder_lbl = _raw if _raw and _raw not in (".", "/") else "Raiz"
                ui.notify(f"'{orig}' restaurado para '{folder_lbl}'.", type="positive")
            except Exception as ex:
                ui.notify(f"Erro ao restaurar: {ex}", type="negative")
            _render()

        def _do_delete(path: Path):
            def _confirm():
                try:
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
                    meta_f = TRASH_DIR / ".meta" / f"{path.name}.json"
                    if meta_f.exists():
                        meta_f.unlink()
                    ui.notify(f"'{_orig_name(path)}' excluído permanentemente.", type="positive")
                except Exception as ex:
                    ui.notify(f"Erro: {ex}", type="negative")
                _render()
            _pedir_senha(f'Excluir "{_orig_name(path)}" permanentemente?', _confirm)

        def _make_actions(p: Path, is_dir: bool, compact: bool = False):
            extra = " flex-fill" if compact else ""

            if not is_dir:
                # ícone-only para não ultrapassar a largura da coluna
                dl = ui.element("button").classes(f"dmc-btn dmc-btn-secondary dmc-btn-sm{extra}").style(
                    "padding:0 8px!important;min-width:32px"
                )
                with dl:
                    ui.html('<span class="material-icons" style="font-size:15px">get_app</span>')
                dl.on("click", lambda fn=p.name: ui.download(f"/api/trash/{fn}"))

            rs = ui.element("button").classes(f"dmc-btn dmc-btn-secondary dmc-btn-sm{extra}")
            with rs:
                ui.html('<span class="material-icons" style="font-size:14px">settings_backup_restore</span>')
                if not compact:
                    ui.html("<span>Restaurar</span>")
            rs.on("click", lambda path=p: _do_restore(path))

            dx = ui.element("button").classes(f"dmc-btn dmc-btn-danger dmc-btn-sm{extra}")
            with dx:
                ui.html('<span class="material-icons" style="font-size:14px">delete_forever</span>')
                if not compact:
                    ui.html("<span>Excluir</span>")
            dx.on("click", lambda path=p: _do_delete(path))

        # ── Render ───────────────────────────────────────────────────

        def _render():
            content.clear()
            items = _items()

            if items:
                total_b = 0
                for p in items:
                    try:
                        total_b += (
                            sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                            if p.is_dir() else p.stat().st_size
                        )
                    except OSError:
                        pass
                n = len(items)
                stats_lbl.set_content(
                    f'<span class="lx-stats">'
                    f'{n} {"item" if n == 1 else "itens"} · {fmt_size(total_b)}</span>'
                )
                esvaziar_btn.style("display:inline-flex")
            else:
                stats_lbl.set_content("")
                esvaziar_btn.style("display:none")

            with content:
                if not items:
                    with ui.element("div").classes("lx-card"):
                        with ui.element("div").classes("lx-empty"):
                            ui.html(
                                '<span class="material-icons" style="font-size:72px;opacity:.1">delete_outline</span>'
                                '<div style="font:13px var(--dmc-fm)">A lixeira está vazia</div>'
                            )
                    return

                if view_state["v"] == "list":
                    _render_list(items)
                else:
                    _render_grid(items)

        def _render_list(items):
            with ui.element("div").classes("lx-card"):
                with ui.element("table").classes("lx-table"):
                    with ui.element("thead"):
                        with ui.element("tr"):
                            for col, w in [
                                ("",            "40px"),
                                ("Nome",        "1550px"),
                                ("Tipo",        "72px"),
                                ("Tamanho",     "85px"),
                                ("Excluído em", "135px"),
                                ("Excluído por","130px"),
                                ("Pasta origem","200px"),
                                ("",            "195px"),
                            ]:
                                s = f"width:{w}" if w else ""
                                with ui.element("th").style(s):
                                    ui.html(col)
                    with ui.element("tbody"):
                        for p in items:
                            is_dir, orig, ddate, ic, co, lb, sz_b, origin, by_who = _item_info(p)
                            with ui.element("tr"):
                                with ui.element("td"):
                                    ui.html(
                                        f'<span class="material-icons" style="font-size:22px;'
                                        f'color:{co};vertical-align:middle">{ic}</span>'
                                    )
                                with ui.element("td").style("overflow:hidden;max-width:0"):
                                    ui.html(f'<div class="lx-name">{orig}</div>')
                                with ui.element("td"):
                                    ui.html(
                                        f'<span class="badge-dmc" style="background:{co}18;'
                                        f'color:{co};border:1px solid {co}38">{lb}</span>'
                                    )
                                with ui.element("td"):
                                    ui.html(f'<span class="lx-meta">{fmt_size(sz_b)}</span>')
                                with ui.element("td"):
                                    ui.html(f'<span class="lx-meta2">{ddate}</span>')
                                with ui.element("td"):
                                    ui.html(f'<span class="lx-user">{by_who}</span>')
                                with ui.element("td"):
                                    ui.html(
                                        f'<div class="lx-path" title="{origin}">'
                                        f'<span class="material-icons" style="font-size:11px;vertical-align:middle;margin-right:3px">folder_open</span>'
                                        f'{origin}</div>'
                                    )
                                with ui.element("td").style("overflow:visible"):
                                    with ui.element("div").style(
                                        "display:flex;gap:5px;justify-content:flex-start"
                                    ):
                                        _make_actions(p, is_dir)

        def _render_grid(items):
            with ui.element("div").classes("lx-grid"):
                for p in items:
                    is_dir, orig, ddate, ic, co, lb, sz_b, origin, by_who = _item_info(p)
                    with ui.element("div").classes("lx-file-card"):
                        ui.html(
                            f'<div style="display:flex;align-items:center;gap:8px">'
                            f'<span class="material-icons" style="font-size:26px;color:{co}">{ic}</span>'
                            f'<span class="badge-dmc" style="background:{co}18;color:{co};'
                            f'border:1px solid {co}38;font-size:9px">{lb}</span></div>'
                        )
                        ui.html(f'<div class="lx-card-name">{orig}</div>')
                        ui.html(f'<div class="lx-card-meta">{fmt_size(sz_b)} · {ddate}</div>')
                        ui.html(
                            f'<div class="lx-card-path" title="{origin}">'
                            f'<span class="material-icons" style="font-size:10px;vertical-align:middle">folder_open</span> '
                            f'{origin}</div>'
                        )
                        ui.html(f'<div class="lx-card-user">por {by_who}</div>')
                        with ui.element("div").classes("lx-card-actions"):
                            _make_actions(p, is_dir, compact=True)

        # ── Toggle de vista ───────────────────────────────────────────
        def _set_view(vv: str):
            view_state["v"] = vv
            for k, b in view_btns.items():
                if k == vv:
                    b.classes(add="active")
                else:
                    b.classes(remove="active")
            _render()

        view_btns["grid"].on("click", lambda: _set_view("grid"))
        view_btns["list"].on("click", lambda: _set_view("list"))

        # ── Esvaziar ─────────────────────────────────────────────────
        def _esvaziar():
            def _confirm():
                erros = 0
                for path in _items():
                    try:
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                        meta_f = TRASH_DIR / ".meta" / f"{path.name}.json"
                        if meta_f.exists():
                            meta_f.unlink()
                    except Exception:
                        erros += 1
                msg = f"Lixeira esvaziada com {erros} erro(s)." if erros else "Lixeira esvaziada."
                ui.notify(msg, type="warning" if erros else "positive")
                _render()
            _pedir_senha("Esvaziar toda a lixeira?", _confirm)

        esvaziar_btn.on("click", _esvaziar)
        _render()
