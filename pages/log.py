"""Página de Log de Atividades — /log"""

from nicegui import app as _lgapp, ui

from services.auth import current_user_label, current_user_perfil, is_authenticated, logout_user, mark_active, current_user_name
from services.acesso import has_access
from services.log import load_logs, ACOES, ENTIDADES
from ui.styles import BOOTSTRAP_CDN, CSS, UTILS_JS

_ACAO_CFG = {
    "criar":    ("#4ADE80", "rgba(74,222,128,.12)",  "add_circle",                "Criar"),
    "editar":   ("#FBBF24", "rgba(251,191,36,.12)",  "edit",                      "Editar"),
    "excluir":  ("#F87171", "rgba(248,113,113,.12)", "delete_forever",            "Excluir"),
    "renomear": ("#60A5FA", "rgba(96,165,250,.12)",  "drive_file_rename_outline", "Renomear"),
    "upload":   ("#A78BFA", "rgba(167,139,250,.12)", "cloud_upload",              "Upload"),
    "pasta":    ("#34D399", "rgba(52,211,153,.12)",  "create_new_folder",         "Pasta"),
}

_ENT_LABELS = {
    "cliente": ("person",            "Cliente"),
    "tecnico": ("engineering",       "Técnico"),
    "obra":    ("construction",      "Obra"),
    "arquivo": ("insert_drive_file", "Arquivo"),
    "pasta":   ("folder",            "Pasta"),
    "ponto":   ("fingerprint",       "Ponto"),
}

_PAGE_CSS = """
<style>
html, body, .nicegui-content,
.q-layout, .q-page-container, .q-page {
  margin: 0 !important; padding: 0 !important;
  width: 100% !important; max-width: 100% !important;
  box-sizing: border-box !important;
}

.lg-page {
  width: 100%; min-height: 100vh;
  background: var(--dmc-bg);
  display: flex; flex-direction: column;
}

/* topbar */
.lg-topbar {
  position: sticky; top: 0; z-index: 100;
  width: 100%; box-sizing: border-box;
  height: 60px; flex-shrink: 0;
  background: var(--dmc-bg2);
  border-bottom: 1px solid var(--dmc-b1);
  backdrop-filter: blur(16px);
  display: flex; align-items: center;
  padding: 0 28px; gap: 14px;
}
.lg-title {
  display: flex; align-items: center; gap: 8px;
  font: 700 15px var(--dmc-fd); color: var(--dmc-text);
  white-space: nowrap;
}
.lg-title .ico { font-size: 20px !important; color: #60A5FA; }
.lg-sep    { width: 1px; height: 28px; background: var(--dmc-b1); flex-shrink: 0; }
.lg-spacer { flex: 1; }
.lg-stat {
  font: 12px var(--dmc-mono); color: var(--dmc-muted2);
  background: rgba(255,255,255,.04); border: 1px solid var(--dmc-b1);
  border-radius: 6px; padding: 3px 10px; white-space: nowrap;
}

/* filtros */
.lg-filters {
  width: 100%; box-sizing: border-box;
  background: var(--dmc-bg2);
  border-bottom: 1px solid var(--dmc-b1);
  padding: 12px 28px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 10px;
}
.lg-search {
  display: flex; align-items: center; gap: 8px;
  background: var(--dmc-bg3); border: 1px solid var(--dmc-b1);
  border-radius: 8px; padding: 0 12px; height: 38px;
  max-width: 440px;
}
.lg-search input {
  flex: 1; background: transparent; border: none; outline: none;
  font: 13px var(--dmc-fm); color: var(--dmc-text);
}
.lg-pills { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.lg-pill-label {
  font: 10px var(--dmc-mono); color: var(--dmc-muted2);
  letter-spacing: .1em; text-transform: uppercase;
  margin-right: 4px; flex-shrink: 0;
}
.lg-pill {
  font: 500 11px var(--dmc-mono); padding: 3px 11px;
  border-radius: 6px; border: 1px solid var(--dmc-b1);
  background: var(--dmc-bg3); color: var(--dmc-muted2);
  cursor: pointer; text-transform: uppercase; letter-spacing: .04em;
  transition: all .15s; white-space: nowrap;
}
.lg-pill:hover { border-color: var(--dmc-b2); color: var(--dmc-text); }
.lg-pill.active { font-weight: 700; }

/* corpo */
.lg-body {
  flex: 1; padding: 24px 28px;
  width: 100%; box-sizing: border-box;
}

/* tabela */
.lg-card {
  background: var(--dmc-bg2);
  border: 1px solid var(--dmc-b1);
  border-radius: 14px;
  overflow-x: auto; overflow-y: hidden;
}
.lg-table {
  border-collapse: collapse;
  width: 100%; min-width: 820px;
}
.lg-table thead tr { border-bottom: 1px solid var(--dmc-b1); }
.lg-table thead th {
  padding: 10px 14px;
  font: 600 10px var(--dmc-mono); color: var(--dmc-muted2);
  text-transform: uppercase; letter-spacing: .06em;
  white-space: nowrap; text-align: left;
}
.lg-table tbody tr {
  border-bottom: 1px solid var(--dmc-b1); transition: background .1s;
}
.lg-table tbody tr:last-child { border-bottom: none; }
.lg-table tbody tr:hover { background: rgba(255,255,255,.025); }
.lg-table tbody td { padding: 9px 14px; vertical-align: middle; }

.lg-badge {
  display: inline-flex; align-items: center; gap: 5px;
  font: 600 10px var(--dmc-mono); padding: 2px 8px;
  border-radius: 5px; text-transform: uppercase; letter-spacing: .06em;
  white-space: nowrap;
}
.lg-ent {
  display: inline-flex; align-items: center; gap: 5px;
  font: 12px var(--dmc-fm); color: var(--dmc-muted2);
  white-space: nowrap;
}
.lg-name {
  font: 500 13px var(--dmc-fm); color: var(--dmc-text);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  max-width: 260px; display: block;
}
.lg-user  { font: 12px var(--dmc-mono); color: var(--dmc-muted); white-space: nowrap; }
.lg-perfil {
  font: 9px var(--dmc-mono); padding: 1px 6px; border-radius: 3px;
  background: rgba(255,255,255,.05); border: 1px solid var(--dmc-b1);
  color: var(--dmc-muted2); white-space: nowrap;
}
.lg-ts    { font: 11px var(--dmc-mono); color: var(--dmc-muted); white-space: nowrap; }
.lg-detalhe {
  font: 11px var(--dmc-mono); color: var(--dmc-muted2);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  max-width: 200px; display: block;
}

/* vazio */
.lg-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 80px 20px; gap: 12px; color: var(--dmc-muted2);
}

@media (max-width: 860px) {
  .lg-topbar { padding: 0 14px; }
  .lg-filters { padding: 10px 14px; }
  .lg-body { padding: 16px 14px; }
  .hide-sm { display: none !important; }
}
</style>
"""


