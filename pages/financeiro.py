"""Página Financeiro — /financeiro  (NFS-e · A Pagar · A Receber)"""

import base64
from datetime import datetime
from pathlib import Path

from nicegui import app as _fapp, ui

from services.auth import (
    current_user_label, current_user_name, current_user_perfil,
    is_authenticated, logout_user, mark_active,
)
from services.acesso import has_access
from services.nfse import list_nfse, load_config, _DEPS_OK
from services.financeiro import (
    load_contas_pagar, load_contas_receber, resumo_pagar, resumo_receber,
)
from ui.styles import BOOTSTRAP_CDN, CSS, UTILS_JS

_PAGE_CSS = """
<style>
html, body, .nicegui-content,
.q-layout, .q-page-container, .q-page {
  margin: 0 !important; padding: 0 !important;
  width: 100% !important; max-width: 100% !important;
  box-sizing: border-box !important;
}
.fi-page {
  width: 100%; min-height: 100vh;
  background: var(--dmc-bg);
  display: flex; flex-direction: column;
}
.fi-topbar {
  position: sticky; top: 0; z-index: 100;
  width: 100%; box-sizing: border-box;
  height: 60px; flex-shrink: 0;
  background: var(--dmc-bg2);
  border-bottom: 1px solid var(--dmc-b1);
  backdrop-filter: blur(16px);
  display: flex; align-items: center;
  padding: 0 28px; gap: 14px;
}
.fi-title {
  display: flex; align-items: center; gap: 8px;
  font: 700 15px var(--dmc-fd); color: var(--dmc-text);
  white-space: nowrap;
}
.fi-title .ico { font-size: 20px !important; color: #4ADE80; }
.fi-sep    { width: 1px; height: 28px; background: var(--dmc-b1); flex-shrink: 0; }
.fi-spacer { flex: 1; }
.fi-stat {
  font: 12px var(--dmc-mono); color: var(--dmc-muted2);
  background: rgba(255,255,255,.04); border: 1px solid var(--dmc-b1);
  border-radius: 6px; padding: 3px 10px; white-space: nowrap;
}
.fi-env-badge {
  font: 700 10px var(--dmc-mono); padding: 3px 10px; border-radius: 5px;
  letter-spacing: .08em; text-transform: uppercase; white-space: nowrap;
}

/* ── Tabs ── */
.fi-tabs {
  display: flex; gap: 0;
  background: var(--dmc-bg2);
  border-bottom: 1px solid var(--dmc-b1);
  padding: 0 28px; flex-shrink: 0;
}
.fi-tab {
  padding: 12px 20px;
  font: 600 12px var(--dmc-mono); letter-spacing:.04em;
  color: var(--dmc-muted2); cursor: pointer;
  border-bottom: 2.5px solid transparent;
  display: flex; align-items: center; gap: 7px;
  transition: color .15s, border-color .15s;
  white-space: nowrap;
}
.fi-tab:hover { color: var(--dmc-text); }
.fi-tab.active { color: var(--dmc-text); border-bottom-color: var(--fi-tab-color, #4ADE80); }

.fi-actions {
  width: 100%; box-sizing: border-box;
  background: var(--dmc-bg2);
  border-bottom: 1px solid var(--dmc-b1);
  padding: 10px 28px;
  display: flex; align-items: center; gap: 10px; flex-shrink: 0;
  flex-wrap: wrap;
}
.fi-body {
  flex: 1; padding: 24px 28px;
  width: 100%; box-sizing: border-box;
}
.fi-stats {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px; margin-bottom: 24px;
}
.fi-stat-card {
  background: var(--dmc-bg2); border: 1px solid var(--dmc-b1);
  border-radius: 12px; padding: 16px 20px;
}
.fi-stat-card .lbl {
  font: 10px var(--dmc-mono); color: var(--dmc-muted2);
  letter-spacing: .1em; text-transform: uppercase; margin-bottom: 6px;
}
.fi-stat-card .val {
  font: 700 22px var(--dmc-fd); color: var(--dmc-text);
}
.fi-stat-card .sub {
  font: 11px var(--dmc-fm); color: var(--dmc-muted2); margin-top: 2px;
}
.fi-card {
  background: var(--dmc-bg2); border: 1px solid var(--dmc-b1);
  border-radius: 14px; overflow-x: auto;
}
.fi-table {
  border-collapse: collapse; width: 100%; min-width: 700px;
}
.fi-table thead tr { border-bottom: 1px solid var(--dmc-b1); }
.fi-table thead th {
  padding: 10px 14px;
  font: 600 10px var(--dmc-mono); color: var(--dmc-muted2);
  text-transform: uppercase; letter-spacing: .06em;
  white-space: nowrap; text-align: left;
}
.fi-table tbody tr {
  border-bottom: 1px solid var(--dmc-b1); transition: background .1s;
}
.fi-table tbody tr:last-child { border-bottom: none; }
.fi-table tbody tr:hover { background: rgba(255,255,255,.025); }
.fi-table tbody td { padding: 9px 14px; vertical-align: middle; }
.fi-num   { font: 600 13px var(--dmc-mono); color: #4ADE80; }
.fi-toma  { font: 500 13px var(--dmc-fm); color: var(--dmc-text); }
.fi-desc  {
  font: 12px var(--dmc-fm); color: var(--dmc-muted);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  max-width: 220px; display: block;
}
.fi-val   { font: 600 13px var(--dmc-mono); color: #FBBF24; }
.fi-val-r { font: 600 13px var(--dmc-mono); color: #4ADE80; }
.fi-val-p { font: 600 13px var(--dmc-mono); color: #F87171; }
.fi-ts    { font: 11px var(--dmc-mono); color: var(--dmc-muted); white-space: nowrap; }
.fi-empty {
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 80px 20px; gap: 12px; color: var(--dmc-muted2);
}
.fi-act-btn {
  width: 28px; height: 28px; border-radius: 6px; cursor: pointer;
  background: transparent; border: 1px solid var(--dmc-b1);
  display: inline-flex; align-items: center; justify-content: center;
  color: var(--dmc-muted2); transition: all .15s; flex-shrink: 0;
}
.fi-act-btn:hover { background: rgba(255,255,255,.06); color: var(--dmc-text); }
.fi-badge {
  font: 700 9px var(--dmc-mono); padding: 2px 8px;
  border-radius: 4px; letter-spacing: .06em; white-space: nowrap;
}
.fi-inline-stat {
  display: flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,.04); border: 1px solid var(--dmc-b1);
  border-radius: 8px; padding: 4px 12px; white-space: nowrap; flex-shrink: 0;
}
.fi-inline-stat .lbl {
  font: 10px var(--dmc-mono); color: var(--dmc-muted2);
  text-transform: uppercase; letter-spacing: .06em;
}
.fi-inline-stat .val { font: 600 13px var(--dmc-mono); }
.fi-progress {
  height: 4px; border-radius: 2px;
  background: rgba(255,255,255,.06);
  overflow: hidden; margin-top: 4px; min-width: 80px;
}
.fi-progress-bar { height: 100%; border-radius: 2px; transition: width .3s; }
@media (max-width: 860px) {
  .fi-topbar, .fi-tabs, .fi-actions, .fi-body { padding-left: 14px; padding-right: 14px; }
  .hide-sm { display: none !important; }
  .fi-tab { padding: 10px 12px; }
}
</style>
"""

