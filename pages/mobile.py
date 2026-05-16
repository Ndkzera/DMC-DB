"""Versão mobile — /mobile — DMC Hub de Serviços"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from nicegui import app as _app, ui

from config import ROOT_DIR
from services.auth import (
    is_authenticated, logout_user,
    current_user_name, current_user_perfil,
)
from services.agenda import fmt_event, get_events_for_month, is_connected
from services.files import breadcrumbs, file_url, list_dir, vtype

_executor = ThreadPoolExecutor(max_workers=2)

# ── Constantes ────────────────────────────────────────────────────────

_COLOR_MAP = {
    "1":"#a4bdfc","2":"#7ae7bf","3":"#dbadff","4":"#ff887c","5":"#fbd75b",
    "6":"#ffb878","7":"#46d6db","8":"#e1e1e1","9":"#5484ed","10":"#51b749","11":"#dc2127",
}
_DEF_COLOR = "#4ADE80"

_STATUS_COLORS = {
    "planejamento": ("#FBBF24", "rgba(251,191,36,.10)"),
    "ativo":        ("#4ADE80", "rgba(74,222,128,.10)"),
    "pausado":      ("#F87171", "rgba(248,113,113,.10)"),
    "concluído":    ("#60A5FA", "rgba(96,165,250,.10)"),
    "concluido":    ("#60A5FA", "rgba(96,165,250,.10)"),
}

_LINKS = [
    ("open_in_new",   "#FBBF24", "CFT-BR",                 "https://servicos.sinceti.net.br"),
    ("map",           "#4ADE80", "SIG-RI",                  "https://mapa.onr.org.br/sigri/"),
    ("location_city", "#60A5FA", "Certidão Confrontantes",  "https://geoportal.pmf.sc.gov.br/services/certidao-confrontantes"),
    ("verified_user", "#C4B5FD", "Assinatura Gov",          "https://sso.acesso.gov.br/login?client_id=assinador.iti.br&authorization_id=19daac7a1ea"),
]

_CSS = """
* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
html, body {
  height: 100% !important; width: 100% !important;
  margin: 0 !important; padding: 0 !important;
  overscroll-behavior: none;
}
/* Anular todos os wrappers do Quasar/NiceGUI */
.nicegui-content,
.q-layout, .q-layout__section--marginal,
.q-page-container, .q-page {
  margin: 0 !important; padding: 0 !important;
  min-height: 0 !important; height: auto !important;
  width: 100% !important; max-width: 100% !important;
}
body { background: #0C130C; }
@keyframes spin { from { transform:rotate(0deg); } to { transform:rotate(360deg); } }
@keyframes fu   { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:none; } }

/* Cobre o viewport inteiro, independente de qualquer container pai */
.mb-page {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  padding-top: env(safe-area-inset-top, 0px);
  background: #0C130C;
  display: flex; flex-direction: column; overflow: hidden;
}
.mb-header {
  z-index: 100;
  background: rgba(6,10,6,.97); backdrop-filter: blur(20px);
  border-bottom: 1px solid #1E301E;
  padding: 11px 16px;
  display: flex; align-items: center; gap: 12px; flex-shrink: 0;
}
/* Content wrapper — fills space between header and bottom nav */
.mb-content {
  flex: 1; display: flex; flex-direction: column; overflow: hidden;
}
/* Scrollable area inside each tab */
.mb-scroll {
  flex: 1; overflow-y: auto;
  padding: 16px 16px 76px;
  display: flex; flex-direction: column; gap: 14px;
  -webkit-overflow-scrolling: touch;
}