@ui.page("/log")
def log_page():
    if not is_authenticated():
        ui.navigate.to("/login")
        return
    if not has_access(current_user_perfil() or "", "adm_log"):
        ui.navigate.to("/")
        return

    ui.dark_mode().enable()
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(UTILS_JS)
    ui.add_head_html(_PAGE_CSS)

    _lg_nome  = current_user_name()
    _lg_email = _lgapp.storage.user.get("dmc_user_email", "")
    mark_active(_lg_email, _lg_nome)

    def _logout():
        logout_user()
        ui.navigate.to("/login")

    _auto_logout_btn = ui.element("button").props('id="dmc-auto-logout"').style(
        "display:none;position:absolute;pointer-events:none"
    )
    _auto_logout_btn.on("click", _logout)
    ui.timer(60, lambda: mark_active(_lg_email, _lg_nome))

    _state = {"busca": "", "acao": "todos", "entidade": "todos"}

    with ui.element("div").classes("lg-page"):

        # ── Topbar ────────────────────────────────────────────────────
        with ui.element("div").classes("lg-topbar"):
            ui.html(
                '<div class="lg-title">'
                '<span class="material-icons ico">history</span>'
                'Log de Atividades'
                '</div>'
            )
            ui.html('<div class="lg-sep"></div>')
            stat_label = ui.html('<div class="lg-stat">—</div>')
            ui.html('<div class="lg-spacer"></div>')
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                "flat round dense"
            ).style("color:var(--dmc-muted)")

        # ── Filtros ───────────────────────────────────────────────────
        with ui.element("div").classes("lg-filters"):
            with ui.element("div").classes("lg-search"):
                ui.html('<span class="material-icons" style="font-size:16px;color:var(--dmc-muted2)">search</span>')
                busca_inp = ui.input(placeholder="Buscar por nome, usuário ou caminho…").props(
                    "borderless dense"
                ).style("flex:1;font:13px var(--dmc-fm)")

            acao_pills    = ui.element("div").classes("lg-pills")
            entidade_pills = ui.element("div").classes("lg-pills")

        # ── Conteúdo ──────────────────────────────────────────────────
        with ui.element("div").classes("lg-body"):
            content = ui.element("div")

        # ── Renderização ──────────────────────────────────────────────
        def _render():
            busca    = _state["busca"].lower().strip()
            fil_acao = _state["acao"]
            fil_ent  = _state["entidade"]

            entries = load_logs(limit=500)
            if fil_acao != "todos":
                entries = [e for e in entries if e.get("acao") == fil_acao]
            if fil_ent != "todos":
                entries = [e for e in entries if e.get("entidade") == fil_ent]
            if busca:
                entries = [
                    e for e in entries
                    if busca in (e.get("nome") or "").lower()
                    or busca in (e.get("usuario") or "").lower()
                    or busca in (e.get("caminho") or "").lower()
                    or busca in (e.get("detalhe") or "").lower()
                ]

            n = len(entries)
            stat_label.set_content(
                f'<div class="lg-stat">{n} registro{"s" if n != 1 else ""}</div>'
            )

            content.clear()
            with content:
                if not entries:
                    with ui.element("div").classes("lg-empty"):
                        ui.html('<span class="material-icons" style="font-size:52px;color:var(--dmc-b2)">manage_search</span>')
                        ui.html('<span style="font:13px var(--dmc-fm)">Nenhum registro encontrado.</span>')
                    return

                with ui.element("div").classes("lg-card"):
                    rows_html = ""
                    for e in entries:
                        acao     = e.get("acao", "")
                        entidade = e.get("entidade", "")
                        cor, bg, ic, lbl = _ACAO_CFG.get(
                            acao, ("#94A3B8", "rgba(148,163,184,.12)", "info", acao or "?")
                        )
                        ent_icon, ent_lbl = _ENT_LABELS.get(entidade, ("help_outline", entidade or "—"))
                        extra = " · ".join(filter(None, [e.get("caminho",""), e.get("detalhe","")]))
                        perfil_str = e.get("perfil","")
                        perfil_badge = (
                            f'<span class="lg-perfil">{perfil_str}</span>'
                            if perfil_str and perfil_str != "—" else ""
                        )

                        rows_html += (
                            f'<tr>'
                            f'<td>'
                            f'<span class="lg-badge" style="background:{bg};color:{cor};border:1px solid {cor}33">'
                            f'<span class="material-icons" style="font-size:13px">{ic}</span>{lbl}'
                            f'</span>'
                            f'</td>'
                            f'<td>'
                            f'<span class="lg-ent">'
                            f'<span class="material-icons" style="font-size:14px">{ent_icon}</span>{ent_lbl}'
                            f'</span>'
                            f'</td>'
                            f'<td style="max-width:280px">'
                            f'<span class="lg-name" title="{e.get("nome","")}">{e.get("nome") or "—"}</span>'
                            f'</td>'
                            f'<td>'
                            f'<div style="display:flex;flex-direction:column;gap:3px">'
                            f'<span class="lg-user">{e.get("usuario") or "—"}</span>'
                            f'{perfil_badge}'
                            f'</div>'
                            f'</td>'
                            f'<td><span class="lg-ts">{e.get("data","")} {e.get("hora","")}</span></td>'
                            f'<td style="max-width:220px">'
                            f'<span class="lg-detalhe" title="{extra}">{extra or "—"}</span>'
                            f'</td>'
                            f'</tr>'
                        )

                    ui.html(
                        '<table class="lg-table">'
                        '<thead><tr>'
                        '<th style="width:110px">Ação</th>'
                        '<th style="width:100px">Entidade</th>'
                        '<th>Nome</th>'
                        '<th style="width:140px">Usuário</th>'
                        '<th style="width:150px">Data / Hora</th>'
                        '<th style="width:220px">Detalhe</th>'
                        '</tr></thead>'
                        f'<tbody>{rows_html}</tbody>'
                        '</table>'
                    )

        def _build_pills():
            acao_pills.clear()
            entidade_pills.clear()

            with acao_pills:
                ui.html('<span class="lg-pill-label">Ação</span>')
                for key, label in [("todos", "Todas")] + [(k, v[3]) for k, v in _ACAO_CFG.items()]:
                    active = _state["acao"] == key
                    cor    = _ACAO_CFG[key][0] if key != "todos" else "#60A5FA"
                    style  = (
                        f"border-color:{cor};background:{cor}18;color:{cor};font-weight:700"
                        if active else ""
                    )
                    b = ui.element("button").classes(
                        "lg-pill active" if active else "lg-pill"
                    ).style(style)
                    with b:
                        ui.html(f"<span>{label}</span>")
                    b.on("click", lambda k=key: [_state.update({"acao": k}), _build_pills(), _render()])

            with entidade_pills:
                ui.html('<span class="lg-pill-label">Entidade</span>')
                all_ents = [("todos", "help_outline", "Todos")] + [
                    (k, ic, lb) for k, (ic, lb) in _ENT_LABELS.items()
                ]
                for key, icon, label in all_ents:
                    active = _state["entidade"] == key
                    style  = (
                        "border-color:#94A3B8;background:rgba(148,163,184,.14);"
                        "color:#94A3B8;font-weight:700"
                        if active else ""
                    )
                    b = ui.element("button").classes(
                        "lg-pill active" if active else "lg-pill"
                    ).style(
                        f"display:inline-flex;align-items:center;gap:4px;{style}"
                    )
                    with b:
                        ui.html(f'<span class="material-icons" style="font-size:12px">{icon}</span>')
                        ui.html(f"<span>{label}</span>")
                    b.on("click", lambda k=key: [_state.update({"entidade": k}), _build_pills(), _render()])

        busca_inp.on("input", lambda e: [_state.update({"busca": e.value or ""}), _render()])

        _build_pills()
        _render()
