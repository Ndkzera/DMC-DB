"""Página Financeiro / NFS-e — /financeiro"""

from nicegui import ui

from services.auth import current_user_label, current_user_perfil, is_authenticated, logout_user, mark_active, current_user_name
from nicegui import app as _fapp
from services.acesso import has_access
from services.nfse import list_nfse, load_config, _DEPS_OK
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
  border-collapse: collapse; width: 100%; min-width: 760px;
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
.fi-status-ok  { color: #4ADE80; font: 600 10px var(--dmc-mono); }
.fi-status-err { color: #F87171; font: 600 10px var(--dmc-mono); }
.fi-status-hom { color: #FBBF24; font: 600 10px var(--dmc-mono); }
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
@media (max-width: 860px) {
  .fi-topbar, .fi-actions, .fi-body { padding-left: 14px; padding-right: 14px; }
  .hide-sm { display: none !important; }
}
</style>
"""


@ui.page("/financeiro")
def financeiro_page():
    if not is_authenticated():
        ui.navigate.to("/login")
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

    from ui.financeiro_dialogs import emitir_nfse_dialog, config_nfse_dialog, ver_nfse_dialog, relatorio_financeiro_dialog

    cfg = load_config()

    with ui.element("div").classes("fi-page"):

        # ── Topbar ────────────────────────────────────────────────────
        with ui.element("div").classes("fi-topbar"):
            ui.html(
                '<div class="fi-title">'
                '<span class="material-icons ico">receipt_long</span>'
                'Financeiro / NFS-e'
                '</div>'
            )
            ui.html('<div class="fi-sep"></div>')

            env = cfg.get('ambiente', 'homologacao')
            env_color = '#FBBF24' if env == 'homologacao' else '#4ADE80'
            env_label = 'HOMOLOGAÇÃO' if env == 'homologacao' else 'PRODUÇÃO'
            stat_label = ui.html('<div class="fi-stat">—</div>')
            ui.html(
                f'<span class="fi-env-badge" '
                f'style="background:{env_color}18;border:1px solid {env_color}44;'
                f'color:{env_color}">{env_label}</span>'
            )
            ui.html('<div class="fi-spacer"></div>')
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                "flat round dense"
            ).style("color:var(--dmc-muted)")

        # ── Barra de ações ─────────────────────────────────────────────
        with ui.element("div").classes("fi-actions"):
            ui.button(
                "Emitir NFS-e", icon="add_circle",
                on_click=lambda: emitir_nfse_dialog(on_success=_refresh),
            ).props("unelevated no-caps").classes("dmc-btn dmc-btn-primary")

            ui.button(
                "Configurar", icon="settings",
                on_click=lambda: config_nfse_dialog(on_save=_refresh_cfg),
            ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")

            ui.button(
                "Relatório", icon="bar_chart",
                on_click=lambda: relatorio_financeiro_dialog(),
            ).props("unelevated no-caps").classes("dmc-btn dmc-btn-secondary")

            ui.button(
                "Atualizar", icon="refresh",
                on_click=lambda: _refresh(),
            ).props("flat round dense").style("color:var(--dmc-muted);margin-left:4px")

            ui.html('<div class="fi-spacer"></div>')
            stats_box = ui.element("div").style("display:flex;align-items:center;gap:8px;flex-shrink:0;flex-wrap:wrap")

            if not _DEPS_OK:
                ui.html(
                    '<span style="font:11px var(--dmc-mono);color:#F87171;'
                    'background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);'
                    'border-radius:6px;padding:4px 10px">'
                    '⚠ Dependências ausentes: pip install lxml cryptography httpx</span>'
                )

        # ── Corpo ──────────────────────────────────────────────────────
        with ui.element("div").classes("fi-body"):
            content_box = ui.element("div")

        # ── Render ────────────────────────────────────────────────────
        _cfg_ref: dict = {'cfg': cfg}

        def _refresh_cfg():
            nonlocal cfg
            cfg = load_config()
            _cfg_ref['cfg'] = cfg
            _refresh()

        def _refresh():
            entries = list_nfse()
            n = len(entries)
            total = sum(e.get('valor', 0) for e in entries)
            mes_atual = datetime.now().strftime('%Y-%m')
            mes_n = sum(1 for e in entries if (e.get('emitido_em', '') or '')[:7] == mes_atual)

            stat_label.set_content(
                f'<div class="fi-stat">{n} nota{"s" if n != 1 else ""}</div>'
            )

            total_fmt = f'R$ {total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
            stats_box.clear()
            with stats_box:
                for lbl, val, col in [
                    ('Total', total_fmt, '#4ADE80'),
                    ('Mês',   f'{mes_n} nota{"s" if mes_n != 1 else ""}', '#60A5FA'),
                    (env_label, cfg.get('cnpj') or '—', env_color),
                ]:
                    ui.html(
                        f'<div class="fi-inline-stat">'
                        f'<span class="lbl">{lbl}</span>'
                        f'<span class="val" style="color:{col}">{val}</span>'
                        f'</div>'
                    )

            content_box.clear()
            with content_box:
                if not entries:
                    with ui.element("div").classes("fi-empty"):
                        ui.html('<span class="material-icons" style="font-size:52px;color:var(--dmc-b2)">receipt_long</span>')
                        ui.html('<span style="font:13px var(--dmc-fm)">Nenhuma NFS-e emitida ainda.</span>')
                        ui.html('<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Clique em "Emitir NFS-e" para começar.</span>')
                    return

                rows_html = ''
                for e in entries:
                    sucesso  = e.get('sucesso', False)
                    amb      = e.get('ambiente', 'homologacao')
                    num      = e.get('numero', '—')
                    toma     = e.get('tomador', '—')
                    desc     = e.get('descricao', '—')
                    valor    = e.get('valor', 0)
                    emitido  = (e.get('emitido_em', '') or '')[:16].replace('T', ' ')
                    chave    = e.get('chave_acesso', '') or e.get('id', '')

                    if not sucesso:
                        status_html = '<span class="fi-status-err">ERRO</span>'
                    elif amb == 'homologacao':
                        status_html = '<span class="fi-status-hom">HOMO</span>'
                    else:
                        status_html = '<span class="fi-status-ok">EMITIDA</span>'

                    valor_fmt = f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

                    rows_html += (
                        f'<tr data-nfse-key="{chave}">'
                        f'<td><span class="fi-num">#{num}</span></td>'
                        f'<td><div style="display:flex;flex-direction:column;gap:2px">'
                        f'<span class="fi-toma">{toma}</span>'
                        f'<span class="fi-desc" title="{desc}">{desc}</span>'
                        f'</div></td>'
                        f'<td><span class="fi-val">{valor_fmt}</span></td>'
                        f'<td>{status_html}</td>'
                        f'<td><span class="fi-ts">{emitido}</span></td>'
                        f'<td>'
                        f'<div style="display:flex;gap:4px">'
                        f'<button class="fi-act-btn" title="Ver detalhes" '
                        f'onclick="emitEvent(\'fi_ver\',{{key:\"{chave}\"}})">'
                        f'<span class="material-icons" style="font-size:15px">visibility</span>'
                        f'</button>'
                        f'{"" if not e.get("nfse_xml") else f"""<button class="fi-act-btn" title="Download XML" onclick="emitEvent(\'fi_dl_xml\',{{key:\"{chave}\"}})"><span class="material-icons" style="font-size:15px">download</span></button>"""}'
                        f'</div>'
                        f'</td>'
                        f'</tr>'
                    )

                with ui.element("div").classes("fi-card"):
                    ui.html(
                        '<table class="fi-table">'
                        '<thead><tr>'
                        '<th style="width:70px">Nº</th>'
                        '<th>Tomador / Descrição</th>'
                        '<th style="width:130px">Valor</th>'
                        '<th style="width:80px">Status</th>'
                        '<th style="width:140px">Emitido em</th>'
                        '<th style="width:80px">Ações</th>'
                        '</tr></thead>'
                        f'<tbody>{rows_html}</tbody>'
                        '</table>'
                    )

            # Eventos JS → Python
            def _on_ver(e):
                key = e.args.get('key', '')
                for entry in list_nfse():
                    k = entry.get('chave_acesso') or entry.get('id', '')
                    if k == key:
                        ver_nfse_dialog(entry)
                        break

            def _on_dl_xml(e):
                key = e.args.get('key', '')
                for entry in list_nfse():
                    k = entry.get('chave_acesso') or entry.get('id', '')
                    if k == key and entry.get('nfse_xml'):
                        xml_b64 = base64.b64encode(entry['nfse_xml'].encode()).decode()
                        fname   = f'NFSe_{entry.get("numero", key)}.xml'
                        ui.run_javascript(f'''
                            const a = document.createElement('a');
                            a.href = 'data:application/xml;base64,{xml_b64}';
                            a.download = '{fname}';
                            document.body.appendChild(a); a.click();
                            document.body.removeChild(a);
                        ''')
                        break

            ui.on('fi_ver',    _on_ver)
            ui.on('fi_dl_xml', _on_dl_xml)

        from datetime import datetime
        import base64

        _refresh()