# ── Status helpers ─────────────────────────────────────────────────────────

_STATUS_PAGAR = {
    "pendente":  ("#FBBF24", "rgba(251,191,36,.1)"),
    "pago":      ("#4ADE80", "rgba(74,222,128,.1)"),
    "cancelado": ("#8BAA8B", "rgba(139,170,139,.08)"),
}
_STATUS_RECEBER = {
    "aberto":    ("#60A5FA", "rgba(96,165,250,.1)"),
    "parcial":   ("#FBBF24", "rgba(251,191,36,.1)"),
    "quitado":   ("#4ADE80", "rgba(74,222,128,.1)"),
    "cancelado": ("#8BAA8B", "rgba(139,170,139,.08)"),
}

def _fmt_brl(v: float) -> str:
    return f'R$ {v:,.2f}'.replace(',','X').replace('.', ',').replace('X','.')

def _badge(label: str, color: str, bg: str) -> str:
    return (f'<span class="fi-badge" style="background:{bg};'
            f'color:{color};border:1px solid {color}44">{label.upper()}</span>')


@ui.page("/financeiro")
def financeiro_page():
    if not is_authenticated():
        ui.navigate.to("/login")
        return
    if not has_access(current_user_perfil(), "fi_ver"):
        ui.navigate.to("/")
        return

    ui.dark_mode().enable()
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(UTILS_JS)
    ui.add_head_html(_PAGE_CSS)

    _fi_nome   = current_user_name()
    _fi_email  = _fapp.storage.user.get("dmc_user_email", "")
    _fi_perfil = current_user_perfil()
    mark_active(_fi_email, _fi_nome, _fi_perfil)

    def _logout():
        logout_user()
        ui.navigate.to("/login")

    _auto_logout_btn = ui.element("button").props('id="dmc-auto-logout"').style(
        "display:none;position:absolute;pointer-events:none"
    )
    _auto_logout_btn.on("click", _logout)
    ui.timer(60, lambda: mark_active(_fi_email, _fi_nome, _fi_perfil))

    from ui.financeiro_dialogs import (
        emitir_nfse_dialog, config_nfse_dialog, ver_nfse_dialog,
        relatorio_financeiro_dialog, empresa_dialog, certificado_dialog,
        nova_conta_pagar_dialog, nova_conta_receber_dialog,
        registrar_pagamento_dialog, categorias_pagar_dialog,
        lixeira_financeiro_dialog,
    )

    cfg = load_config()
    _cfg_ref: dict = {"cfg": cfg}
    _tab_ref: dict = {"tab": "nfse"}

    with ui.element("div").classes("fi-page"):

        # ── Topbar ─────────────────────────────────────────────────────
        with ui.element("div").classes("fi-topbar"):
            ui.html(
                '<div class="fi-title">'
                '<span class="material-icons ico">account_balance_wallet</span>'
                'Financeiro'
                '</div>'
            )
            ui.html('<div class="fi-sep"></div>')

            env       = cfg.get("ambiente", "homologacao")
            env_color = "#FBBF24" if env == "homologacao" else "#4ADE80"
            env_label = "HOMOLOGAÇÃO" if env == "homologacao" else "PRODUÇÃO"

            stat_nfse = ui.html('<div class="fi-stat">—</div>')

            ui.html(
                f'<span class="fi-env-badge" '
                f'style="background:{env_color}18;border:1px solid {env_color}44;'
                f'color:{env_color}">{env_label}</span>'
            )
            ui.html('<div class="fi-spacer"></div>')

            ui.button(
                "Empresa", icon="business",
                on_click=lambda: empresa_dialog(on_save=_refresh_cfg),
            ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary").style(
                "color:#60A5FA;border-color:rgba(96,165,250,.3)"
            )

            _cert_ok = bool(cfg.get("cert_path") and Path(cfg.get("cert_path","")).exists())
            _cert_dot_color = "#4ADE80" if _cert_ok else "#FBBF24"
            with ui.element("div").style("position:relative;flex-shrink:0"):
                ui.button(
                    "Certificado", icon="verified_user",
                    on_click=lambda: certificado_dialog(on_save=_refresh_cfg),
                ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary").style(
                    "color:#A78BFA;border-color:rgba(167,139,250,.3)"
                )
                _cert_dot = ui.html(
                    f'<div style="position:absolute;top:5px;right:5px;'
                    f'width:7px;height:7px;border-radius:50%;pointer-events:none;'
                    f'background:{_cert_dot_color};box-shadow:0 0 5px {_cert_dot_color}88"></div>'
                )

            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                "flat round dense"
            ).style("color:var(--dmc-muted)")

        # ── Abas ───────────────────────────────────────────────────────
        with ui.element("div").classes("fi-tabs"):
            _TABS = [
                ("nfse",    "receipt_long",     "#4ADE80", "NFS-e"),
                ("pagar",   "arrow_circle_down","#F87171", "Contas a Pagar"),
                ("receber", "arrow_circle_up",  "#4ADE80", "Contas a Receber"),
            ]
            tab_btns: dict = {}
            for tid, ticon, tcolor, tlabel in _TABS:
                is_active = tid == "nfse"
                btn = ui.element("div").classes("fi-tab" + (" active" if is_active else "")).style(
                    f"--fi-tab-color:{tcolor}"
                )
                with btn:
                    ui.html(
                        f'<span class="material-icons" style="font-size:16px;color:{tcolor}">'
                        f'{ticon}</span>'
                        f'<span>{tlabel}</span>'
                    )
                tab_btns[tid] = btn
                btn.on("click", lambda t=tid: _switch_tab(t))

        # ── Barra de ações ──────────────────────────────────────────────
        actions_box = ui.element("div").classes("fi-actions")
        stats_box   = ui.element("div").style(
            "display:flex;align-items:center;gap:8px;flex-shrink:0;flex-wrap:wrap"
        )

        # ── Corpo ───────────────────────────────────────────────────────
        with ui.element("div").classes("fi-body"):
            content_box = ui.element("div")

        # ── Lógica de abas ──────────────────────────────────────────────

        def _switch_tab(tab: str) -> None:
            _tab_ref["tab"] = tab
            for tid, btn in tab_btns.items():
                if tid == tab:
                    btn.classes(add="active")
                else:
                    btn.classes(remove="active")
            _refresh()

        def _refresh_cfg() -> None:
            nonlocal cfg
            cfg = load_config()
            _cfg_ref["cfg"] = cfg
            c_ok    = bool(cfg.get("cert_path") and Path(cfg.get("cert_path","")).exists())
            c_color = "#4ADE80" if c_ok else "#FBBF24"
            _cert_dot.set_content(
                f'<div style="position:absolute;top:5px;right:5px;'
                f'width:7px;height:7px;border-radius:50%;pointer-events:none;'
                f'background:{c_color};box-shadow:0 0 5px {c_color}88"></div>'
            )
            _refresh()

        def _refresh() -> None:
            tab = _tab_ref["tab"]
            actions_box.clear()
            stats_box.clear()
            content_box.clear()

            if tab == "nfse":
                _render_nfse()
            elif tab == "pagar":
                _render_pagar()
            elif tab == "receber":
                _render_receber()

        # ── Tab NFS-e ────────────────────────────────────────────────────

        def _render_nfse() -> None:
            _pode_emitir = has_access(_fi_perfil, "fi_nfse_emitir")
            _pode_config = has_access(_fi_perfil, "fi_nfse_configurar")
            _pode_rel    = has_access(_fi_perfil, "fi_relatorio")

            with actions_box:
                if _pode_emitir:
                    ui.button(
                        "Emitir NFS-e", icon="add_circle",
                        on_click=lambda: emitir_nfse_dialog(on_success=_refresh),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-primary")

                if _pode_config:
                    ui.button(
                        "Configurar", icon="settings",
                        on_click=lambda: config_nfse_dialog(on_save=_refresh_cfg),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")

                if _pode_rel:
                    ui.button(
                        "Relatório", icon="bar_chart",
                        on_click=lambda: relatorio_financeiro_dialog(),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")

                ui.button(
                    "Atualizar", icon="refresh", on_click=_refresh,
                ).props("flat round dense").style("color:var(--dmc-muted);margin-left:4px")

                ui.html('<div style="flex:1"></div>')
                _build_nfse_stats()

                if not _DEPS_OK:
                    ui.html(
                        '<span style="font:11px var(--dmc-mono);color:#F87171;'
                        'background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);'
                        'border-radius:6px;padding:4px 10px">'
                        '⚠ pip install lxml cryptography httpx</span>'
                    )

            _build_nfse_table()

        def _build_nfse_stats() -> None:
            entries   = list_nfse()
            n         = len(entries)
            total     = sum(e.get("valor",0) for e in entries)
            mes_atual = datetime.now().strftime("%Y-%m")
            mes_n     = sum(1 for e in entries if (e.get("emitido_em","") or "")[:7] == mes_atual)
            total_fmt = _fmt_brl(total)
            stat_nfse.set_content(f'<div class="fi-stat">{n} nota{"s" if n!=1 else ""}</div>')
            with stats_box:
                for lbl, val, col in [
                    ("Total", total_fmt, "#4ADE80"),
                    ("Mês",   f'{mes_n} nota{"s" if mes_n!=1 else ""}', "#60A5FA"),
                    (env_label, cfg.get("cnpj") or "—", env_color),
                ]:
                    ui.html(
                        f'<div class="fi-inline-stat">'
                        f'<span class="lbl">{lbl}</span>'
                        f'<span class="val" style="color:{col}">{val}</span>'
                        f'</div>'
                    )

        def _build_nfse_table() -> None:
            entries = list_nfse()
            with content_box:
                if not entries:
                    with ui.element("div").classes("fi-empty"):
                        ui.html('<span class="material-icons" style="font-size:52px;color:var(--dmc-b2)">receipt_long</span>')
                        ui.html('<span style="font:13px var(--dmc-fm)">Nenhuma NFS-e emitida ainda.</span>')
                        ui.html('<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Clique em "Emitir NFS-e" para começar.</span>')
                    return

                rows_html = ""
                for e in entries:
                    sucesso = e.get("sucesso", False)
                    amb     = e.get("ambiente", "homologacao")
                    num     = e.get("numero", "—")
                    toma    = e.get("tomador", "—")
                    desc    = e.get("descricao", "—")
                    valor   = e.get("valor", 0)
                    emitido = (e.get("emitido_em","") or "")[:16].replace("T"," ")
                    chave   = e.get("chave_acesso","") or e.get("id","")

                    if not sucesso:
                        st_html = '<span style="color:#F87171;font:600 10px var(--dmc-mono)">ERRO</span>'
                    elif amb == "homologacao":
                        st_html = '<span style="color:#FBBF24;font:600 10px var(--dmc-mono)">HOMO</span>'
                    else:
                        st_html = '<span style="color:#4ADE80;font:600 10px var(--dmc-mono)">EMITIDA</span>'

                    xml_btn = (
                        f'<button class="fi-act-btn" title="XML" '
                        f'data-action="fi_dl_xml" data-id="{chave}"'
                        f'><span class="material-icons" style="font-size:15px">download</span></button>'
                    ) if e.get("nfse_xml") else ""
                    rows_html += (
                        f'<tr data-nfse-key="{chave}">'
                        f'<td><span class="fi-num">#{num}</span></td>'
                        f'<td><div style="display:flex;flex-direction:column;gap:2px">'
                        f'<span class="fi-toma">{toma}</span>'
                        f'<span class="fi-desc" title="{desc}">{desc}</span>'
                        f'</div></td>'
                        f'<td><span class="fi-val">{_fmt_brl(valor)}</span></td>'
                        f'<td>{st_html}</td>'
                        f'<td><span class="fi-ts">{emitido}</span></td>'
                        f'<td><div style="display:flex;gap:4px">'
                        f'<button class="fi-act-btn" title="Ver" '
                        f'data-action="fi_ver" data-id="{chave}"'
                        f'><span class="material-icons" style="font-size:15px">visibility</span></button>'
                        f'{xml_btn}'
                        f'</div></td></tr>'
                    )

                with ui.element("div").classes("fi-card"):
                    ui.html(
                        '<table class="fi-table"><thead><tr>'
                        '<th style="width:70px">Nº</th>'
                        '<th>Tomador / Descrição</th>'
                        '<th style="width:130px">Valor</th>'
                        '<th style="width:80px">Status</th>'
                        '<th style="width:140px">Emitido em</th>'
                        '<th style="width:80px">Ações</th>'
                        f'</tr></thead><tbody>{rows_html}</tbody></table>'
                    )
                async def _wire_nfse_btns():
                    await ui.run_javascript(
                        '(function(){'
                        'document.querySelectorAll(".fi-act-btn[data-action]").forEach(function(b){'
                        'b.onclick=function(){emitEvent(b.getAttribute("data-action"),{id:b.getAttribute("data-id")});};'
                        '});'
                        '})()'
                    )
                ui.timer(0.15, _wire_nfse_btns, once=True)

        # ── Tab Contas a Pagar ────────────────────────────────────────────

        def _render_pagar() -> None:
            _pode_criar   = has_access(_fi_perfil, "fi_pagar_criar")
            _pode_editar  = has_access(_fi_perfil, "fi_pagar_editar")
            _pode_deletar = has_access(_fi_perfil, "fi_pagar_deletar")
            _pode_cat     = has_access(_fi_perfil, "fi_pagar_categorias")
            _pode_rel     = has_access(_fi_perfil, "fi_relatorio")

            contas = load_contas_pagar()
            res    = resumo_pagar()

            with actions_box:
                if _pode_criar:
                    ui.button(
                        "Nova Conta", icon="add_circle",
                        on_click=lambda: nova_conta_pagar_dialog(on_save=_refresh),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-primary").style(
                        "background:rgba(248,113,113,.12);border-color:rgba(248,113,113,.35);color:#F87171"
                    )
                if _pode_cat:
                    ui.button(
                        "Categorias", icon="label",
                        on_click=lambda: categorias_pagar_dialog(on_save=_refresh),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")
                if _pode_rel:
                    ui.button(
                        "Relatório", icon="bar_chart",
                        on_click=lambda: relatorio_financeiro_dialog(),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")
                ui.button(
                    "Lixeira", icon="delete_outline",
                    on_click=lambda: lixeira_financeiro_dialog(on_restore=_refresh),
                ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")
                ui.button(
                    icon="refresh", on_click=_refresh,
                ).props("flat round dense").style("color:var(--dmc-muted);margin-left:4px")
                ui.html('<div style="flex:1"></div>')
                with stats_box:
                    for lbl, val, col in [
                        ("Pendente", _fmt_brl(res["pendente"]), "#FBBF24"),
                        ("Pago",     _fmt_brl(res["pago"]),     "#4ADE80"),
                        ("Total",    _fmt_brl(res["total"]),    "#DCE8DC"),
                    ]:
                        ui.html(
                            f'<div class="fi-inline-stat">'
                            f'<span class="lbl">{lbl}</span>'
                            f'<span class="val" style="color:{col}">{val}</span>'
                            f'</div>'
                        )

            with content_box:
                if not contas:
                    with ui.element("div").classes("fi-empty"):
                        ui.html('<span class="material-icons" style="font-size:52px;color:var(--dmc-b2)">arrow_circle_down</span>')
                        ui.html('<span style="font:13px var(--dmc-fm)">Nenhuma conta a pagar cadastrada.</span>')
                    return

                rows_html = ""
                for c in contas:
                    st     = c.get("status","pendente")
                    cor, bg = _STATUS_PAGAR.get(st, ("#8BAA8B","rgba(139,170,139,.08)"))
                    badge  = _badge(st, cor, bg)
                    cat    = c.get("categoria_nome") or "—"
                    cat_cor = c.get("categoria_cor") or "#8BAA8B"
                    obra   = c.get("obra_nome") or "—"
                    venc   = c.get("data_venc") or "—"
                    pag    = c.get("data_pag") or "—"
                    cid    = c["id"]
                    _btn_pagar = (
                        f'<button class="fi-act-btn" title="Marcar como pago" '
                        f'style="color:#4ADE80;border-color:rgba(74,222,128,.3)" '
                        f'data-action="fi_pagar" data-id="{cid}"'
                        f'><span class="material-icons" style="font-size:14px">check_circle</span></button>'
                    ) if _pode_editar and st != "pago" else ""
                    _btn_editar = (
                        f'<button class="fi-act-btn" title="Editar" '
                        f'data-action="fi_edit_pagar" data-id="{cid}"'
                        f'><span class="material-icons" style="font-size:14px">edit</span></button>'
                    ) if _pode_editar else ""
                    _btn_deletar = (
                        f'<button class="fi-act-btn" title="Excluir" '
                        f'style="color:#F87171;border-color:rgba(248,113,113,.2)" '
                        f'data-action="fi_del_pagar" data-id="{cid}"'
                        f'><span class="material-icons" style="font-size:14px">delete</span></button>'
                    ) if _pode_deletar else ""
                    rows_html += (
                        f'<tr>'
                        f'<td><span class="fi-toma">{c.get("descricao","—")}</span></td>'
                        f'<td><span style="font:11px var(--dmc-mono);'
                        f'background:{cat_cor}14;color:{cat_cor};padding:2px 7px;'
                        f'border-radius:4px;border:1px solid {cat_cor}30">{cat}</span></td>'
                        f'<td><span class="fi-ts">{obra}</span></td>'
                        f'<td><span class="fi-val-p">{_fmt_brl(c.get("valor",0))}</span></td>'
                        f'<td><span class="fi-ts">{venc}</span></td>'
                        f'<td><span class="fi-ts">{pag}</span></td>'
                        f'<td>{badge}</td>'
                        f'<td><div style="display:flex;gap:4px">'
                        f'{_btn_pagar}{_btn_editar}{_btn_deletar}'
                        f'</div></td></tr>'
                    )

                with ui.element("div").classes("fi-card"):
                    ui.html(
                        '<table class="fi-table"><thead><tr>'
                        '<th>Descrição</th>'
                        '<th style="width:120px">Categoria</th>'
                        '<th style="width:140px">Obra</th>'
                        '<th style="width:110px">Valor</th>'
                        '<th style="width:90px">Vencimento</th>'
                        '<th style="width:90px">Pagamento</th>'
                        '<th style="width:90px">Status</th>'
                        '<th style="width:100px">Ações</th>'
                        f'</tr></thead><tbody>{rows_html}</tbody></table>'
                    )
                async def _wire_pagar_btns():
                    await ui.run_javascript(
                        '(function(){'
                        'document.querySelectorAll(".fi-act-btn[data-action]").forEach(function(b){'
                        'b.onclick=function(){emitEvent(b.getAttribute("data-action"),{id:b.getAttribute("data-id")});};'
                        '});'
                        '})()'
                    )
                ui.timer(0.15, _wire_pagar_btns, once=True)


        # ── Tab Contas a Receber ──────────────────────────────────────────

        def _render_receber() -> None:
            _pode_criar   = has_access(_fi_perfil, "fi_receber_criar")
            _pode_pagar   = has_access(_fi_perfil, "fi_receber_pagar")
            _pode_deletar = has_access(_fi_perfil, "fi_receber_deletar")
            _pode_rel     = has_access(_fi_perfil, "fi_relatorio")

            contas = load_contas_receber()
            res    = resumo_receber()

            with actions_box:
                if _pode_criar:
                    ui.button(
                        "Nova Conta", icon="add_circle",
                        on_click=lambda: nova_conta_receber_dialog(on_save=_refresh),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-primary")
                if _pode_rel:
                    ui.button(
                        "Relatório", icon="bar_chart",
                        on_click=lambda: relatorio_financeiro_dialog(),
                    ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")
                ui.button(
                    "Lixeira", icon="delete_outline",
                    on_click=lambda: lixeira_financeiro_dialog(on_restore=_refresh),
                ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")
                ui.button(
                    icon="refresh", on_click=_refresh,
                ).props("flat round dense").style("color:var(--dmc-muted);margin-left:4px")
                ui.html('<div style="flex:1"></div>')
                with stats_box:
                    for lbl, val, col in [
                        ("A Receber", _fmt_brl(res["a_receber"]), "#60A5FA"),
                        ("Recebido",  _fmt_brl(res["recebido"]),  "#4ADE80"),
                        ("Total",     _fmt_brl(res["total"]),     "#DCE8DC"),
                    ]:
                        ui.html(
                            f'<div class="fi-inline-stat">'
                            f'<span class="lbl">{lbl}</span>'
                            f'<span class="val" style="color:{col}">{val}</span>'
                            f'</div>'
                        )

            with content_box:
                if not contas:
                    with ui.element("div").classes("fi-empty"):
                        ui.html('<span class="material-icons" style="font-size:52px;color:var(--dmc-b2)">arrow_circle_up</span>')
                        ui.html('<span style="font:13px var(--dmc-fm)">Nenhuma conta a receber cadastrada.</span>')
                    return

                rows_html = ""
                for c in contas:
                    st      = c.get("status","aberto")
                    cor, bg = _STATUS_RECEBER.get(st, ("#8BAA8B","rgba(139,170,139,.08)"))
                    badge   = _badge(st, cor, bg)
                    vt      = float(c.get("valor_total",0))
                    vp      = float(c.get("valor_pago",0))
                    pct     = int(min(100, (vp/vt*100))) if vt else 0
                    parc    = c.get("parcelas",1)
                    n_pags  = len(c.get("pagamentos",[]))
                    obra    = c.get("obra_nome") or "—"
                    venc    = c.get("data_venc") or "—"
                    cid     = c["id"]

                    progresso = (
                        f'<div class="fi-progress">'
                        f'<div class="fi-progress-bar" style="width:{pct}%;background:{cor}"></div>'
                        f'</div>'
                        f'<span style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">'
                        f'{_fmt_brl(vp)} / {_fmt_brl(vt)}</span>'
                    )

                    _btn_pag = (
                        f'<button class="fi-act-btn" title="Registrar pagamento" '
                        f'style="color:#4ADE80;border-color:rgba(74,222,128,.3)" '
                        f'data-action="fi_pag_receber" data-id="{cid}"'
                        f'><span class="material-icons" style="font-size:14px">payments</span></button>'
                    ) if _pode_pagar else ""
                    _btn_ver = (
                        f'<button class="fi-act-btn" title="Ver parcelas" '
                        f'data-action="fi_ver_receber" data-id="{cid}"'
                        f'><span class="material-icons" style="font-size:14px">list</span></button>'
                    )
                    _btn_del = (
                        f'<button class="fi-act-btn" title="Excluir" '
                        f'style="color:#F87171;border-color:rgba(248,113,113,.2)" '
                        f'data-action="fi_del_receber" data-id="{cid}"'
                        f'><span class="material-icons" style="font-size:14px">delete</span></button>'
                    ) if _pode_deletar else ""
                    rows_html += (
                        f'<tr>'
                        f'<td><span class="fi-toma">{c.get("descricao","—")}</span></td>'
                        f'<td><div style="display:flex;flex-direction:column;gap:2px">'
                        f'<span class="fi-toma">{c.get("cliente_nome","—")}</span>'
                        f'</div></td>'
                        f'<td><span class="fi-ts">{obra}</span></td>'
                        f'<td><div style="display:flex;flex-direction:column;gap:3px">{progresso}</div></td>'
                        f'<td><span style="font:11px var(--dmc-mono);color:var(--dmc-muted)">'
                        f'{n_pags}/{parc} parcela{"s" if parc!=1 else ""}</span></td>'
                        f'<td><span class="fi-ts">{venc}</span></td>'
                        f'<td>{badge}</td>'
                        f'<td><div style="display:flex;gap:4px">'
                        f'{_btn_pag}{_btn_ver}{_btn_del}'
                        f'</div></td></tr>'
                    )

                with ui.element("div").classes("fi-card"):
                    ui.html(
                        '<table class="fi-table"><thead><tr>'
                        '<th>Descrição</th>'
                        '<th style="width:140px">Cliente</th>'
                        '<th style="width:140px">Obra</th>'
                        '<th style="width:160px">Progresso</th>'
                        '<th style="width:100px">Parcelas</th>'
                        '<th style="width:90px">Vencimento</th>'
                        '<th style="width:90px">Status</th>'
                        '<th style="width:110px">Ações</th>'
                        f'</tr></thead><tbody>{rows_html}</tbody></table>'
                    )
                async def _wire_receber_btns():
                    await ui.run_javascript(
                        '(function(){'
                        'document.querySelectorAll(".fi-act-btn[data-action]").forEach(function(b){'
                        'b.onclick=function(){emitEvent(b.getAttribute("data-action"),{id:b.getAttribute("data-id")});};'
                        '});'
                        '})()'
                    )
                ui.timer(0.15, _wire_receber_btns, once=True)

        # ── Handlers de eventos (registrados uma vez, ao nível da página) ──

        def _on_nfse_ver(e):
            key = e.args.get("id","")
            for entry in list_nfse():
                k = entry.get("chave_acesso") or entry.get("id","")
                if k == key:
                    ver_nfse_dialog(entry)
                    break

        def _on_nfse_dl_xml(e):
            key = e.args.get("id","")
            for entry in list_nfse():
                k = entry.get("chave_acesso") or entry.get("id","")
                if k == key and entry.get("nfse_xml"):
                    xml_b64 = base64.b64encode(entry["nfse_xml"].encode()).decode()
                    fname   = f'NFSe_{entry.get("numero", key)}.xml'
                    ui.run_javascript(f'''
                        const a = document.createElement('a');
                        a.href = 'data:application/xml;base64,{xml_b64}';
                        a.download = '{fname}';
                        document.body.appendChild(a); a.click();
                        document.body.removeChild(a);
                    ''')
                    break

        def _on_pagar(e):
            from services.financeiro import pagar_conta
            pagar_conta(e.args.get("id",""))
            _refresh()

        def _on_del_pagar(e):
            from services.financeiro import delete_conta_pagar
            delete_conta_pagar(e.args.get("id",""))
            _refresh()

        def _on_edit_pagar(e):
            cid = e.args.get("id","")
            conta = next((c for c in load_contas_pagar() if c["id"] == cid), None)
            if conta:
                nova_conta_pagar_dialog(conta=conta, on_save=_refresh)

        def _on_pag_receber(e):
            cid   = e.args.get("id","")
            conta = next((c for c in load_contas_receber() if c["id"] == cid), None)
            if conta:
                registrar_pagamento_dialog(conta=conta, on_save=_refresh)

        def _on_ver_receber(e):
            cid   = e.args.get("id","")
            conta = next((c for c in load_contas_receber() if c["id"] == cid), None)
            if conta:
                registrar_pagamento_dialog(conta=conta, on_save=_refresh, modo="ver")

        def _on_del_receber(e):
            from services.financeiro import delete_conta_receber
            delete_conta_receber(e.args.get("id",""))
            _refresh()

        ui.on("fi_ver",         _on_nfse_ver)
        ui.on("fi_dl_xml",      _on_nfse_dl_xml)
        ui.on("fi_pagar",       _on_pagar)
        ui.on("fi_del_pagar",   _on_del_pagar)
        ui.on("fi_edit_pagar",  _on_edit_pagar)
        ui.on("fi_pag_receber", _on_pag_receber)
        ui.on("fi_ver_receber", _on_ver_receber)
        ui.on("fi_del_receber", _on_del_receber)

        _refresh()
