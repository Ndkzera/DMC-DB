"""Área principal: toolbar, breadcrumb, estatísticas, pastas e arquivos."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from nicegui import ui

from config import ROOT_DIR
from services.files import (
    breadcrumbs,
    file_url,
    list_dir,
    safe,
    san,
    vtype,
)
from ui.components import sec_hdr, tbtn
from ui.sidebar import render_sidebar
from services.auth import current_user_label, current_user_perfil
from services.acesso import has_access
from services.log import log_action

_executor = ThreadPoolExecutor(max_workers=4)


def _folder_label(path: Path) -> str:
    """Retorna label legível do diretório pai relativo à raiz."""
    parent = path.parent
    try:
        parts = parent.relative_to(ROOT_DIR).parts
        if not parts:
            return "Raiz"
        return "/".join(parts[-2:]) if len(parts) > 1 else parts[0]
    except ValueError:
        return parent.name


# ── Pastas ───────────────────────────────────────────────────────────

def _folders_list(folders: list, nav_fn, is_search: bool = False) -> None:
    with ui.element("div").classes("table-responsive").style("margin-bottom:24px"):
        with ui.element("table").classes("table table-dmc table-hover mb-0"):
            with ui.element("thead"):
                with ui.element("tr"):
                    cols = [("", "40px"), ("Nome", "auto"), ("Itens", "110px"), ("Modificado", "120px")]
                    if is_search:
                        cols.append(("Pasta", "180px"))
                    cols.append(("", "80px"))
                    for col, w in cols:
                        with ui.element("th").style(f"width:{w}"):
                            ui.html(col)
            with ui.element("tbody"):
                for f in folders:
                    row = ui.element("tr").classes("dmc-folder-row fu")
                    with row:
                        with ui.element("td"):
                            ui.html('<span class="material-icons" style="color:var(--dmc-amber);font-size:22px">folder</span>')
                        with ui.element("td"):
                            ui.html(
                                f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text);'
                                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{f["name"]}</div>'
                            )
                        with ui.element("td"):
                            ui.html(f'<span style="font:11px var(--dmc-fm);color:var(--dmc-muted)">{f.get("count", 0)} itens</span>')
                        with ui.element("td"):
                            ui.html(f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted2)">{f["mtime_str"]}</span>')
                        if is_search:
                            with ui.element("td"):
                                chip = ui.element("div").style(
                                    "display:inline-flex;align-items:center;gap:5px;padding:4px 10px;"
                                    "border-radius:7px;cursor:pointer;max-width:170px;"
                                    "background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);"
                                    "transition:background .12s;"
                                )
                                with chip:
                                    ui.html('<span class="material-icons" style="font-size:12px;color:#60A5FA;flex-shrink:0">folder_open</span>')
                                    ui.html(
                                        f'<span style="font:11px var(--dmc-mono);color:#60A5FA;'
                                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                        f'{_folder_label(f["path"])}</span>'
                                    )
                                chip.on("click", lambda p=f["path"].parent: nav_fn(p))
                        with ui.element("td").style("text-align:right"):
                            ob = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                            with ob:
                                ui.html('<span class="material-icons">folder_open</span>')
                                ui.html("<span>Abrir</span>")
                            ob.on("click", lambda p=f["path"]: nav_fn(p))
                    row.on("dblclick", lambda p=f["path"]: nav_fn(p))


# ── Arquivos ─────────────────────────────────────────────────────────

def _file_card(f: dict, nav_fn=None, is_search: bool = False) -> None:
    c     = f["cat"]
    color = c["color"]
    icon  = c["icon"]
    label = c["label"]
    url   = file_url(f["path"])
    name  = f["name"]
    vt    = vtype(f["ext"])

    card_h = "height:210px" if is_search else "height:185px"
    with ui.element("div").classes("card dmc-file-card fu").style(card_h):
        with ui.element("div").style(
            "display:flex;flex-direction:column;height:100%;padding:13px 11px 10px;"
        ):
            with ui.element("div").style("display:flex;flex-direction:column;gap:5px;flex:1;min-height:0"):
                ui.html(
                    f'<div class="badge-dmc" style="background:{color}18;color:{color};'
                    f'border:1px solid {color}38;display:inline-block">{label}</div>'
                )
                ui.html(f'<span class="material-icons" style="font-size:28px;color:{color}">{icon}</span>')
                ui.html(
                    f'<div class="dmc-clamp2" style="font:11px/1.5 var(--dmc-fm);color:var(--dmc-text)">{name}</div>'
                )
                ui.html(f'<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">{f["size"]}</div>')

            if is_search and nav_fn:
                folder_chip = ui.element("div").style(
                    "display:flex;align-items:center;gap:4px;padding:4px 8px;margin-top:6px;"
                    "border-radius:6px;cursor:pointer;overflow:hidden;"
                    "background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);"
                    "transition:background .12s;"
                )
                with folder_chip:
                    ui.html('<span class="material-icons" style="font-size:11px;color:#60A5FA;flex-shrink:0">folder_open</span>')
                    ui.html(
                        f'<span style="font:10px var(--dmc-mono);color:#60A5FA;'
                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                        f'{_folder_label(f["path"])}</span>'
                    )
                folder_chip.on("click", lambda p=f["path"].parent: nav_fn(p))

            with ui.element("div").style(
                "display:flex;gap:4px;padding-top:8px;border-top:1px solid var(--dmc-b1);margin-top:6px;"
            ):
                if vt:
                    vb = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm flex-fill")
                    with vb:
                        ui.html('<span class="material-icons">visibility</span>')
                        ui.html("<span>Ver</span>")
                    vb.on("click", lambda u=url, n=name, v=vt:
                        ui.run_javascript(f'openViewer("{u}","{n}","{v}")'))

                db = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm flex-fill")
                with db:
                    ui.html('<span class="material-icons">download</span>')
                    ui.html("<span>DL</span>")
                db.on("click", lambda u=url: ui.download(u))


def _folders_grid(folders: list, nav_fn, is_search: bool = False) -> None:
    card_h = "height:210px" if is_search else "height:185px"
    with ui.element("div").classes("row row-cols-2 row-cols-md-3 row-cols-xl-4 g-2").style("margin-bottom:24px"):
        for f in folders:
            with ui.element("div").classes("col"):
                card = ui.element("div").classes("card dmc-file-card fu").style(card_h)
                with card:
                    with ui.element("div").style(
                        "display:flex;flex-direction:column;height:100%;padding:13px 11px 10px;"
                    ):
                        with ui.element("div").style("display:flex;flex-direction:column;gap:6px;flex:1;min-height:0"):
                            ui.html('<span class="material-icons" style="font-size:32px;color:var(--dmc-amber)">folder</span>')
                            ui.html(
                                f'<div class="dmc-clamp2" style="font:500 12px/1.4 var(--dmc-fm);color:var(--dmc-text)">{f["name"]}</div>'
                            )
                            ui.html(
                                f'<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">'
                                f'{f.get("count", 0)} itens · {f["mtime_str"]}</div>'
                            )
                        if is_search:
                            folder_chip = ui.element("div").style(
                                "display:flex;align-items:center;gap:4px;padding:4px 8px;margin-top:6px;"
                                "border-radius:6px;cursor:pointer;overflow:hidden;"
                                "background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);"
                                "transition:background .12s;"
                            )
                            with folder_chip:
                                ui.html('<span class="material-icons" style="font-size:11px;color:#60A5FA;flex-shrink:0">folder_open</span>')
                                ui.html(
                                    f'<span style="font:10px var(--dmc-mono);color:#60A5FA;'
                                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                    f'{_folder_label(f["path"])}</span>'
                                )
                            folder_chip.on("click", lambda p=f["path"].parent: nav_fn(p))
                        with ui.element("div").style(
                            "display:flex;padding-top:8px;border-top:1px solid var(--dmc-b1);margin-top:6px;"
                        ):
                            ob = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm flex-fill")
                            with ob:
                                ui.html('<span class="material-icons">folder_open</span>')
                                ui.html("<span>Abrir</span>")
                            ob.on("click", lambda p=f["path"]: nav_fn(p))
                card.on("dblclick", lambda p=f["path"]: nav_fn(p))


def _files_grid(files: list, nav_fn=None, is_search: bool = False) -> None:
    with ui.element("div").classes("row row-cols-2 row-cols-md-3 row-cols-xl-4 g-2").style("margin-bottom:30px"):
        for f in files:
            with ui.element("div").classes("col"):
                _file_card(f, nav_fn=nav_fn, is_search=is_search)


def _files_list(files: list, nav_fn=None, is_search: bool = False) -> None:
    with ui.element("div").classes("table-responsive").style("margin-bottom:30px"):
        with ui.element("table").classes("table table-dmc table-hover mb-0").style(
            "table-layout:fixed;width:100%"
        ):
            with ui.element("thead"):
                with ui.element("tr"):
                    cols = [("", "40px"), ("Nome", "auto"), ("Tipo", "80px"), ("Tamanho", "100px"), ("Modificado", "120px")]
                    if is_search:
                        cols.append(("Pasta", "180px"))
                    cols.append(("", "110px"))
                    for col, w in cols:
                        with ui.element("th").style(f"width:{w}"):
                            ui.html(col)
            with ui.element("tbody"):
                for f in files:
                    c     = f["cat"]
                    color = c["color"]
                    icon  = c["icon"]
                    label = c["label"]
                    url   = file_url(f["path"])
                    name  = f["name"]
                    vt    = vtype(f["ext"])
                    with ui.element("tr").classes("fu"):
                        with ui.element("td"):
                            ui.html(f'<span class="material-icons" style="color:{color};font-size:20px">{icon}</span>')
                        with ui.element("td").style("overflow:hidden;max-width:0"):
                            ui.html(
                                f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text);'
                                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{name}</div>'
                            )
                        with ui.element("td"):
                            ui.html(
                                f'<div class="badge-dmc" style="background:{color}18;color:{color};'
                                f'border:1px solid {color}38;display:inline-block">{label}</div>'
                            )
                        with ui.element("td"):
                            ui.html(f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted)">{f["size"]}</span>')
                        with ui.element("td"):
                            ui.html(f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted2)">{f["mtime_str"]}</span>')
                        if is_search:
                            with ui.element("td"):
                                chip = ui.element("div").style(
                                    "display:inline-flex;align-items:center;gap:5px;padding:4px 10px;"
                                    "border-radius:7px;cursor:pointer;max-width:170px;"
                                    "background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);"
                                    "transition:background .12s;"
                                )
                                with chip:
                                    ui.html('<span class="material-icons" style="font-size:12px;color:#60A5FA;flex-shrink:0">folder_open</span>')
                                    ui.html(
                                        f'<span style="font:11px var(--dmc-mono);color:#60A5FA;'
                                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                        f'{_folder_label(f["path"])}</span>'
                                    )
                                chip.on("click", lambda p=f["path"].parent: nav_fn(p))
                        with ui.element("td").style("text-align:right"):
                            with ui.element("div").style("display:flex;gap:4px;justify-content:flex-end"):
                                if vt:
                                    vb = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                                    with vb:
                                        ui.html('<span class="material-icons">visibility</span>')
                                        ui.html("<span>Ver</span>")
                                    vb.on("click", lambda u=url, n=name, v=vt:
                                        ui.run_javascript(f'openViewer("{u}","{n}","{v}")'))
                                db = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                                with db:
                                    ui.html('<span class="material-icons">download</span>')
                                    ui.html("<span>DL</span>")
                                db.on("click", lambda u=url: ui.download(u))


# ── Área principal ────────────────────────────────────────────────────

def render_main(state, on_delete, on_share, on_create_folder) -> None:
    from config import ROOT_DIR

    path   = state.path
    search = state.search
    filt   = state.filter

    if hasattr(state, "_search_results") and state._search_results is not None:
        folders_all, files_all = state._search_results
    else:
        folders_all, files_all = list_dir(path, search)

    if filt != "all":
        files_all   = [f for f in files_all if f["cat"]["group"] == filt]
        folders_all = []

    with ui.element("div").style(
        "margin-left:260px;margin-top:60px;"
        "min-height:calc(100vh - 60px);padding:24px 28px;"
        "position:relative;z-index:1;"
    ):
        # ── Toolbar ──────────────────────────────────────────────────
        with ui.element("div").style(
            "display:flex;align-items:center;gap:8px;margin-bottom:18px;flex-wrap:wrap"
        ):
            nb = tbtn("Nova Pasta", "create_new_folder", primary=True)
            nb.on("click", on_create_folder)

            bk = tbtn("Voltar", "arrow_back")
            if path != ROOT_DIR:
                bk.on("click", lambda: state.nav(path.parent))
            else:
                bk.style("opacity:.35;cursor:not-allowed;pointer-events:none")

            rb = tbtn("Atualizar", "refresh")
            rb.on("click", state.render)

            db_btn = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
            with db_btn:
                ui.html('<span class="material-icons">delete</span>')
                ui.html("<span>Deletar</span>")
            db_btn.on("click", on_delete)

            sh_btn = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
            with sh_btn:
                ui.html('<span class="material-icons">share</span>')
                ui.html("<span>Compartilhar</span>")
            sh_btn.on("click", on_share)

            ui.element("div").style("width:1px;height:28px;background:var(--dmc-b1);margin:0 2px")
            ui.html(
                '<div style="font:600 12px var(--dmc-fd);color:var(--dmc-muted2);letter-spacing:.03em">'
                'Database DMC</div>'
            )
            if has_access(current_user_perfil() or "", "arq_lixeira"):
                lx_btn = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                with lx_btn:
                    ui.html('<span class="material-icons" style="font-size:15px;color:#F87171">delete</span>')
                    ui.html("<span>Lixeira</span>")
                lx_btn.on("click", lambda: ui.navigate.to("/lixeira"))
            ui.element("div").style("flex:1")

            # Alternador de vista
            with ui.element("div").style("display:flex;gap:4px"):
                for vv, ic in [("grid", "grid_view"), ("list", "view_list")]:
                    act = state.view == vv
                    variant = "dmc-btn-primary" if act else "dmc-btn-secondary"
                    vb = ui.element("button").classes(f"dmc-btn-icon {variant}").style(
                        "border-radius:8px!important"
                    )
                    with vb:
                        ui.html(f'<span class="material-icons" style="font-size:17px">{ic}</span>')
                    vb.on("click", lambda v=vv: state.set_view(v))

            ui.element("div").style("width:1px;height:28px;background:var(--dmc-b1);margin:0 4px")

            # Busca
            si = (
                ui.input(placeholder="Buscar… (Enter para buscar)", value=search)
                .props('outlined dense color="green" prepend-icon="search"')
                .style("width:240px;font-family:var(--dmc-fm);font-size:12px")
            )

            def _do_search():
                state.search = si.value.strip()
                state.render()

            def _clear_search():
                if not si.value:
                    state.search = ""
                    state.render()

            si.on("keydown.enter", _do_search)
            si.on("keydown.escape", lambda: (si.set_value(""), _clear_search()))

        # ── Breadcrumb ────────────────────────────────────────────────
        crumbs = breadcrumbs(path)
        with ui.element("nav").style("margin-bottom:18px"):
            with ui.element("div").classes("dmc-crumb"):
                for i, (name, p) in enumerate(crumbs):
                    is_last = i == len(crumbs) - 1
                    if i > 0:
                        ui.html('<span class="dmc-crumb-sep">›</span>')
                    if is_last:
                        ui.html(f'<span class="dmc-crumb-cur">{name}</span>')
                    else:
                        lnk = ui.element("span").classes("dmc-crumb-link")
                        with lnk:
                            ui.html(name)
                        lnk.on("click", lambda pp=p: state.nav(pp))
        ui.run_javascript(
            "var el=document.querySelector('.dmc-crumb');"
            "if(el)el.scrollLeft=el.scrollWidth;"
        )

        # ── Estatísticas ──────────────────────────────────────────────
        total_b = sum(f["size_bytes"] for f in files_all)
        stats = [
            (str(len(folders_all)), "pastas"),
            (str(len(files_all)),   "arquivos"),
            (
                f"{total_b / 1024**3:.2f} GB" if total_b >= 1024**3 else
                f"{total_b / 1024**2:.1f} MB" if total_b >= 1024**2 else
                f"{total_b / 1024:.1f} KB"    if total_b >= 1024    else f"{total_b} B",
                "total"
            ),
            (path.name if path != ROOT_DIR else "Raiz", "diretório"),
        ]
        with ui.element("div").style(
            "display:flex;background:var(--dmc-bg2);border:1px solid var(--dmc-b1);"
            "border-radius:12px;overflow:hidden;margin-bottom:24px;"
        ):
            for idx, (val, lbl_txt) in enumerate(stats):
                with ui.element("div").style("padding:14px 20px;flex:1;display:flex;flex-direction:column;gap:3px"):
                    ui.html(
                        f'<div style="font:700 20px var(--dmc-fd);color:var(--dmc-green);line-height:1">{val}</div>'
                    )
                    ui.html(
                        f'<div style="font:9px var(--dmc-mono);color:var(--dmc-muted2);'
                        f'text-transform:uppercase;letter-spacing:.1em">{lbl_txt}</div>'
                    )
                if idx < len(stats) - 1:
                    ui.element("div").style("width:1px;background:var(--dmc-b1);align-self:stretch")

        # ── Pastas / Arquivos / Vazio ─────────────────────────────────
        is_search = bool(search)

        if folders_all:
            sec_hdr(f"Pastas · {len(folders_all)}")
            if state.view == "list":
                _folders_list(folders_all, state.nav, is_search=is_search)
            else:
                _folders_grid(folders_all, state.nav, is_search=is_search)

        if files_all:
            sec_hdr(f"Arquivos · {len(files_all)}")
            if state.view == "list":
                _files_list(files_all, nav_fn=state.nav, is_search=is_search)
            else:
                _files_grid(files_all, nav_fn=state.nav, is_search=is_search)

        if not folders_all and not files_all:
            with ui.element("div").style(
                "display:flex;flex-direction:column;align-items:center;"
                "justify-content:center;padding:80px;gap:14px;color:var(--dmc-muted2);"
            ):
                ui.html('<span class="material-icons" style="font-size:52px;opacity:.2">folder_open</span>')
                ui.html(
                    f'<div style="font:13px var(--dmc-fm)">'
                    f'{"Nenhum resultado." if search else "Pasta vazia."}</div>'
                )


async def render_async(state) -> None:
    """Executa list_dir em thread e depois renderiza — evita bloquear o event loop."""
    from config import ROOT_DIR

    query     = state.search
    path_name = state.path.name or str(state.path)

    def _cancel_and_root():
        state.search = ""
        state.path   = ROOT_DIR
        state.render()

    state.area.clear()
    with state.area:
        from ui.sidebar import render_sidebar
        render_sidebar(state, state.set_filter, state._buscar_cliente_dialog)
        with ui.element("div").style(
            "margin-left:260px;margin-top:60px;padding:0 32px;"
            "display:flex;flex-direction:column;align-items:center;"
            "justify-content:center;gap:16px;"
        ):
            with ui.element("div").style(
                "display:flex;align-items:center;gap:12px;"
                "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);"
                "border-radius:14px;padding:18px 24px;max-width:480px;width:100%"
            ):
                ui.html(
                    '<span class="material-icons" style="font-size:26px;color:var(--dmc-muted2);'
                    'animation:spin 1s linear infinite;flex-shrink:0">refresh</span>'
                )
                with ui.element("div").style("flex:1;min-width:0"):
                    ui.html(
                        f'<div style="font:600 13px var(--dmc-fm);color:var(--dmc-text);'
                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                        f'Procurando: <span style="color:#FBBF24">{query}</span></div>'
                        f'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);margin-top:3px">'
                        f'em <span style="color:var(--dmc-muted)">{path_name}</span> e subpastas</div>'
                    )
            ui.button(
                "Cancelar e voltar à raiz",
                icon="close",
                on_click=_cancel_and_root,
            ).props("flat no-caps").classes("dmc-btn dmc-btn-ghost").style(
                "font:12px var(--dmc-fm);color:var(--dmc-muted2)"
            )

    loop = asyncio.get_event_loop()
    state._search_results = await loop.run_in_executor(
        _executor, list_dir, state.path, query
    )

    # Se o usuário cancelou durante a busca, não re-renderiza
    if state.search != query:
        state._search_results = None
        return

    state.area.clear()
    with state.area:
        state._full_render()

    state._search_results = None


async def handle_upload(e, state) -> None:
    from config import ROOT_DIR
    path  = state.path
    fname = san(e.file.name)
    if not fname:
        ui.notify("Nome inválido.", type="negative")
        return

    target = path / fname
    if not safe(target):
        ui.notify("Caminho não permitido.", type="negative")
        return

    if target.exists():
        stem, suf = target.stem, target.suffix
        i = 1
        while target.exists():
            target = path / f"{stem}_{i}{suf}"
            i += 1

    try:
        content = await e.file.read()
        target.write_bytes(content)
        log_action(current_user_label(), current_user_perfil(),
                   "upload", "arquivo", target.name, str(path))
        ui.notify(f"✓ {target.name} enviado!", type="positive")
        state.render()
    except OSError as ex:
        ui.notify(f"Erro: {ex}", type="negative")
