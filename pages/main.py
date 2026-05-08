"""Página principal — explorador de arquivos com estado por sessão."""

import asyncio
import json
from pathlib import Path

from nicegui import ui

from config import ROOT_DIR
from services.files import list_dir, safe, san
from ui.dialogs import (
    buscar_cliente_dialog,
    cadastrar_cliente_dialog,
    create_folder_dialog,
    delete_selected_dialog,
    share_selected_dialog,
)
from ui.main_view import render_async, render_main
from ui.sidebar import render_sidebar
from ui.styles import BOOTSTRAP_CDN, CSS, DRAG_DROP_HTML, HEADER_HTML, UTILS_JS, VIEWER_HTML
from ui.tecnicos_dialogs import inject_tecnicos_js


class PageState:
    """Estado da sessão de um único cliente conectado."""

    def __init__(self):
        self.path: Path = ROOT_DIR
        self.search: str = ""
        self.view: str = "grid"
        self.filter: str = "all"
        self._search_results = None
        self.area = None

    # ── Navegação ────────────────────────────────────────────────────

    def nav(self, path: Path) -> None:
        self.path = path
        self.search = ""
        self.render()

    def set_filter(self, f: str) -> None:
        self.filter = f
        self.render()

    def set_view(self, v: str) -> None:
        self.view = v
        self.render()

    # ── Referência para dialogs que precisam do estado ───────────────

    def _buscar_cliente_dialog(self, campo: str) -> None:
        buscar_cliente_dialog(campo)

    # ── Renderização ─────────────────────────────────────────────────

    def _full_render(self) -> None:
        """Renderiza sidebar + conteúdo principal dentro de self.area."""
        render_sidebar(self, self.set_filter, self._buscar_cliente_dialog, cadastrar_cliente_dialog)
        render_main(
            self,
            on_delete=lambda: delete_selected_dialog(self),
            on_share=lambda: share_selected_dialog(self),
            on_create_folder=lambda: create_folder_dialog(self),
        )

    def render(self) -> None:
        if self.area is None:
            return
        self._search_results = None
        _p = json.dumps(str(self.path))
        ui.run_javascript(f"window.dmcCurrentPath={_p};")
        if not self.search:
            self.area.clear()
            with self.area:
                self._full_render()
        else:
            asyncio.ensure_future(render_async(self))


@ui.page("/")
def main_page():
    from services.auth import is_authenticated, current_user_perfil
    if not is_authenticated():
        ui.navigate.to("/login")
        return
    if current_user_perfil() == "FUNCIONÁRIO CAMPO":
        ui.navigate.to("/campo")
        return

    state = PageState()

    async def _check_mobile():
        is_mobile = await ui.run_javascript(
            "window.innerWidth <= 768 || /Mobi|Android/i.test(navigator.userAgent)"
        )
        if is_mobile:
            ui.navigate.to("/mobile")

    ui.timer(0.05, _check_mobile, once=True)

    ui.dark_mode().enable()
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(VIEWER_HTML)
    ui.add_head_html(UTILS_JS)
    ui.add_body_html(HEADER_HTML)
    ui.add_body_html(DRAG_DROP_HTML)
    inject_tecnicos_js()

    from services.auth import logout_user, current_user_name

    def _logout():
        logout_user()
        ui.navigate.to("/login")

    with ui.teleport("#dmc-user-slot"):
        nome = current_user_name()
        ui.html(
            f'<div style="display:flex;align-items:center;gap:7px">'
            f'<span class="material-icons" style="font-size:15px;color:var(--dmc-muted2)">person</span>'
            f'<span style="font:500 12px \'DM Mono\',monospace;color:var(--dmc-muted2);'
            f'letter-spacing:.04em;text-transform:uppercase">{nome}</span>'
            f'</div>'
        )

    with ui.teleport("#dmc-logout-slot"):
        ui.button(icon="logout", on_click=_logout).props('flat round dense').tooltip("Sair").style(
            "color:#527A52;font-size:18px;"
        )

    refresh_btn = ui.element("button").props('id="dmc-refresh-btn"').style("display:none")
    refresh_btn.on("click", state.render)

    state.area = ui.element("div").style("width:100%")
    state.render()
