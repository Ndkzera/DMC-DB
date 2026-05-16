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

    import time as _time
    from services.auth import (
        logout_user, current_user_name, current_user_perfil,
        mark_active, get_active_count, get_active_users, PERFIL_CORES,
    )
    from nicegui import app as _app

    def _logout():
        logout_user()
        ui.navigate.to("/login")

    nome   = current_user_name()
    email  = _app.storage.user.get("dmc_user_email", "")
    perfil = current_user_perfil()
    mark_active(email, nome, perfil)

    with ui.teleport("#dmc-user-slot"):
        ui.html(
            f'<div style="display:flex;align-items:center;gap:7px">'
            f'<span class="material-icons" style="font-size:15px;color:var(--dmc-muted2)">person</span>'
            f'<span style="font:500 12px \'DM Mono\',monospace;color:var(--dmc-muted2);'
            f'letter-spacing:.04em;text-transform:uppercase">{nome}</span>'
            f'</div>'
        )

    # ── Slot de membros ativos (clicável) ────────────────────────────
    with ui.teleport("#dmc-active-slot"):
        with ui.element("button").style(
            "display:flex;align-items:center;gap:5px;cursor:pointer;"
            "background:transparent;border:none;padding:3px 8px;border-radius:6px;"
            "transition:background .15s;"
        ).on("mouseover", lambda: None).on("mouseout", lambda: None) as active_btn:
            ui.html(
                '<span class="material-icons" '
                'style="font-size:14px;color:var(--dmc-muted2);pointer-events:none">people</span>'
            )
            active_count_el = ui.html(
                '<span style="font:500 11px \'DM Mono\',monospace;'
                'color:var(--dmc-muted2);letter-spacing:.04em;pointer-events:none">—</span>'
            )

    def _update_active_count():
        cnt = get_active_count()
        active_count_el.set_content(
            f'<span style="font:500 11px \'DM Mono\',monospace;'
            f'color:var(--dmc-muted2);letter-spacing:.04em;pointer-events:none">{cnt}</span>'
        )

    _update_active_count()

    def _open_active_dialog():
        users = get_active_users()
        now   = _time.time()
        with ui.dialog() as dlg:
            dlg.open()
            with ui.card().style(
                "width:300px;max-width:96vw;padding:0;gap:0;"
                "background:var(--dmc-bg2)!important;"
                "border:1px solid var(--dmc-b2)!important;"
                "border-radius:14px!important;"
                "box-shadow:0 16px 48px rgba(0,0,0,.55)!important;"
            ):
                # cabeçalho
                with ui.element("div").style(
                    "display:flex;align-items:center;gap:8px;"
                    "padding:12px 16px;border-bottom:1px solid var(--dmc-b1);"
                ):
                    ui.html(
                        '<span class="material-icons" '
                        'style="font-size:16px;color:var(--dmc-muted2)">people</span>'
                        '<span style="font:700 13px var(--dmc-fd);color:var(--dmc-text);flex:1">'
                        'Membros Ativos</span>'
                    )
                    ui.html(
                        f'<span style="font:500 10px var(--dmc-mono);'
                        f'color:var(--dmc-muted2);background:var(--dmc-bg3);"'                        f'style="padding:2px 7px;border-radius:4px">{len(users)}</span>'
                    )
                    cb = ui.element("button").style(
                        "background:transparent;border:none;cursor:pointer;"
                        "color:var(--dmc-muted2);display:flex;align-items:center;padding:2px"
                    )
                    with cb:
                        ui.html('<span class="material-icons" style="font-size:16px">close</span>')
                    cb.on("click", dlg.close)

                # lista
                with ui.element("div").style(
                    "padding:10px;max-height:320px;overflow-y:auto;display:flex;"
                    "flex-direction:column;gap:6px;"
                ):
                    if not users:
                        ui.html(
                            '<div style="text-align:center;padding:24px;'
                            'font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                            'Nenhum membro online</div>'
                        )
                    else:
                        for u in users:
                            u_nome   = u.get("nome", "—")
                            u_perfil = u.get("perfil", "")
                            elapsed  = int(now - u.get("ts", now))
                            if elapsed < 60:
                                since = "agora"
                            elif elapsed < 3600:
                                since = f"{elapsed // 60}min atrás"
                            else:
                                since = f"{elapsed // 3600}h atrás"

                            tc, bc, brd = PERFIL_CORES.get(
                                u_perfil, ("#8BAA8B", "rgba(139,170,139,.08)", "rgba(139,170,139,.25)")
                            )
                            inicial = (u_nome[:1] or "?").upper()
                            ui.html(
                                f'<div style="display:flex;align-items:center;gap:10px;'
                                f'padding:8px 10px;border-radius:9px;'
                                f'background:var(--dmc-bg3);border:1px solid var(--dmc-b1)">'
                                # avatar
                                f'<div style="width:32px;height:32px;border-radius:8px;flex-shrink:0;'
                                f'background:{bc};border:1.5px solid {brd};'
                                f'display:flex;align-items:center;justify-content:center;">'
                                f'<span style="font:700 13px var(--dmc-fd);color:{tc}">{inicial}</span>'
                                f'</div>'
                                # info
                                f'<div style="flex:1;min-width:0">'
                                f'<div style="font:500 12px var(--dmc-fm);color:var(--dmc-text);'
                                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{u_nome}</div>'
                                f'<div style="margin-top:3px;display:flex;align-items:center;gap:5px">'
                                f'<span style="font:500 8px var(--dmc-mono);letter-spacing:.05em;'
                                f'background:{bc};color:{tc};padding:1px 5px;border-radius:3px">'
                                f'{u_perfil or "—"}</span>'
                                f'<span style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">{since}</span>'
                                f'</div></div>'
                                # dot online
                                f'<span class="material-icons" '
                                f'style="font-size:10px;color:#4ADE80;flex-shrink:0">fiber_manual_record</span>'
                                f'</div>'
                            )

    active_btn.on("click", _open_active_dialog)

    def _heartbeat():
        mark_active(email, nome, perfil)
        _update_active_count()

    ui.timer(60, _heartbeat)

    # ── Notificações ─────────────────────────────────────────────────
    from services.acesso import has_access
    from services.financeiro import get_notificacoes

    _pode_ver_fi = has_access(perfil, "fi_ver")

    _NOTIF_LEVEL_COLORS = {
        "danger":  ("#F87171", "rgba(248,113,113,.12)", "rgba(248,113,113,.3)"),
        "warning": ("#FBBF24", "rgba(251,191,36,.10)",  "rgba(251,191,36,.3)"),
        "info":    ("#60A5FA", "rgba(96,165,250,.10)",   "rgba(96,165,250,.3)"),
    }

    # Sino só é montado para usuários com acesso ao financeiro
    if _pode_ver_fi:
        with ui.teleport("#dmc-notif-slot"):
            notif_btn = ui.element("button").style(
                "position:relative;width:34px;height:34px;border-radius:8px;"
                "border:1px solid var(--dmc-b2);background:transparent;cursor:pointer;"
                "display:flex;align-items:center;justify-content:center;"
                "color:var(--dmc-muted);transition:all .2s;flex-shrink:0;"
            )
            with notif_btn:
                ui.html(
                    '<span class="material-icons" style="font-size:18px;pointer-events:none">'
                    'notifications_none</span>'
                )
                notif_badge = ui.html("").style(
                    "position:absolute;top:4px;right:4px;pointer-events:none"
                )

        def _update_notif_badge():
            notifs = get_notificacoes()
            count  = len(notifs)
            if count:
                has_danger = any(n["nivel"] == "danger" for n in notifs)
                col = "#F87171" if has_danger else "#FBBF24"
                notif_badge.set_content(
                    f'<span style="'
                    f'min-width:14px;height:14px;border-radius:7px;padding:0 3px;'
                    f'background:{col};color:#0a0a0a;font:700 8px var(--dmc-mono);'
                    f'display:flex;align-items:center;justify-content:center;'
                    f'line-height:1;box-sizing:border-box">'
                    f'{count}</span>'
                )
                notif_btn.style(
                    "position:relative;width:34px;height:34px;border-radius:8px;"
                    f"border:1px solid {col}44;background:transparent;cursor:pointer;"
                    "display:flex;align-items:center;justify-content:center;"
                    f"color:{col};transition:all .2s;flex-shrink:0;"
                )
            else:
                notif_badge.set_content("")
                notif_btn.style(
                    "position:relative;width:34px;height:34px;border-radius:8px;"
                    "border:1px solid var(--dmc-b2);background:transparent;cursor:pointer;"
                    "display:flex;align-items:center;justify-content:center;"
                    "color:var(--dmc-muted);transition:all .2s;flex-shrink:0;"
                )

        _update_notif_badge()

        def _open_notif_dialog():
            notifs = get_notificacoes()
            with ui.dialog() as ndlg:
                ndlg.open()
                with ui.card().style(
                    "width:340px;max-width:96vw;padding:0;gap:0;"
                    "background:var(--dmc-bg2)!important;"
                    "border:1px solid var(--dmc-b2)!important;"
                    "border-radius:14px!important;"
                    "box-shadow:0 16px 48px rgba(0,0,0,.55)!important;"
                ):
                    with ui.element("div").style(
                        "display:flex;align-items:center;gap:8px;"
                        "padding:12px 16px;border-bottom:1px solid var(--dmc-b1);"
                    ):
                        ui.html(
                            '<span class="material-icons" style="font-size:16px;color:var(--dmc-muted2)">'
                            'notifications</span>'
                            '<span style="font:700 13px var(--dmc-fd);color:var(--dmc-text);flex:1">'
                            'Notificações</span>'
                        )
                        if notifs:
                            ui.html(
                                f'<span style="font:700 9px var(--dmc-mono);color:#F87171;'
                                f'background:rgba(248,113,113,.1);padding:2px 7px;border-radius:4px">'
                                f'{len(notifs)}</span>'
                            )
                        ncb = ui.element("button").style(
                            "background:transparent;border:none;cursor:pointer;"
                            "color:var(--dmc-muted2);display:flex;align-items:center;padding:2px"
                        )
                        with ncb:
                            ui.html('<span class="material-icons" style="font-size:16px">close</span>')
                        ncb.on("click", ndlg.close)

                    with ui.element("div").style(
                        "padding:10px;max-height:360px;overflow-y:auto;display:flex;"
                        "flex-direction:column;gap:6px;"
                    ):
                        if not notifs:
                            ui.html(
                                '<div style="text-align:center;padding:28px 12px;">'
                                '<span class="material-icons" style="font-size:36px;color:var(--dmc-muted2);'
                                'opacity:.3;display:block;margin-bottom:8px">notifications_none</span>'
                                '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">'
                                'Nenhuma notificação pendente</div>'
                                '</div>'
                            )
                        else:
                            for n in notifs:
                                tc, bg, brd = _NOTIF_LEVEL_COLORS.get(n["nivel"], _NOTIF_LEVEL_COLORS["info"])
                                ui.html(
                                    f'<div style="display:flex;align-items:flex-start;gap:10px;'
                                    f'padding:10px 12px;border-radius:9px;'
                                    f'background:{bg};border:1px solid {brd}">'
                                    f'<span class="material-icons" style="font-size:18px;color:{tc};'
                                    f'flex-shrink:0;margin-top:1px">{n["icon"]}</span>'
                                    f'<div style="flex:1;min-width:0">'
                                    f'<div style="font:500 12px var(--dmc-fm);color:{tc};line-height:1.3">'
                                    f'{n["titulo"]}</div>'
                                    f'<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2);margin-top:3px">'
                                    f'{n["detalhe"]}</div>'
                                    f'</div></div>'
                                )

                    with ui.element("div").style(
                        "padding:8px 12px;border-top:1px solid var(--dmc-b1);"
                        "display:flex;justify-content:flex-end"
                    ):
                        goto = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                        with goto:
                            ui.html(
                                '<span class="material-icons" style="font-size:13px">payments</span>'
                                "<span>Ir ao Financeiro</span>"
                            )
                        goto.on("click", lambda: [ndlg.close(), ui.navigate.to("/financeiro")])

        notif_btn.on("click", _open_notif_dialog)
        ui.timer(120, _update_notif_badge)

    with ui.teleport("#dmc-logout-slot"):
        ui.button(icon="logout", on_click=_logout).props('flat round dense').tooltip("Sair").style(
            "color:#527A52;font-size:18px;"
        )

    auto_logout_btn = ui.element("button").props('id="dmc-auto-logout"').style(
        "display:none;position:absolute;pointer-events:none"
    )
    auto_logout_btn.on("click", _logout)

    refresh_btn = ui.element("button").props('id="dmc-refresh-btn"').style("display:none")
    refresh_btn.on("click", state.render)

    state.area = ui.element("div").style("width:100%")
    state.render()