/* ── Quick-action cards ── */
.mb-action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.mb-action-card {
  background: #111A11; border: 1px solid #1E301E; border-radius: 18px;
  padding: 20px 16px 16px;
  display: flex; flex-direction: column; align-items: flex-start; gap: 10px;
  cursor: pointer; transition: all .18s;
  -webkit-user-select: none; user-select: none;
  position: relative; overflow: hidden; min-height: 118px;
}
.mb-action-card:active { transform: scale(.97); opacity: .82; }
.mb-card-icon {
  width: 42px; height: 42px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; font-size: 22px;
}
.mb-card-label { font: 500 13px 'Inter',sans-serif; color: #DCE8DC; line-height: 1.4; }
.mb-card-arrow { position: absolute; bottom: 12px; right: 12px; font-size: 14px; opacity: .22; }

/* ── Section title ── */
.mb-section-title {
  font: 600 10px 'DM Mono',monospace;
  color: #527A52; letter-spacing: .14em; text-transform: uppercase;
  display: flex; align-items: center; gap: 6px; margin-bottom: 2px;
}
.mb-section-title::after { content:''; flex:1; height:1px; background:#1E301E; }

/* ── Event cards ── */
.mb-evt {
  background: #111A11; border: 1px solid #1E301E; border-radius: 14px;
  padding: 13px 15px; display: flex; gap: 11px; align-items: flex-start;
  animation: fu .2s ease both;
}
.mb-evt-bar { width: 3px; border-radius: 2px; align-self: stretch; flex-shrink: 0; min-height: 16px; }
.mb-evt-title { font: 500 14px 'Inter',sans-serif; color: #DCE8DC; margin-bottom: 3px; }
.mb-evt-time  { font: 11px 'DM Mono',monospace; color: #527A52; display: flex; align-items: center; gap: 4px; }

/* ── File / list rows ── */
.mb-file-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px;
  background: #111A11; border: 1px solid #1E301E; border-radius: 14px;
  cursor: pointer; transition: background .14s; animation: fu .18s ease both;
}
.mb-file-row:active { background: #182218; }

/* ── Breadcrumb ── */
.mb-crumb {
  display: flex; align-items: center; gap: 4px; flex-shrink: 0;
  overflow-x: auto; scrollbar-width: none;
  padding: 10px 16px 10px; border-bottom: 1px solid #1E301E;
  background: rgba(6,10,6,.6);
}
.mb-crumb::-webkit-scrollbar { display: none; }

/* ── Search bar ── */
.mb-search-bar {
  display: flex; align-items: center; gap: 8px;
  background: #111A11; border: 1.5px solid #1E301E; border-radius: 14px;
  padding: 0 14px; height: 48px; transition: border-color .15s;
}
.mb-search-bar:focus-within { border-color: rgba(74,222,128,.35); }

/* ── Chips ── */
.mb-chip {
  padding: 6px 14px; border-radius: 20px;
  border: 1px solid #1E301E; background: transparent;
  font: 500 12px 'Inter',sans-serif; color: #527A52;
  cursor: pointer; transition: all .15s;
  -webkit-user-select: none; user-select: none; white-space: nowrap;
}
.mb-chip.active {
  background: rgba(74,222,128,.1);
  border-color: rgba(74,222,128,.3); color: #4ADE80;
}

/* ── Generic card ── */
.mb-card {
  background: #111A11; border: 1px solid #1E301E; border-radius: 14px;
  padding: 14px 16px; display: flex; flex-direction: column; gap: 8px;
  animation: fu .2s ease both;
}

/* ── Link rows ── */
.mb-link-row {
  background: #111A11; border: 1px solid #1E301E; border-radius: 14px;
  padding: 15px 16px; display: flex; align-items: center; gap: 13px;
  cursor: pointer; transition: background .14s;
}
.mb-link-row:active { background: #182218; }

/* ── Empty state ── */
.mb-empty {
  text-align: center; padding: 32px 20px;
  font: 11px 'DM Mono',monospace; color: #2A4A2A; line-height: 1.9;
}

/* ── Bottom nav ── */
.mb-bottom-nav {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 200;
  background: rgba(6,10,6,.97); backdrop-filter: blur(20px);
  border-top: 1px solid #1E301E;
  display: flex; padding-bottom: env(safe-area-inset-bottom, 0px);
}
.mb-nav-btn {
  flex: 1; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 3px;
  background: transparent; border: none; cursor: pointer;
  padding: 10px 4px 8px; transition: opacity .15s;
  -webkit-user-select: none; user-select: none;
  min-height: 56px; position: relative;
}
.mb-nav-btn:active { opacity: .55; }
.mb-nav-btn .nb-icon  { font-size: 22px; color: #2A4A2A; transition: color .15s; }
.mb-nav-btn .nb-label { font: 600 9px 'DM Mono',monospace; letter-spacing: .06em; text-transform: uppercase; color: #2A4A2A; transition: color .15s; }
.mb-nav-btn.active .nb-icon,
.mb-nav-btn.active .nb-label { color: var(--nav-color, #4ADE80); }
.mb-nav-btn.active::before {
  content: ''; position: absolute; top: 0; left: 18%; right: 18%;
  height: 2.5px; border-radius: 0 0 4px 4px;
  background: var(--nav-color, #4ADE80);
}
"""

_NAV_JS = """
<script>
var _MB_MUTED = '#2A4A2A';
function mbSetTab(tab, color) {
  document.querySelectorAll('.mb-nav-btn').forEach(function(b) {
    var active = b.dataset.tab === tab;
    b.classList.toggle('active', active);
    var col = active ? color : _MB_MUTED;
    b.querySelectorAll('.nb-icon,.nb-label').forEach(function(s) {
      s.style.color = col;
    });
    if (active) b.style.setProperty('--nav-color', color);
  });
}
</script>
"""


# ── Estado ────────────────────────────────────────────────────────────

class MobileState:
    def __init__(self):
        self.tab: str       = "home"
        self.file_path: Path = ROOT_DIR
        self.content_area   = None

    def switch_tab(self, tab: str, color: str = "#4ADE80") -> None:
        self.tab = tab
        ui.run_javascript(f"mbSetTab('{tab}','{color}')")
        self.render()

    def render(self) -> None:
        if self.content_area is None:
            return
        if self.tab == "home":
            _render_home(self)
        elif self.tab == "files":
            asyncio.ensure_future(_render_files(self))
        elif self.tab == "clients":
            _render_clients(self)
        elif self.tab == "campo":
            asyncio.ensure_future(_render_campo(self))
        elif self.tab == "mais":
            asyncio.ensure_future(_render_mais(self))


# ── Helpers ───────────────────────────────────────────────────────────

def _mb_icon_box(icon: str, color: str, size: int = 38) -> None:
    """Caixa quadrada com ícone material."""
    ui.html(
        f'<div style="width:{size}px;height:{size}px;border-radius:10px;flex-shrink:0;'
        f'background:{color}18;border:1px solid {color}30;'
        f'display:flex;align-items:center;justify-content:center;">'
        f'<span class="material-icons" style="font-size:{size-16}px;color:{color}">{icon}</span></div>'
    )


def _mb_loading(msg: str = "Carregando…") -> None:
    ui.html(
        f'<div style="display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;padding:60px 20px;gap:14px">'
        f'<span class="material-icons" style="font-size:30px;color:#2A4A2A;'
        f'animation:spin 1s linear infinite">refresh</span>'
        f'<span style="font:11px \'DM Mono\',monospace;color:#2A4A2A;letter-spacing:.08em">'
        f'{msg}</span></div>'
    )


def _action_btn(label: str, icon: str, fg: str, bg: str, fn) -> None:
    """Botão de ação largo (flex:1)."""
    btn = ui.element("button").style(
        f"flex:1;height:40px;border-radius:11px;"
        f"background:{bg};border:1px solid {fg}38;"
        f"display:flex;align-items:center;justify-content:center;gap:6px;cursor:pointer;"
    )
    with btn:
        ui.html(f'<span class="material-icons" style="font-size:16px;color:{fg}">{icon}</span>')
        ui.html(f'<span style="font:600 11px \'DM Mono\',monospace;color:{fg};letter-spacing:.04em">{label}</span>')
    btn.on("click", fn)


# ── Tab: Início ───────────────────────────────────────────────────────

def _render_home(state: MobileState) -> None:
    state.content_area.clear()
    today  = date.today()
    _MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    _DIAS  = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
    data_str = f"{_DIAS[today.weekday()]}, {today.day} de {_MESES[today.month-1]}"
    primeiro = (current_user_name() or "Usuário").split()[0]

    with state.content_area:
        with ui.element("div").classes("mb-scroll"):
            # Saudação
            ui.html(
                f'<div style="padding:4px 2px 6px">'
                f'<div style="font:800 22px \'Syne\',sans-serif;color:#DCE8DC;line-height:1.1">'
                f'Olá, {primeiro}!</div>'
                f'<div style="font:11px \'DM Mono\',monospace;color:#527A52;margin-top:5px;'
                f'letter-spacing:.07em">{data_str.upper()}</div>'
                f'</div>'
            )

            # Ações rápidas
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#4ADE80">bolt</span>'
                'Ações Rápidas</div>'
            )
            with ui.element("div").classes("mb-action-grid"):
                _CARDS = [
                    ("fingerprint", "#4ADE80", "rgba(74,222,128,.1)",   "Registro\nde Campo",   "campo_page"),
                    ("today",       "#FBBF24", "rgba(251,191,36,.1)",   "Ver\nAgenda",           "tab_campo"),
                    ("people",      "#60A5FA", "rgba(96,165,250,.1)",   "Buscar\nClientes",      "tab_clients"),
                    ("engineering", "#C4B5FD", "rgba(196,181,253,.1)",  "Ver\nObras",            "tab_mais"),
                ]
                for icon, fg, bg, label, action in _CARDS:
                    card = ui.element("div").classes("mb-action-card").style(f"border-color:{fg}22")
                    with card:
                        ui.html(f'<div class="mb-card-icon" style="background:{bg}">'
                                f'<span class="material-icons" style="color:{fg}">{icon}</span></div>')
                        ui.html(f'<div class="mb-card-label">{label.replace(chr(10),"<br>")}</div>')
                        ui.html('<span class="material-icons mb-card-arrow">arrow_forward</span>')
                    if action == "campo_page":
                        card.on("click", lambda: ui.run_javascript(
                            "window.open('/campo','_blank','noopener,noreferrer')"))
                    elif action == "tab_campo":
                        card.on("click", lambda: state.switch_tab("campo", "#C4B5FD"))
                    elif action == "tab_clients":
                        card.on("click", lambda: state.switch_tab("clients", "#60A5FA"))
                    elif action == "tab_mais":
                        card.on("click", lambda: state.switch_tab("mais", "#8BAA8B"))

            # Agenda do dia
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#FBBF24">calendar_today</span>'
                'Agenda de hoje</div>'
            )
            agenda_area = ui.element("div").style("display:flex;flex-direction:column;gap:8px")
            async def _start_agenda():
                await _load_agenda_home(agenda_area, today)
            ui.timer(0.05, _start_agenda, once=True)


async def _load_agenda_home(area, today: date) -> None:
    area.clear()
    with area:
        if not is_connected():
            ui.html(
                '<div class="mb-empty">Google Agenda não conectado<br>'
                '<span style="font-size:10px;opacity:.6">Conecte na versão desktop</span></div>'
            )
            return
        try:
            loop  = asyncio.get_event_loop()
            raw   = await loop.run_in_executor(_executor, get_events_for_month, today.year, today.month)
            hoje  = today.isoformat()
            evts  = sorted(
                [fmt_event(e) for e in raw if fmt_event(e).get("date_key") == hoje],
                key=lambda e: e.get("time_str", "")
            )
            if not evts:
                ui.html('<div class="mb-empty">Sem eventos hoje ✓</div>')
                return
            for ev in evts:
                dot = _COLOR_MAP.get(ev["color"], _DEF_COLOR)
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
                                f'<div style="font:11px \'Inter\',sans-serif;color:#527A52;margin-top:3px;'
                                f'display:flex;align-items:center;gap:4px">'
                                f'<span class="material-icons" style="font-size:11px">location_on</span>'
                                f'{ev["location"]}</div>'
                            )
        except Exception as exc:
            ui.html(f'<div style="color:#F87171;font:11px monospace;padding:12px">Erro: {exc}</div>')


# ── Tab: Arquivos ─────────────────────────────────────────────────────

async def _render_files(state: MobileState) -> None:
    state.content_area.clear()
    with state.content_area:
        _mb_loading("Carregando arquivos…")

    loop = asyncio.get_event_loop()
    try:
        folders, files = await loop.run_in_executor(_executor, list_dir, state.file_path, "")
    except Exception as exc:
        state.content_area.clear()
        with state.content_area:
            ui.html(f'<div style="color:#F87171;font:12px monospace;padding:20px">Erro: {exc}</div>')
        return

    state.content_area.clear()
    with state.content_area:
        # Breadcrumb
        crumbs = breadcrumbs(state.file_path)
        with ui.element("div").classes("mb-crumb"):
            if state.file_path != ROOT_DIR:
                back = ui.element("button").style(
                    "width:30px;height:30px;border-radius:8px;flex-shrink:0;"
                    "background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.2);"
                    "display:flex;align-items:center;justify-content:center;cursor:pointer;"
                )
                with back:
                    ui.html('<span class="material-icons" style="font-size:15px;color:#4ADE80">arrow_back</span>')
                back.on("click", lambda: _nav_files(state, state.file_path.parent))

            for i, (name, p) in enumerate(crumbs):
                if i > 0:
                    ui.html('<span style="color:#2A4A2A;font-size:14px;flex-shrink:0;padding:0 2px">›</span>')
                is_last = i == len(crumbs) - 1
                if is_last:
                    ui.html(
                        f'<span style="font:500 12px \'DM Mono\',monospace;color:#DCE8DC;'
                        f'white-space:nowrap;flex-shrink:0">{name}</span>'
                    )
                else:
                    lnk = ui.element("span").style(
                        "font:12px 'DM Mono',monospace;color:#527A52;white-space:nowrap;"
                        "flex-shrink:0;cursor:pointer;"
                    )
                    with lnk:
                        ui.html(name)
                    lnk.on("click", lambda pp=p: _nav_files(state, pp))

        with ui.element("div").classes("mb-scroll").style("padding-top:14px"):
            if not folders and not files:
                ui.html(
                    '<div class="mb-empty">'
                    '<span class="material-icons" style="font-size:44px;display:block;opacity:.18;margin-bottom:8px">folder_open</span>'
                    'Pasta vazia</div>'
                )

            if folders:
                ui.html(
                    f'<div class="mb-section-title">'
                    f'<span class="material-icons" style="font-size:11px;color:#FBBF24">folder</span>'
                    f'Pastas · {len(folders)}</div>'
                )
                with ui.element("div").style("display:flex;flex-direction:column;gap:8px;margin-bottom:4px"):
                    for f in folders:
                        row = ui.element("div").classes("mb-file-row")
                        with row:
                            _mb_icon_box("folder", "#FBBF24")
                            with ui.element("div").style("flex:1;min-width:0"):
                                ui.html(
                                    f'<div style="font:500 14px \'Inter\',sans-serif;color:#DCE8DC;'
                                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{f["name"]}</div>'
                                )
                                ui.html(
                                    f'<div style="font:11px \'DM Mono\',monospace;color:#527A52;margin-top:2px">'
                                    f'{f.get("count",0)} itens · {f["mtime_str"]}</div>'
                                )
                            ui.html('<span class="material-icons" style="font-size:18px;color:#2A4A2A;flex-shrink:0">chevron_right</span>')
                        row.on("click", lambda p=f["path"]: _nav_files(state, p))

            if files:
                ui.html(
                    f'<div class="mb-section-title">'
                    f'<span class="material-icons" style="font-size:11px;color:#60A5FA">insert_drive_file</span>'
                    f'Arquivos · {len(files)}</div>'
                )
                with ui.element("div").style("display:flex;flex-direction:column;gap:8px"):
                    for f in files:
                        c     = f["cat"]
                        color = c["color"]
                        icon  = c["icon"]
                        label = c["label"]
                        url   = file_url(f["path"])
                        vt    = vtype(f["ext"])

                        row = ui.element("div").classes("mb-file-row")
                        with row:
                            _mb_icon_box(icon, color)
                            with ui.element("div").style("flex:1;min-width:0"):
                                ui.html(
                                    f'<div style="font:500 13px \'Inter\',sans-serif;color:#DCE8DC;'
                                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{f["name"]}</div>'
                                )
                                ui.html(
                                    f'<div style="font:11px \'DM Mono\',monospace;color:#527A52;margin-top:2px;'
                                    f'display:flex;align-items:center;gap:6px">'
                                    f'<span style="background:{color}18;color:{color};padding:1px 5px;'
                                    f'border-radius:3px;font-size:9px">{label}</span>'
                                    f'{f["size"]} · {f["mtime_str"]}</div>'
                                )
                            with ui.element("div").style("display:flex;gap:6px;flex-shrink:0"):
                                if vt:
                                    vb = ui.element("button").style(
                                        "width:34px;height:34px;border-radius:9px;flex-shrink:0;"
                                        "background:rgba(96,165,250,.1);border:1px solid rgba(96,165,250,.2);"
                                        "display:flex;align-items:center;justify-content:center;cursor:pointer;"
                                    )
                                    with vb:
                                        ui.html('<span class="material-icons" style="font-size:16px;color:#60A5FA">visibility</span>')
                                    vb.on("click", lambda u=url:
                                        ui.run_javascript(f'window.open("{u}","_blank","noopener,noreferrer")'))

                                db = ui.element("button").style(
                                    "width:34px;height:34px;border-radius:9px;flex-shrink:0;"
                                    "background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.2);"
                                    "display:flex;align-items:center;justify-content:center;cursor:pointer;"
                                )
                                with db:
                                    ui.html('<span class="material-icons" style="font-size:16px;color:#4ADE80">download</span>')
                                db.on("click", lambda u=url: ui.download(u))


def _nav_files(state: MobileState, path: Path) -> None:
    state.file_path = path
    asyncio.ensure_future(_render_files(state))


# ── Tab: Clientes ─────────────────────────────────────────────────────

def _render_clients(state: MobileState) -> None:
    from services.clientes import load_clientes, fmt_tel as _fmt_tel

    state.content_area.clear()
    with state.content_area:
        with ui.element("div").classes("mb-scroll"):
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#60A5FA">people</span>'
                'Clientes</div>'
            )

            field_state = {"v": state.client_field if hasattr(state, "client_field") else "nome"}
            chip_refs: dict = {}

            # Chips de campo
            with ui.element("div").style("display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px"):
                for fid, flbl in [("nome","Nome"),("telefone","Telefone"),("cpf","CPF/CNPJ")]:
                    c = ui.element("button").classes("mb-chip" + (" active" if fid == field_state["v"] else ""))
                    with c:
                        ui.html(flbl)
                    chip_refs[fid] = c
                    def _set(f=fid):
                        field_state["v"] = f
                        if hasattr(state, "client_field"):
                            state.client_field = f
                        for k, cr in chip_refs.items():
                            if k == f: cr.classes(add="active")
                            else:       cr.classes(remove="active")
                    c.on("click", _set)

            # Barra de busca
            with ui.element("div").classes("mb-search-bar"):
                si = (
                    ui.input(placeholder="Buscar cliente…")
                    .props("dense borderless")
                    .style("flex:1;font:14px 'Inter',sans-serif;color:#DCE8DC;min-width:0")
                )
                sb = ui.element("button").style(
                    "width:36px;height:36px;border-radius:10px;flex-shrink:0;"
                    "background:rgba(74,222,128,.1);border:1px solid rgba(74,222,128,.2);"
                    "display:flex;align-items:center;justify-content:center;cursor:pointer;"
                )
                with sb:
                    ui.html('<span class="material-icons" style="color:#4ADE80;font-size:18px">search</span>')

            results_area = ui.element("div").style("display:flex;flex-direction:column;gap:8px")

            def _do_search():
                q = si.value.strip()
                results_area.clear()
                with results_area:
                    if not q:
                        return
                    clientes = load_clientes()
                    campo    = field_state["v"]
                    q_low    = q.lower()
                    q_dig    = "".join(ch for ch in q if ch.isdigit())
                    results  = []
                    for cl in clientes:
                        if campo == "nome" and q_low in cl.get("nome","").lower():
                            results.append(cl)
                        elif campo == "telefone" and q_dig and q_dig in "".join(ch for ch in cl.get("telefone","") if ch.isdigit()):
                            results.append(cl)
                        elif campo == "cpf" and q_dig and q_dig in "".join(ch for ch in cl.get("cpf","") if ch.isdigit()):
                            results.append(cl)

                    if not results:
                        ui.html(f'<div class="mb-empty">Nenhum resultado para "{q}"</div>')
                        return

                    ui.html(
                        f'<div style="font:11px \'DM Mono\',monospace;color:#527A52;'
                        f'letter-spacing:.04em">{len(results)} resultado{"s" if len(results)>1 else ""}</div>'
                    )
                    for cl in results[:30]:
                        nome    = cl.get("nome","—")
                        tel     = _fmt_tel(cl.get("telefone",""))
                        cpf     = cl.get("cpf","")
                        cidade  = cl.get("end_cidade","")
                        estado  = cl.get("end_estado","")
                        tipo    = cl.get("tipo","PF")
                        tc      = "#60A5FA" if tipo == "PJ" else "#4ADE80"
                        inicial = (nome[:1] or "?").upper()
                        tel_raw = "".join(ch for ch in cl.get("telefone","") if ch.isdigit())

                        with ui.element("div").classes("mb-card"):
                            # Header da linha
                            with ui.element("div").style("display:flex;align-items:flex-start;gap:10px"):
                                ui.html(
                                    f'<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                                    f'background:{tc}14;border:1px solid {tc}28;'
                                    f'display:flex;align-items:center;justify-content:center;">'
                                    f'<span style="font:700 15px \'Syne\',sans-serif;color:{tc}">{inicial}</span></div>'
                                )
                                with ui.element("div").style("flex:1;min-width:0"):
                                    ui.html(
                                        f'<div style="font:600 14px \'Inter\',sans-serif;color:#DCE8DC;'
                                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{nome}</div>'
                                    )
                                    ui.html(
                                        f'<div style="display:flex;align-items:center;gap:6px;margin-top:3px">'
                                        f'<span style="font:700 9px \'DM Mono\',monospace;'
                                        f'background:{tc}14;color:{tc};padding:1px 6px;border-radius:3px">{tipo}</span>'
                                        f'<span style="font:11px \'DM Mono\',monospace;color:#527A52">{cpf}</span>'
                                        f'</div>'
                                    )
                            # Contato / local
                            if tel:
                                with ui.element("div").style("display:flex;align-items:center;gap:6px"):
                                    ui.html('<span class="material-icons" style="font-size:13px;color:#2A4A2A">phone</span>')
                                    ui.html(f'<span style="font:13px \'Inter\',sans-serif;color:#8BAA8B">{tel}</span>')
                            if cidade:
                                with ui.element("div").style("display:flex;align-items:center;gap:6px"):
                                    ui.html('<span class="material-icons" style="font-size:13px;color:#2A4A2A">location_on</span>')
                                    ui.html(
                                        f'<span style="font:12px \'Inter\',sans-serif;color:#527A52">'
                                        f'{cidade}{", "+estado if estado else ""}</span>'
                                    )
                            # Ações
                            with ui.element("div").style(
                                "display:flex;gap:8px;padding-top:10px;border-top:1px solid #1E301E;margin-top:2px"
                            ):
                                if tel_raw:
                                    _action_btn(
                                        "Ligar", "phone", "#4ADE80", "rgba(74,222,128,.08)",
                                        lambda t=tel_raw: ui.run_javascript(f'window.location.href="tel:{t}"')
                                    )
                                maps_url = cl.get("obra_maps") or cl.get("end_maps","")
                                if maps_url:
                                    _action_btn(
                                        "Maps", "map", "#60A5FA", "rgba(96,165,250,.08)",
                                        lambda u=maps_url: ui.run_javascript(
                                            f'window.open({repr(u)},"_blank","noopener,noreferrer")')
                                    )

            si.on("keydown.enter", _do_search)
            sb.on("click", _do_search)

            with results_area:
                ui.html('<div class="mb-empty">Digite para buscar</div>')


# ── Tab: Campo ────────────────────────────────────────────────────────

async def _render_campo(state: MobileState) -> None:
    state.content_area.clear()
    with state.content_area:
        _mb_loading("Carregando registros…")

    today = date.today()
    try:
        from services.ponto import load_ponto
        registros = await asyncio.get_event_loop().run_in_executor(_executor, load_ponto)
    except Exception:
        registros = []

    state.content_area.clear()
    with state.content_area:
        with ui.element("div").classes("mb-scroll"):

            # Ponto rápido
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#4ADE80">fingerprint</span>'
                'Ponto</div>'
            )
            with ui.element("div").style("display:flex;gap:10px"):
                for label, icon, fg, bg in [
                    ("CHECK-IN",  "login",  "#4ADE80", "rgba(74,222,128,.1)"),
                    ("CHECK-OUT", "logout", "#F87171", "rgba(248,113,113,.08)"),
                ]:
                    btn = ui.element("button").style(
                        f"flex:1;height:58px;border-radius:14px;"
                        f"background:{bg};border:1.5px solid {fg}38;"
                        f"display:flex;flex-direction:column;align-items:center;"
                        f"justify-content:center;gap:4px;cursor:pointer;"
                    )
                    with btn:
                        ui.html(f'<span class="material-icons" style="font-size:22px;color:{fg}">{icon}</span>')
                        ui.html(f'<span style="font:700 9px \'DM Mono\',monospace;color:{fg};letter-spacing:.08em">{label}</span>')
                    btn.on("click", lambda: ui.run_javascript(
                        "window.open('/campo','_blank','noopener,noreferrer')"))

            # Registros de hoje
            hoje_str  = today.strftime("%d/%m/%Y")
            hoje_regs = sorted(
                [r for r in registros if r.get("data") == hoje_str],
                key=lambda r: r.get("hora","")
            )
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#FBBF24">today</span>'
                'Registros de hoje</div>'
            )
            if not hoje_regs:
                ui.html('<div class="mb-empty">Sem registros hoje</div>')
            else:
                with ui.element("div").style("display:flex;flex-direction:column;gap:8px;margin-bottom:4px"):
                    for r in hoje_regs:
                        tipo  = r.get("tipo","checkin")
                        fc    = "#4ADE80" if tipo == "checkin" else "#F87171"
                        icon  = "login"  if tipo == "checkin" else "logout"
                        label = "Check-in" if tipo == "checkin" else "Check-out"
                        with ui.element("div").classes("mb-evt"):
                            ui.element("div").classes("mb-evt-bar").style(f"background:{fc}")
                            with ui.element("div").style("flex:1;min-width:0"):
                                with ui.element("div").style("display:flex;align-items:center;gap:7px"):
                                    ui.html(f'<span class="material-icons" style="font-size:14px;color:{fc}">{icon}</span>')
                                    ui.html(f'<span style="font:500 13px \'Inter\',sans-serif;color:#DCE8DC">{label}</span>')
                                    ui.html(
                                        f'<span style="margin-left:auto;font:600 12px \'DM Mono\',monospace;color:{fc}">'
                                        f'{r.get("hora","—")}</span>'
                                    )
                                if r.get("usuario"):
                                    ui.html(
                                        f'<div class="mb-evt-time" style="margin-top:4px">'
                                        f'<span class="material-icons" style="font-size:11px">person</span>'
                                        f'{r["usuario"]}</div>'
                                    )
                                if r.get("obra"):
                                    ui.html(
                                        f'<div class="mb-evt-time" style="margin-top:2px">'
                                        f'<span class="material-icons" style="font-size:11px">construction</span>'
                                        f'{r["obra"]}</div>'
                                    )

            # Histórico recente (últimos 15)
            recent = sorted(
                registros,
                key=lambda r: (r.get("data",""), r.get("hora","")),
                reverse=True
            )[:15]
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#60A5FA">history</span>'
                'Histórico recente</div>'
            )
            if not recent:
                ui.html('<div class="mb-empty">Sem registros</div>')
            else:
                with ui.element("div").style("display:flex;flex-direction:column;gap:6px"):
                    for r in recent:
                        tipo  = r.get("tipo","checkin")
                        fc    = "#4ADE80" if tipo == "checkin" else "#F87171"
                        badge = "IN" if tipo == "checkin" else "OUT"
                        with ui.element("div").style(
                            "display:flex;align-items:center;gap:10px;"
                            "padding:10px 13px;background:#111A11;"
                            "border:1px solid #1E301E;border-radius:12px;"
                        ):
                            ui.html(
                                f'<span style="font:700 9px \'DM Mono\',monospace;'
                                f'background:{fc}14;color:{fc};border:1px solid {fc}28;'
                                f'padding:3px 7px;border-radius:4px;flex-shrink:0">{badge}</span>'
                            )
                            with ui.element("div").style("flex:1;min-width:0"):
                                ui.html(
                                    f'<div style="font:500 12px \'Inter\',sans-serif;color:#DCE8DC;'
                                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                    f'{r.get("usuario","—")}</div>'
                                )
                                if r.get("obra"):
                                    ui.html(
                                        f'<div style="font:11px \'DM Mono\',monospace;color:#527A52;'
                                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                        f'{r["obra"]}</div>'
                                    )
                            with ui.element("div").style("text-align:right;flex-shrink:0"):
                                ui.html(f'<div style="font:11px \'DM Mono\',monospace;color:#527A52">{r.get("data","—")}</div>')
                                ui.html(f'<div style="font:600 11px \'DM Mono\',monospace;color:{fc}">{r.get("hora","—")}</div>')


# ── Tab: Mais ─────────────────────────────────────────────────────────

async def _render_mais(state: MobileState) -> None:
    state.content_area.clear()
    with state.content_area:
        _mb_loading("Carregando…")

    try:
        from services.obras import load_obras
        obras = await asyncio.get_event_loop().run_in_executor(_executor, load_obras)
    except Exception:
        obras = []

    state.content_area.clear()
    with state.content_area:
        with ui.element("div").classes("mb-scroll"):

            # Obras
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#C4B5FD">engineering</span>'
                'Obras</div>'
            )
            filter_state = {"v": "todas"}
            chip_refs: dict = {}

            def _render_obras():
                obras_area.clear()
                filt     = filter_state["v"]
                filtered = obras if filt == "todas" else [
                    o for o in obras if o.get("status","").lower() == filt
                ]
                with obras_area:
                    if not filtered:
                        ui.html('<div class="mb-empty">Nenhuma obra encontrada</div>')
                        return
                    for obra in filtered[:25]:
                        status = obra.get("status","").lower()
                        sc, sb = _STATUS_COLORS.get(status, ("#8BAA8B","rgba(139,170,139,.08)"))
                        with ui.element("div").classes("mb-card"):
                            with ui.element("div").style("display:flex;align-items:flex-start;gap:10px"):
                                _mb_icon_box("construction", sc)
                                with ui.element("div").style("flex:1;min-width:0"):
                                    ui.html(
                                        f'<div style="font:600 13px \'Inter\',sans-serif;color:#DCE8DC;'
                                        f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                        f'{obra.get("cliente_nome","—")}</div>'
                                    )
                                    ui.html(
                                        f'<span style="font:700 9px \'DM Mono\',monospace;'
                                        f'background:{sb};color:{sc};'
                                        f'padding:2px 7px;border-radius:4px;display:inline-block;margin-top:3px">'
                                        f'{obra.get("status","—").upper()}</span>'
                                    )
                            cidade = obra.get("obra_cidade","")
                            log    = obra.get("obra_log","")
                            if log or cidade:
                                addr = f'{log} {obra.get("obra_num","")}'.strip()
                                full = f'{addr}, {cidade}' if cidade else addr
                                with ui.element("div").style("display:flex;align-items:center;gap:5px;margin-top:2px"):
                                    ui.html('<span class="material-icons" style="font-size:13px;color:#2A4A2A">location_on</span>')
                                    ui.html(f'<span style="font:12px \'Inter\',sans-serif;color:#527A52">{full}</span>')
                            ui.html(
                                f'<div style="display:flex;gap:14px;margin-top:4px">'
                                f'<span style="font:10px \'DM Mono\',monospace;color:#2A4A2A">'
                                f'Início: {obra.get("data_inicio","—")}</span>'
                                f'<span style="font:10px \'DM Mono\',monospace;color:#2A4A2A">'
                                f'Fim: {obra.get("data_fim","—")}</span>'
                                f'</div>'
                            )
                            maps_url = obra.get("obra_maps","")
                            if maps_url:
                                with ui.element("div").style(
                                    "padding-top:8px;border-top:1px solid #1E301E;margin-top:6px"
                                ):
                                    _action_btn(
                                        "Ver no Maps", "map", "#60A5FA", "rgba(96,165,250,.08)",
                                        lambda u=maps_url: ui.run_javascript(
                                            f'window.open({repr(u)},"_blank","noopener,noreferrer")')
                                    )

            with ui.element("div").style("display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px"):
                for fid, flbl in [
                    ("todas","Todas"),("ativo","Ativo"),
                    ("planejamento","Planej."),("pausado","Pausado"),("concluido","Concluído"),
                ]:
                    c = ui.element("button").classes("mb-chip" + (" active" if fid == "todas" else ""))
                    with c:
                        ui.html(flbl)
                    chip_refs[fid] = c
                    def _set(f=fid):
                        filter_state["v"] = f
                        for k, cr in chip_refs.items():
                            if k == f: cr.classes(add="active")
                            else:       cr.classes(remove="active")
                        _render_obras()
                    c.on("click", _set)

            obras_area = ui.element("div").style("display:flex;flex-direction:column;gap:8px;margin-bottom:4px")
            _render_obras()

            # Links rápidos
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#60A5FA">link</span>'
                'Links Rápidos</div>'
            )
            for icon, color, label, url in _LINKS:
                row = ui.element("div").classes("mb-link-row")
                with row:
                    ui.html(f'<span class="material-icons" style="font-size:20px;color:{color};flex-shrink:0">{icon}</span>')
                    ui.html(f'<span style="font:500 14px \'Inter\',sans-serif;color:#DCE8DC;flex:1">{label}</span>')
                    ui.html('<span class="material-icons" style="font-size:15px;color:#2A4A2A">open_in_new</span>')
                row.on("click", lambda u=url: ui.run_javascript(
                    f"window.open({repr(u)},'_blank','noopener,noreferrer')"))

            # Configurações
            ui.html(
                '<div class="mb-section-title">'
                '<span class="material-icons" style="font-size:11px;color:#8BAA8B">settings</span>'
                'Configurações</div>'
            )
            with ui.element("div").style("display:flex;flex-direction:column;gap:8px;margin-bottom:8px"):
                desktop_row = ui.element("div").classes("mb-link-row")
                with desktop_row:
                    ui.html('<span class="material-icons" style="font-size:20px;color:#60A5FA;flex-shrink:0">computer</span>')
                    with ui.element("div").style("flex:1"):
                        ui.html('<div style="font:500 14px \'Inter\',sans-serif;color:#DCE8DC">Versão Desktop</div>')
                        ui.html('<div style="font:11px \'DM Mono\',monospace;color:#527A52;margin-top:2px">Acesso completo ao hub</div>')
                    ui.html('<span class="material-icons" style="font-size:15px;color:#2A4A2A">open_in_new</span>')
                desktop_row.on("click", lambda: ui.navigate.to("/"))


# ── Página ────────────────────────────────────────────────────────────

@ui.page("/mobile")
def mobile_page():
    if not is_authenticated():
        ui.navigate.to("/login")
        return

    username = current_user_name() or "Usuário"

    ui.dark_mode().enable()
    ui.add_head_html(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, '
        'maximum-scale=1.0, viewport-fit=cover">'
    )
    ui.add_head_html(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800'
        '&family=Inter:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">'
    )
    ui.add_head_html(f"<style>{_CSS}</style>")
    ui.add_body_html(_NAV_JS)

    state = MobileState()
    state.client_field = "nome"

    def _do_logout():
        logout_user()
        ui.navigate.to("/login")

    with ui.element("div").classes("mb-page"):

        # ── Header ────────────────────────────────────────────────────
        with ui.element("div").classes("mb-header"):
            ui.html(
                '<div style="width:38px;height:38px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1.5px solid rgba(74,222,128,.3);'
                'display:flex;align-items:center;justify-content:center;">'
                '<svg width="20" height="20" viewBox="0 0 22 22" fill="none">'
                '<path d="M11 3L19 17H3L11 3Z" fill="rgba(74,222,128,.11)" stroke="#4ADE80"'
                ' stroke-width="1.3" stroke-linejoin="round"/>'
                '<path d="M6 13Q11 9.5 16 13" stroke="rgba(74,222,128,.48)"'
                ' stroke-width="0.85" fill="none" stroke-linecap="round"/>'
                '<circle cx="11" cy="3" r="1.3" fill="#4ADE80"/>'
                '</svg></div>'
            )
            with ui.element("div").style("flex:1;line-height:1"):
                with ui.element("div").style("display:flex;align-items:center;gap:7px"):
                    ui.html('<span style="font:800 15px \'Syne\',sans-serif;color:#DCE8DC">DMC</span>')
                    ui.html(
                        '<span style="font:700 8px \'Syne\',sans-serif;color:#4ADE80;'
                        'letter-spacing:.2em;border-left:1.5px solid rgba(74,222,128,.3);'
                        'padding-left:6px">TOPOGRAFIA</span>'
                    )
                ui.html('<div style="font:10px \'DM Mono\',monospace;color:#527A52;'
                        'letter-spacing:.1em;margin-top:2px">Hub de Serviços</div>')
            with ui.element("div").style(
                "display:flex;align-items:center;gap:7px;padding:5px 11px;border-radius:20px;"
                "background:rgba(74,222,128,.06);border:1px solid rgba(74,222,128,.18);"
            ):
                ui.html('<span class="material-icons" style="font-size:13px;color:#4ADE80">person</span>')
                ui.html(f'<span style="font:600 12px \'DM Mono\',monospace;color:#DCE8DC">'
                        f'{username.split()[0]}</span>')

        # ── Content area ──────────────────────────────────────────────
        state.content_area = ui.element("div").classes("mb-content")

        # ── Bottom nav ────────────────────────────────────────────────
        _TABS = [
            ("home",    "home",        "#4ADE80", "Início"),
            ("files",   "folder",      "#FBBF24", "Arquivos"),
            ("clients", "people",      "#60A5FA", "Clientes"),
            ("campo",   "terrain",     "#C4B5FD", "Campo"),
            ("mais",    "apps",        "#8BAA8B",  "Mais"),
        ]
        with ui.element("div").classes("mb-bottom-nav"):
            for tab_id, tab_icon, tab_color, tab_label in _TABS:
                is_active = tab_id == "home"
                btn = ui.element("button").classes("mb-nav-btn" + (" active" if is_active else ""))
                btn.props(f'data-tab="{tab_id}"')
                btn.style(f"--nav-color:{tab_color}")
                span_color = tab_color if is_active else '#2A4A2A'
                with btn:
                    ui.html(f'<span class="material-icons nb-icon" style="color:{span_color}">{tab_icon}</span>')
                    ui.html(f'<span class="nb-label" style="color:{span_color}">{tab_label}</span>')
                btn.on("click", lambda t=tab_id, c=tab_color: state.switch_tab(t, c))

    # Renderização inicial
    _render_home(state)
