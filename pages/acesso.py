"""Página de Configuração de Acesso — /acesso"""

from nicegui import ui
from services.auth import is_authenticated, current_user_perfil, PERFIS, PERFIL_CORES
from services.acesso import FEATURES, load_access, save_access, has_access
from ui.styles import BOOTSTRAP_CDN, CSS

_PERFIL_ABBR = {
    "DESENVOLVEDOR":           ("DEV",  "code",                 ),
    "ADMINISTRADOR":           ("ADM",  "admin_panel_settings", ),
    "FUNCIONÁRIO PRIORITÁRIO": ("PRI",  "star",                 ),
    "FUNCIONÁRIO":             ("FUNC", "person",               ),
    "FUNCIONÁRIO CAMPO":       ("CAM",  "construction",         ),
}

_CAT_META = {
    "Sistema":        ("lock",                    "#F87171"),
    "Agenda":         ("calendar_month",          "#FBBF24"),
    "Clientes":       ("people",                  "#60A5FA"),
    "Obras":          ("engineering",             "#34D399"),
    "Financeiro":     ("account_balance_wallet",  "#4ADE80"),
    "Administrativo": ("admin_panel_settings",    "#C4B5FD"),
    "Arquivos":       ("folder_open",             "#F97316"),
}

_CSS = """
html, body, .nicegui-content {
  height: 100% !important; margin: 0 !important; padding: 0 !important;
}
.ac-page {
  min-height: 100vh; width: 100%;
  background: var(--dmc-bg);
  display: flex; flex-direction: column;
}
/* ── Header ── */
.ac-header {
  position: sticky; top: 0; z-index: 100;
  background: var(--dmc-header-bg); backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--dmc-b1);
  display: flex; align-items: center; gap: 14px;
  padding: 0 32px; height: 60px; flex-shrink: 0;
}
/* ── Layout principal (sidebar + conteúdo) ── */
.ac-layout {
  flex: 1;
  display: flex;
  min-height: 0;
}
/* ── Sidebar de navegação ── */
.ac-sidenav {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--dmc-b1);
  padding: 20px 0 40px;
  position: sticky;
  top: 60px;
  height: calc(100vh - 60px);
  overflow-y: auto;
  background: var(--dmc-bg);
}
.ac-sidenav-label {
  padding: 6px 18px 8px;
  font: 600 9px var(--dmc-mono);
  color: var(--dmc-muted2);
  letter-spacing: .2em;
  text-transform: uppercase;
  opacity: .7;
}
.ac-nav-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 9px 18px;
  background: transparent; border: none; cursor: pointer;
  font: 13px var(--dmc-fm); color: var(--dmc-muted2);
  text-align: left; transition: all .15s;
  border-left: 2px solid transparent;
}
.ac-nav-item:hover { background: rgba(0,0,0,.04); color: var(--dmc-text); }
.ac-nav-item.active {
  color: #C4B5FD;
  background: rgba(196,181,253,.07);
  border-left-color: #C4B5FD;
  font-weight: 600;
}
/* ── Área de conteúdo ── */
.ac-content {
  flex: 1; min-width: 0;
  padding: 28px 24px 100px;
  box-sizing: border-box;
  overflow-y: auto;
}
/* ── Tabela grid ── */
.ac-table {
  background: var(--dmc-bg2);
  border: 1px solid var(--dmc-b1);
  border-radius: 16px;
  overflow: hidden;
}
.ac-head-row, .ac-feat-row {
  display: grid;
  grid-template-columns: minmax(200px,1fr) repeat(5, 100px);
  align-items: center;
}
.ac-head-row {
  background: var(--dmc-bg3);
  border-bottom: 2px solid var(--dmc-b1);
  position: sticky; top: 0; z-index: 20;
}
.ac-head-cell {
  padding: 14px 8px;
  display: flex; flex-direction: column;
  align-items: center; gap: 5px;
  text-align: center;
}
.ac-head-feat {
  padding-left: 20px;
  align-items: flex-start;
  font: 600 10px var(--dmc-mono);
  color: var(--dmc-muted2);
  letter-spacing: .15em;
  text-transform: uppercase;
}
.ac-cat-row {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 20px;
  background: var(--dmc-bg3);
  border-top: 1px solid var(--dmc-b1);
  border-bottom: 1px solid var(--dmc-b1);
  font: 600 10px var(--dmc-mono);
  color: var(--dmc-muted2);
  letter-spacing: .14em;
  text-transform: uppercase;
}
.ac-feat-row {
  border-bottom: 1px solid var(--dmc-b1);
  transition: background .12s;
}
.ac-feat-row:last-child { border-bottom: none; }
.ac-feat-row:hover { background: rgba(0,0,0,.03); }
.ac-feat-name {
  padding: 11px 12px 11px 20px;
  font: 13px var(--dmc-fm);
  color: var(--dmc-text);
  line-height: 1.35;
}
.ac-switch-cell {
  display: flex; align-items: center; justify-content: center;
  padding: 8px 4px;
}
.ac-switch-cell .q-toggle__inner { font-size: 38px !important; }
.ac-switch-cell .q-toggle__inner--truthy .q-toggle__thumb:before { background: #4ADE80 !important; }
.ac-switch-cell .q-toggle__track { background: rgba(74,222,128,.25) !important; }
/* ── Footer fixo ── */
.ac-footer {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 90;
  background: var(--dmc-header-bg); backdrop-filter: blur(20px);
  border-top: 1px solid var(--dmc-b1);
  padding: 12px 32px;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
"""


