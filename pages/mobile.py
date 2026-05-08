"""Versão mobile — /mobile"""

import asyncio
from datetime import date

from nicegui import app as _app, ui

from services.auth import is_authenticated, logout_user, current_user_name, current_user_perfil
from services.agenda import fmt_event, get_events_for_month, is_connected

_COLOR_MAP = {
    "1":"#a4bdfc","2":"#7ae7bf","3":"#dbadff","4":"#ff887c","5":"#fbd75b",
    "6":"#ffb878","7":"#46d6db","8":"#e1e1e1","9":"#5484ed","10":"#51b749","11":"#dc2127",
}
_DEF = "#4ADE80"

_CSS = """
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html, body, .nicegui-content {
  height: 100% !important; margin: 0 !important; padding: 0 !important;
  overscroll-behavior: none;
}
body { background: #0C130C; }
.mb-page {
  min-height: 100vh;
  background: #0C130C;
  display: flex;
  flex-direction: column;
  padding-bottom: calc(72px + env(safe-area-inset-bottom, 0px));
}
.mb-header {
  position: sticky; top: 0; z-index: 100;
  background: rgba(6,10,6,.97);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid #1E301E;
  padding: 14px 18px;
  display: flex; align-items: center; gap: 12px;
}
.mb-logo {
  width: 36px; height: 36px; border-radius: 10px;
  background: rgba(74,222,128,.1);
  border: 1.5px solid rgba(74,222,128,.35);
  display: flex; align-items: center; justify-content: center;
  font: 800 11px 'DM Mono',monospace;
  color: #4ADE80; letter-spacing: -.3px; flex-shrink: 0;
}
.mb-title { flex: 1; }
.mb-title-main { font: 700 15px 'Syne',sans-serif; color: #DCE8DC; }
.mb-title-sub  { font: 11px 'Inter',sans-serif; color: #527A52; letter-spacing: .1em; text-transform: uppercase; }
.mb-user-badge {
  display: flex; align-items: center; gap: 7px;
  padding: 6px 12px; border-radius: 20px;
  background: rgba(74,222,128,.07);
  border: 1px solid rgba(74,222,128,.2);
}
.mb-scroll { flex: 1; overflow-y: auto; padding: 18px 16px; display: flex; flex-direction: column; gap: 16px; }
/* Cards de ação */
.mb-action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.mb-action-card {
  background: #111A11;
  border: 1px solid #1E301E;
  border-radius: 18px;
  padding: 22px 16px 18px;
  display: flex; flex-direction: column;
  align-items: flex-start; gap: 12px;
  cursor: pointer;
  transition: all .18s;
  -webkit-user-select: none; user-select: none;
  position: relative; overflow: hidden;
  min-height: 128px;
}
.mb-action-card:active { transform: scale(.97); opacity: .85; }
.mb-action-card .mb-card-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px;
}
.mb-action-card .mb-card-label {
  font: 500 13px 'Inter',sans-serif;
  color: #DCE8DC;
  line-height: 1.4;
}
.mb-action-card .mb-card-arrow {
  position: absolute; bottom: 14px; right: 14px;
  font-size: 15px; opacity: .3;
}
/* Seção agenda */
.mb-section-title {
  font: 600 11px 'DM Mono',monospace;
  color: #527A52; letter-spacing: .14em;
  text-transform: uppercase;
  display: flex; align-items: center; gap: 7px;
  margin-bottom: 6px;
}
.mb-section-title::after {
  content:''; flex:1; height:1px; background:#1E301E;
}
.mb-evt {
  background: #111A11;
  border: 1px solid #1E301E;
  border-radius: 14px;
  padding: 14px 16px;
  display: flex; gap: 12px; align-items: flex-start;
}
.mb-evt-bar { width: 3px; border-radius: 2px; align-self: stretch; flex-shrink: 0; min-height: 16px; }
.mb-evt-title { font: 500 14px 'Inter',sans-serif; color: #DCE8DC; margin-bottom: 4px; }
.mb-evt-time  { font: 12px 'DM Mono',monospace; color: #527A52; display: flex; align-items: center; gap: 4px; }
/* Links rápidos */
.mb-link-row {
  background: #111A11;
  border: 1px solid #1E301E;
  border-radius: 14px;
  padding: 16px 18px;
  display: flex; align-items: center; gap: 14px;
  cursor: pointer; transition: background .15s;
}
.mb-link-row:active { background: #1A281A; }
/* Bottom nav */
.mb-bottom-nav {
  position: fixed; bottom: 0; left: 0; right: 0;
  z-index: 200;
  background: rgba(6,10,6,.97);
  backdrop-filter: blur(20px);
  border-top: 1px solid #1E301E;
  display: flex;
  padding-bottom: env(safe-area-inset-bottom, 0px);
}
.mb-nav-btn {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 4px;
  background: transparent; border: none;
  cursor: pointer; padding: 10px 4px 8px; transition: opacity .15s;
  -webkit-user-select: none; user-select: none;
  min-height: 54px; position: relative;
}
.mb-nav-btn:active { opacity: .6; }
.mb-nav-btn .nb-icon { font-size: 24px; }
.mb-nav-btn .nb-label { font: 600 10px 'DM Mono',monospace; letter-spacing: .06em; text-transform: uppercase; }
.mb-nav-btn.active::before {
  content: ''; position: absolute; top: 0; left: 22%; right: 22%;
  height: 2px; border-radius: 0 0 3px 3px;
  background: var(--nav-color, #4ADE80);
}
"""

_LINKS = [
    ("open_in_new",   "#FBBF24", "CFT-BR",                  "https://servicos.sinceti.net.br"),
    ("map",           "#4ADE80", "SIG-RI",                   "https://mapa.onr.org.br/sigri/"),
    ("location_city", "#60A5FA", "Certidão Confrontantes",   "https://geoportal.pmf.sc.gov.br/services/certidao-confrontantes"),
    ("verified_user", "#C4B5FD", "Assinatura Gov",           "https://sso.acesso.gov.br/login?client_id=assinador.iti.br&authorization_id=19daac7a1ea"),
]


@ui.page("/mobile")
def mobile_page():
    if not is_authenticated():
        ui.navigate.to("/login")
        return

    username = current_user_name() or _app.storage.browser.get("dmc_usuario", "Usuário")
    perfil   = current_user_perfil()
    today    = date.today()
    _MESES   = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    _DIAS    = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
    data_str = f"{_DIAS[today.weekday()]}, {today.day} {_MESES[today.month-1]}"

    ui.dark_mode().enable()
    ui.add_head_html('<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">')
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, viewport-fit=cover">')
    ui.add_head_html(f"<style>{_CSS}</style>")

    with ui.element("div").classes("mb-page"):

        # ── Header ────────────────────────────────────────────────────
        with ui.element("div").classes("mb-header"):
            ui.html('<div class="mb-logo">DMC</div>')
            with ui.element("div").classes("mb-title"):
                ui.html('<div class="mb-title-main">DMC Topografia</div>')
                ui.html(f'<div class="mb-title-sub">{data_str}</div>')
            with ui.element("div").classes("mb-user-badge"):
                ui.html('<span class="material-icons" style="font-size:13px;color:#4ADE80">person</span>')
                ui.html(f'<span style="font:600 12px \'DM Mono\',monospace;color:#DCE8DC">{username.split()[0]}</span>')

        with ui.element("div").classes("mb-scroll"):

            # ── Ações rápidas ──────────────────────────────────────────
            with ui.element("div").classes("mb-action-grid"):
                _CARDS = [
                    ("fingerprint", "#4ADE80", "rgba(74,222,128,.12)", "Registro\nde Campo",   "/campo"),
                    ("today",       "#FBBF24", "rgba(251,191,36,.12)", "Ver\nAgenda",           None),
                    ("folder_open", "#60A5FA", "rgba(96,165,250,.12)", "Arquivos\n(Desktop)",   "/"),
                    ("person_add",  "#C4B5FD", "rgba(196,181,253,.12)","Cadastrar\nCliente",    "/cliente/cadastrar"),
                ]
                for icon, fg, bg, label, href in _CARDS:
                    card = ui.element("div").classes("mb-action-card").style(
                        f"border-color:{fg}22;"
                    )
                    with card:
                        ui.html(
                            f'<div class="mb-card-icon" style="background:{bg}">'
                            f'<span class="material-icons" style="color:{fg}">{icon}</span></div>'
                        )
                        ui.html(
                            f'<div class="mb-card-label">{label.replace(chr(10),"<br>")}</div>'
                        )
                        ui.html('<span class="material-icons mb-card-arrow">arrow_forward</span>')
                    if href:
                        if href == "/campo":
                            card.on("click", lambda: ui.run_javascript("window.open('/campo','_blank','noopener,noreferrer')"))
                        else:
                            card.on("click", lambda h=href: ui.navigate.to(h))
                    else:
                        from ui.agenda_dialogs import ver_agenda_dialog
                        card.on("click", ver_agenda_dialog)

            # ── Agenda do dia ──────────────────────────────────────────
            ui.html(
                f'<div class="mb-section-title">'
                f'<span class="material-icons" style="font-size:12px;color:#FBBF24">today</span>'
                f'Agenda de hoje</div>'
            )
            agenda_area = ui.element("div").style("display:flex;flex-direction:column;gap:8px")

            async def _load_agenda():
                agenda_area.clear()
                with agenda_area:
                    if not is_connected():
                        ui.html(
                            '<div style="padding:20px;text-align:center;background:#111A11;'
                            'border:1px solid #1E301E;border-radius:12px;'
                            'font:12px \'DM Mono\',monospace;color:#527A52">'
                            'Google Agenda não conectado</div>'
                        )
                        return
                    try:
                        raw    = await asyncio.to_thread(get_events_for_month, today.year, today.month)
                        hoje   = today.isoformat()
                        eventos = sorted(
                            [fmt_event(e) for e in raw if fmt_event(e).get("date_key") == hoje],
                            key=lambda e: e.get("time_str","")
                        )
                        if not eventos:
                            ui.html(
                                '<div style="padding:20px;text-align:center;background:#111A11;'
                                'border:1px dashed #1E301E;border-radius:12px;'
                                'font:12px \'DM Mono\',monospace;color:#527A52">'
                                'Sem eventos hoje</div>'
                            )
                        else:
                            for ev in eventos:
                                dot = _COLOR_MAP.get(ev["color"], _DEF)
                                with ui.element("div").classes("mb-evt"):
                                    ui.element("div").classes("mb-evt-bar").style(f"background:{dot}")
                                    with ui.element("div").style("flex:1;min-width:0"):
                                        ui.html(f'<div class="mb-evt-title">{ev["title"]}</div>')
                                        ui.html(
                                            f'<div class="mb-evt-time">'
                                            f'<span class="material-icons" style="font-size:11px">schedule</span>'
                                            f'{ev["time_str"]}</div>'
                                        )
                                        if ev.get("location"):
                                            ui.html(
                                                f'<div style="font:12px \'Inter\',sans-serif;color:#527A52;margin-top:4px;'
                                                f'display:flex;align-items:center;gap:4px">'
                                                f'<span class="material-icons" style="font-size:11px">location_on</span>'
                                                f'{ev["location"]}</div>'
                                            )
                    except Exception as exc:
                        ui.html(f'<div style="color:#F87171;font:12px monospace;padding:10px">Erro: {exc}</div>')

            ui.timer(0.1, _load_agenda, once=True)

            # ── Links rápidos ──────────────────────────────────────────
            ui.html(
                '<div class="mb-section-title" style="margin-top:4px">'
                '<span class="material-icons" style="font-size:12px;color:#60A5FA">link</span>'
                'Links rápidos</div>'
            )
            for icon, color, label, url in _LINKS:
                row = ui.element("div").classes("mb-link-row")
                with row:
                    ui.html(
                        f'<span class="material-icons" style="font-size:20px;color:{color};flex-shrink:0">{icon}</span>'
                    )
                    ui.html(f'<span style="font:500 14px \'Inter\',sans-serif;color:#DCE8DC;flex:1">{label}</span>')
                    ui.html('<span class="material-icons" style="font-size:16px;color:#2A4A2A">open_in_new</span>')
                row.on("click", lambda u=url: ui.run_javascript(
                    f"window.open({repr(u)},'_blank','noopener,noreferrer')"
                ))

        # ── Bottom nav ────────────────────────────────────────────────
        def _do_logout():
            logout_user()
            ui.navigate.to("/login")

        with ui.element("div").classes("mb-bottom-nav"):
            for nav_icon, nav_color, nav_label, nav_action in [
                ("home",        "#4ADE80", "Início",   lambda: ui.navigate.to("/mobile")),
                ("assignment",  "#FBBF24", "Campo",    lambda: ui.run_javascript("window.open('/campo','_blank','noopener,noreferrer')")),
                ("computer",    "#60A5FA", "Desktop",  lambda: ui.navigate.to("/")),
                ("logout",      "#F87171", "Sair",     _do_logout),
            ]:
                is_active = nav_icon == "home"
                btn = ui.element("button").classes("mb-nav-btn" + (" active" if is_active else ""))
                if is_active:
                    btn.style(f"--nav-color:{nav_color}")
                with btn:
                    ui.html(f'<span class="material-icons nb-icon" style="color:{nav_color}">{nav_icon}</span>')
                    ui.html(f'<span class="nb-label" style="color:{nav_color}">{nav_label}</span>')
                btn.on("click", nav_action)