@ui.page("/acesso")
def acesso_page():
    if not is_authenticated():
        ui.navigate.to("/login")
        return
    if not has_access(current_user_perfil(), "adm_config_acesso"):
        ui.navigate.to("/")
        return

    ui.dark_mode().enable()
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(f"<style>{_CSS}</style>")
    ui.add_head_html("<script>setTimeout(function(){var t=localStorage.getItem('dmc-theme')||'dark';if(window.Quasar)window.Quasar.Dark.set(t==='dark');},300);</script>")

    config: dict[str, dict[str, bool]] = load_access()

    cats: list[tuple[str, list[tuple[str, str]]]] = []
    _seen: dict[str, list] = {}
    for fid, label, cat in FEATURES:
        if cat not in _seen:
            _seen[cat] = []
            cats.append((cat, _seen[cat]))
        _seen[cat].append((fid, label))

    with ui.element("div").classes("ac-page"):

        # ── Header ───────────────────────────────────────────────────
        with ui.element("div").classes("ac-header"):
            ui.html(
                '<div style="width:36px;height:36px;border-radius:10px;flex-shrink:0;'
                'background:rgba(196,181,253,.08);border:1px solid rgba(196,181,253,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:18px;color:#C4B5FD">shield</span></div>'
            )
            with ui.element("div").style("flex:1;min-width:0"):
                ui.html(
                    '<div style="font:700 15px \'Syne\',sans-serif;color:var(--dmc-text)">'
                    'Administrativo</div>'
                )
                ui.html(
                    '<div style="font:10px \'Inter\',sans-serif;color:var(--dmc-muted2);'
                    'letter-spacing:.1em;text-transform:uppercase">'
                    'Gestão de contas e permissões · DMC Topografia</div>'
                )
            ui.button(icon="close", on_click=lambda: ui.run_javascript("window.close()")).props(
                'flat round dense'
            ).style("color:var(--dmc-muted)")

        # ── Layout: sidebar + conteúdo ────────────────────────────────
        with ui.element("div").classes("ac-layout"):

            # ── Sidebar de navegação ──────────────────────────────────
            with ui.element("div").classes("ac-sidenav"):
                ui.html('<div class="ac-sidenav-label">Administrativo</div>')

                # Gestão de Contas
                b_contas = ui.element("button").classes("ac-nav-item")
                with b_contas:
                    ui.html('<span class="material-icons" style="font-size:16px;color:#4ADE80;flex-shrink:0">manage_accounts</span>')
                    ui.html("<span>Gestão de Contas</span>")
                b_contas.on("click", lambda: ui.navigate.to("/contas"))

                # Configuração de Acesso (ativo)
                with ui.element("button").classes("ac-nav-item active"):
                    ui.html('<span class="material-icons" style="font-size:16px;color:#C4B5FD;flex-shrink:0">security</span>')
                    ui.html("<span>Configuração de Acesso</span>")

            # ── Conteúdo: matriz de permissões ────────────────────────
            with ui.element("div").classes("ac-content"):

                ui.html(
                    '<div style="display:flex;align-items:center;gap:10px;padding:12px 18px;'
                    'border-radius:12px;margin-bottom:20px;'
                    'background:rgba(196,181,253,.06);border:1px solid rgba(196,181,253,.18);">'
                    '<span class="material-icons" style="font-size:15px;color:#C4B5FD;flex-shrink:0">info</span>'
                    '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">'
                    'Ative ou desative cada funcionalidade por perfil. '
                    'Alterações entram em vigor no próximo acesso do usuário.'
                    '</span></div>'
                )

                with ui.element("div").classes("ac-table"):

                    # Cabeçalho de perfis
                    with ui.element("div").classes("ac-head-row"):
                        ui.html('<div class="ac-head-cell ac-head-feat">Funcionalidade</div>')
                        for p in PERFIS:
                            abbr, icon = _PERFIL_ABBR[p]
                            fg, bg, br = PERFIL_CORES.get(p, ("#4ADE80", "rgba(74,222,128,.1)", "rgba(74,222,128,.25)"))
                            with ui.element("div").classes("ac-head-cell"):
                                ui.html(
                                    f'<div style="width:32px;height:32px;border-radius:8px;'
                                    f'background:{bg};border:1px solid {br};'
                                    f'display:flex;align-items:center;justify-content:center;">'
                                    f'<span class="material-icons" style="font-size:16px;color:{fg}">{icon}</span></div>'
                                )
                                ui.html(f'<span style="font:700 9px var(--dmc-mono);color:{fg};letter-spacing:.08em">{abbr}</span>')
                                ui.html(f'<span style="font:8px var(--dmc-mono);color:var(--dmc-muted2);text-align:center;line-height:1.3;max-width:90px">{p}</span>')

                    # Linhas por categoria e feature
                    for cat, feats in cats:
                        cat_icon, cat_color = _CAT_META.get(cat, ("folder", "#60A5FA"))
                        ui.html(
                            f'<div class="ac-cat-row">'
                            f'<span class="material-icons" style="font-size:13px;color:{cat_color}">{cat_icon}</span>'
                            f'{cat}</div>'
                        )
                        for fid, label in feats:
                            with ui.element("div").classes("ac-feat-row"):
                                ui.html(f'<div class="ac-feat-name">{label}</div>')
                                for p in PERFIS:
                                    fg, _, _ = PERFIL_CORES.get(p, ("#4ADE80", "", ""))
                                    with ui.element("div").classes("ac-switch-cell"):
                                        sw = ui.switch(
                                            value=config.get(p, {}).get(fid, True)
                                        ).props('color="green" dense keep-color').style("margin:0")
                                        def _on_change(e, _p=p, _fid=fid):
                                            config.setdefault(_p, {})[_fid] = bool(e.value)
                                        sw.on_value_change(_on_change)

    # ── Footer fixo ───────────────────────────────────────────────────
    with ui.element("div").classes("ac-footer"):
        status = ui.html(
            '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">'
            'Ajuste as permissões e clique em Salvar.</span>'
        )

        async def _salvar():
            save_access(config)
            status.set_content(
                '<span style="font:12px var(--dmc-fm);color:#4ADE80">'
                '✓ Configurações salvas com sucesso!</span>'
            )
            ui.notify("✓ Permissões atualizadas!", type="positive")

        ui.button("Salvar configurações", icon="save", on_click=_salvar).props(
            'unelevated no-caps'
        ).classes('dmc-btn dmc-btn-primary').style("padding:0 28px;height:40px")
