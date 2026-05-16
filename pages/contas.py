"""Página de Gestão de Contas — /contas"""

import uuid
from nicegui import ui
from services.auth import (
    _hash, _load as _load_users, _save as _save_users,
    is_authenticated, current_user_perfil, PERFIS, PERFIL_CORES,
)
from services.acesso import has_access
from ui.styles import BOOTSTRAP_CDN, CSS

_PERFIL_META = {
    "DESENVOLVEDOR":           ("code",                 "Nível 1"),
    "ADMINISTRADOR":           ("admin_panel_settings", "Nível 2"),
    "FUNCIONÁRIO PRIORITÁRIO": ("star",                 "Nível 3"),
    "FUNCIONÁRIO":             ("person",               "Nível 4"),
    "FUNCIONÁRIO CAMPO":       ("construction",         "Nível 5"),
}

_CSS = """
html, body, .nicegui-content {
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}
/* ── Dialog overrides ── */
.q-dialog__backdrop {
  background: rgba(0,0,0,.82) !important;
  backdrop-filter: blur(6px) !important;
}
.q-dialog .q-card {
  background: var(--dmc-bg2) !important;
  color: var(--dmc-text) !important;
}
.q-dialog .gc-input {
  background: var(--dmc-bg) !important;
  color: var(--dmc-text) !important;
}
.q-dialog .gc-label {
  color: var(--dmc-muted2) !important;
}
.gc-page {
  min-height: 100vh;
  width: 100%;
  background: var(--dmc-bg);
  display: flex;
  flex-direction: column;
}
/* ── Header ── */
.gc-header {
  position: sticky; top: 0; z-index: 100;
  background: var(--dmc-header-bg);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--dmc-b1);
  display: flex; align-items: center; gap: 14px;
  padding: 0 32px; height: 60px; flex-shrink: 0;
}
/* ── Sidebar de navegação ── */
.gc-sidenav {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--dmc-b1);
  padding: 20px 0 40px;
  position: fixed;
  left: 0;
  top: 60px;
  z-index: 50;
  height: calc(100vh - 60px);
  overflow-y: auto;
  background: var(--dmc-bg);
}
.gc-sidenav-label {
  padding: 6px 18px 8px;
  font: 600 9px var(--dmc-mono);
  color: var(--dmc-muted2);
  letter-spacing: .2em;
  text-transform: uppercase;
  opacity: .7;
}
.gc-nav-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 9px 18px;
  background: transparent; border: none; cursor: pointer;
  font: 13px var(--dmc-fm); color: var(--dmc-muted2);
  text-align: left; transition: all .15s;
  border-left: 2px solid transparent;
}
.gc-nav-item:hover { background: rgba(0,0,0,.04); color: var(--dmc-text); }
.gc-nav-item.active {
  color: #4ADE80;
  background: rgba(74,222,128,.07);
  border-left-color: #4ADE80;
  font-weight: 600;
}
/* ── Body 2-col ── */
/* ── Layout principal ── */
.gc-layout {
  flex: 1;
  display: flex;
  min-height: 0;
}
.gc-main {
  flex: 1; min-width: 0;
  overflow-y: auto;
}
.gc-body {
  display: grid;
  grid-template-columns: 340px 1fr;
  max-width: 1060px;
  width: 100%;
  margin: 0 auto;
  padding: 24px 24px 32px;
  padding-left: 244px;
  box-sizing: border-box;
  gap: 28px;
  align-items: flex-start;
}
@media(max-width:800px){ .gc-body { grid-template-columns: 1fr; } }
/* ── Panel header ── */
.gc-panel-hdr {
  padding: 13px 18px;
  border-bottom: 1px solid var(--dmc-b1);
  display: flex; align-items: center; gap: 8px;
  font: 600 10px var(--dmc-mono);
  color: var(--dmc-muted2);
  letter-spacing: .15em;
  text-transform: uppercase;
  background: var(--dmc-bg3);
  flex-shrink: 0;
}
/* ── Users panel (left) ── */
.gc-users-panel {
  background: var(--dmc-bg2);
  border: 1px solid var(--dmc-b1);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.gc-user-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--dmc-b1);
  transition: background .15s;
}
.gc-user-row:last-child { border-bottom: none; }
.gc-user-row:hover { background: rgba(0,0,0,.04); }
.gc-avatar {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  font: 700 13px var(--dmc-mono);
  letter-spacing: -.5px;
}
.gc-user-name {
  font: 500 13px var(--dmc-fm);
  color: var(--dmc-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gc-user-sub {
  font: 11px var(--dmc-fm);
  color: var(--dmc-muted2);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.gc-badge {
  font: 700 8px var(--dmc-mono);
  padding: 2px 7px; border-radius: 20px;
  letter-spacing: .08em; text-transform: uppercase;
  white-space: nowrap;
}
.gc-icon-btn {
  width: 28px; height: 28px; border-radius: 7px;
  flex-shrink: 0; border: 1px solid;
  background: transparent; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.gc-icon-btn:hover { opacity: .8; transform: scale(1.05); }
/* ── Form panel (right) ── */
.gc-form-panel {
  display: flex; flex-direction: column; gap: 0;
  background: var(--dmc-bg2);
  border: 1px solid var(--dmc-b1);
  border-radius: 16px;
  overflow: hidden;
}
.gc-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  padding: 20px 22px;
}
@media(max-width:540px){ .gc-form-grid { grid-template-columns: 1fr; } }
.gc-field { display: flex; flex-direction: column; gap: 5px; }
.gc-field.full { grid-column: 1/-1; }
.gc-label {
  font: 600 10px var(--dmc-mono);
  color: var(--dmc-muted2);
  letter-spacing: .14em;
  text-transform: uppercase;
}
.gc-input {
  background: var(--dmc-bg);
  border: 1px solid var(--dmc-b1);
  border-radius: 8px;
  color: var(--dmc-text);
  font: 13px var(--dmc-fm);
  padding: 9px 12px;
  outline: none;
  transition: border-color .2s;
  width: 100%;
  box-sizing: border-box;
}
.gc-input:focus { border-color: var(--dmc-green); }
/* ── Perfil pills ── */
.gc-perfil-wrap {
  padding: 16px 22px 22px;
  border-top: 1px solid var(--dmc-b1);
  background: var(--dmc-bg3);
}
.gc-pills {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 12px;
}
.gc-pill {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid var(--dmc-b1);
  background: var(--dmc-bg3);
  cursor: pointer;
  transition: all .18s;
  text-align: left;
  width: 100%; box-sizing: border-box;
}
.gc-pill:hover { background: var(--dmc-b1) !important; }
.gc-pill.selected { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(0,0,0,.35); }
.gc-pill .pill-icon { font-size: 18px; flex-shrink: 0; }
.gc-pill .pill-name { font: 700 10px var(--dmc-mono); letter-spacing: .06em; text-transform: uppercase; line-height: 1.2; }
.gc-pill .pill-lvl  { font: 9px var(--dmc-mono); opacity: .5; margin-top: 1px; }
.gc-pill .pill-dot  { width: 7px; height: 7px; border-radius: 50%; margin-left: auto; flex-shrink: 0; opacity: 0; transition: opacity .2s; }
.gc-pill.selected .pill-dot { opacity: 1; }
/* ── Form footer ── */
.gc-form-footer {
  padding: 14px 22px;
  border-top: 1px solid var(--dmc-b1);
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px;
  background: var(--dmc-bg3);
}
"""

_SCRIPT = """
<script>
function maskTelefone(el){
  var v=el.value.replace(/\D/g,'').slice(0,11);
  if(!v){el.value='';return;}
  if(v.length<=2){el.value='('+v;return;}
  if(v.length<=6){el.value='('+v.slice(0,2)+') '+v.slice(2);return;}
  if(v.length<=10){el.value='('+v.slice(0,2)+') '+v.slice(2,6)+'-'+v.slice(6);return;}
  el.value='('+v.slice(0,2)+') '+v.slice(2,3)+' '+v.slice(3,7)+'-'+v.slice(7);
}
function gcSelectPerfil(el) {
  var wrap = el.closest('.gc-pills');
  if (!wrap) return;
  wrap.querySelectorAll('.gc-pill').forEach(function(c) {
    c.classList.remove('selected');
    c.style.border = '1px solid rgba(255,255,255,.09)';
    c.style.background = 'rgba(255,255,255,.04)';
    c.style.transform = '';
    c.style.boxShadow = '';
  });
  el.classList.add('selected');
  el.style.border = '2px solid ' + el.dataset.br;
  el.style.background = el.dataset.bg;
  el.style.transform = 'translateY(-1px)';
  el.style.boxShadow = '0 6px 18px rgba(0,0,0,.35)';
  var inp = document.getElementById(el.dataset.target);
  if (inp) inp.value = el.dataset.perfil;
}
</script>
"""


def _pills_html(perfil_sel: str, input_id: str) -> str:
    out = f'<input type="hidden" id="{input_id}" value="{perfil_sel}"><div class="gc-pills">'
    for p in PERFIS:
        fg, bg, br = PERFIL_CORES[p]
        icon, nivel = _PERFIL_META[p]
        sel = p == perfil_sel
        sel_cls = " selected" if sel else ""
        sel_sty = f"border:2px solid {br};background:{bg};transform:translateY(-1px);box-shadow:0 6px 18px rgba(0,0,0,.35);" if sel else ""
        out += (
            f'<button type="button" class="gc-pill{sel_cls}" '
            f'data-perfil="{p}" data-fg="{fg}" data-bg="{bg}" data-br="{br}" '
            f'data-target="{input_id}" style="{sel_sty}">'
            f'<span class="material-icons pill-icon" style="color:{fg}">{icon}</span>'
            f'<span style="flex:1;min-width:0">'
            f'<div class="pill-name" style="color:{fg}">{p}</div>'
            f'<div class="pill-lvl">{nivel}</div>'
            f'</span>'
            f'<span class="pill-dot" style="background:{fg}"></span>'
            f'</button>'
        )
    out += '</div>'
    return out


@ui.page("/contas")
def contas_page():
    if not is_authenticated():
        ui.navigate.to("/login")
        return
    if not has_access(current_user_perfil(), "adm_gestao_contas"):
        ui.navigate.to("/")
        return

    ui.dark_mode().enable()
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(f"<style>{_CSS}</style>")
    ui.add_head_html(_SCRIPT)
    ui.add_head_html("<script>setTimeout(function(){var t=localStorage.getItem('dmc-theme')||'dark';if(window.Quasar)window.Quasar.Dark.set(t==='dark');},300);</script>")

    with ui.element("div").classes("gc-page"):

        # ── Header ────────────────────────────────────────────────────
        with ui.element("div").classes("gc-header"):
            ui.html(
                '<div style="width:36px;height:36px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:18px;color:#4ADE80">shield</span></div>'
            )
            with ui.element("div").style("display:flex;flex-direction:column;gap:1px;line-height:1"):
                ui.html('<span style="font:700 15px \'Syne\',sans-serif;color:var(--dmc-text)">Administrativo</span>')
                ui.html('<span style="font:10px \'Inter\',sans-serif;color:var(--dmc-muted2);letter-spacing:.1em;text-transform:uppercase">Gestão de contas e permissões · DMC Topografia</span>')
            ui.element("div").style("flex:1")
            ui.button(icon="close", on_click=lambda: ui.run_javascript("window.close()")).props(
                'flat round dense'
            ).style("color:var(--dmc-muted)")

        with ui.element("div").classes("gc-layout"):

            # ── Sidebar de navegação ──────────────────────────────────
            with ui.element("div").classes("gc-sidenav"):
                ui.html('<div class="gc-sidenav-label">Administrativo</div>')

                with ui.element("button").classes("gc-nav-item active"):
                    ui.html('<span class="material-icons" style="font-size:16px;color:#4ADE80;flex-shrink:0">manage_accounts</span>')
                    ui.html("<span>Gestão de Contas</span>")

                b_acesso = ui.element("button").classes("gc-nav-item")
                with b_acesso:
                    ui.html('<span class="material-icons" style="font-size:16px;color:#C4B5FD;flex-shrink:0">security</span>')
                    ui.html("<span>Configuração de Acesso</span>")
                b_acesso.on("click", lambda: ui.navigate.to("/acesso"))

        with ui.element("div").classes("gc-body"):

            # ════ COLUNA ESQUERDA — lista de usuários ════════════════
            users_panel = ui.element("div").classes("gc-users-panel")

            def _render_users():
                users_panel.clear()
                with users_panel:
                    with ui.element("div").classes("gc-panel-hdr"):
                        ui.html('<span class="material-icons" style="font-size:13px;color:#60A5FA">group</span>')
                        ui.html("Usuários cadastrados")
                        users_count = len(_load_users())
                        ui.html(
                            f'<span style="margin-left:auto;background:rgba(96,165,250,.12);'
                            f'border:1px solid rgba(96,165,250,.25);border-radius:20px;'
                            f'padding:1px 9px;font:700 10px var(--dmc-mono);color:#60A5FA">'
                            f'{users_count}</span>'
                        )

                    users = _load_users()
                    if not users:
                        ui.html(
                            '<div style="padding:32px 20px;text-align:center;'
                            'font:12px var(--dmc-fm);color:var(--dmc-muted2)">Nenhum usuário cadastrado.</div>'
                        )
                    else:
                        for u in users:
                            nome   = u.get("nome", "?")
                            email  = u.get("email", "")
                            cargo  = u.get("cargo", "")
                            perfil = u.get("perfil", "FUNCIONÁRIO")
                            uid    = u.get("id", "")
                            initials = "".join(p[0].upper() for p in nome.split()[:2])
                            fg, bg, br = PERFIL_CORES.get(perfil, ("#4ADE80", "rgba(74,222,128,.1)", "rgba(74,222,128,.25)"))

                            with ui.element("div").classes("gc-user-row"):
                                ui.html(
                                    f'<div class="gc-avatar" style="background:{bg};border:1px solid {br};color:{fg}">'
                                    f'{initials}</div>'
                                )
                                with ui.element("div").style("flex:1;min-width:0"):
                                    with ui.element("div").style("display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-bottom:2px"):
                                        ui.html(f'<span class="gc-user-name">{nome}</span>')
                                        ui.html(
                                            f'<span class="gc-badge" style="background:{bg};border:1px solid {br};color:{fg}">'
                                            f'{perfil}</span>'
                                        )
                                    sub = email + (f" · {cargo}" if cargo else "")
                                    ui.html(f'<div class="gc-user-sub">{sub}</div>')

                                with ui.element("div").style("display:flex;gap:5px;flex-shrink:0;margin-left:4px"):

                                    def _editar(u_id=uid, u_data=dict(u)):
                                        ed = u_data
                                        with ui.dialog() as dlg_ed, ui.card().style(
                                            "background:#111A11!important;"
                                            "border:1px solid #1E301E!important;"
                                            "border-radius:18px!important;padding:0;"
                                            "width:min(540px,96vw);color:#D4E8D4!important;"
                                            "box-shadow:0 24px 64px rgba(0,0,0,.85)!important;"
                                        ):
                                            with ui.element("div").style(
                                                "padding:16px 22px;border-bottom:1px solid var(--dmc-b1);"
                                                "display:flex;align-items:center;gap:12px;"
                                            ):
                                                ui.html(
                                                    '<div style="width:36px;height:36px;border-radius:9px;flex-shrink:0;'
                                                    'background:rgba(96,165,250,.1);border:1px solid rgba(96,165,250,.25);'
                                                    'display:flex;align-items:center;justify-content:center;">'
                                                    '<span class="material-icons" style="font-size:17px;color:#60A5FA">edit</span></div>'
                                                )
                                                with ui.element("div").style("flex:1"):
                                                    ui.html(f'<div style="font:700 14px var(--dmc-fd);color:var(--dmc-text)">Editar usuário</div>')
                                                    ui.html(f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">{ed.get("nome","")}</div>')
                                                ui.button(icon="close", on_click=dlg_ed.close).props("flat round dense").style("color:var(--dmc-muted)")

                                            ui.html(f"""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:20px 22px 16px">
  <div style="display:flex;flex-direction:column;gap:5px">
    <label class="gc-label">Nome completo</label>
    <input id="ed-nome" class="gc-input" type="text" value="{ed.get('nome','')}">
  </div>
  <div style="display:flex;flex-direction:column;gap:5px">
    <label class="gc-label">E-mail</label>
    <input id="ed-email" class="gc-input" type="email" value="{ed.get('email','')}">
  </div>
  <div style="display:flex;flex-direction:column;gap:5px">
    <label class="gc-label">Telefone</label>
    <input id="ed-tel" class="gc-input" type="tel" value="{ed.get('telefone','')}">
  </div>
  <div style="display:flex;flex-direction:column;gap:5px">
    <label class="gc-label">Cargo / Função</label>
    <input id="ed-cargo" class="gc-input" type="text" value="{ed.get('cargo','')}">
  </div>
  <div style="display:flex;flex-direction:column;gap:5px">
    <label class="gc-label">Nova senha <span style="opacity:.5;font-weight:400">(em branco = manter)</span></label>
    <input id="ed-senha" class="gc-input" type="password" placeholder="••••••••">
  </div>
  <div style="display:flex;flex-direction:column;gap:5px">
    <label class="gc-label">Confirmar nova senha</label>
    <input id="ed-senha2" class="gc-input" type="password" placeholder="••••••••">
  </div>
</div>
<div style="padding:0 22px 20px">
  <div style="font:600 10px var(--dmc-mono);color:var(--dmc-muted2);letter-spacing:.15em;
    text-transform:uppercase;margin-bottom:12px;display:flex;align-items:center;gap:8px">
    <span class="material-icons" style="font-size:13px">shield</span>Perfil de acesso
    <span style="flex:1;height:1px;background:var(--dmc-b1);display:inline-block"></span>
  </div>
  {_pills_html(ed.get('perfil','FUNCIONÁRIO'), 'ed-perfil')}
</div>
<div style="padding:2px 22px 10px;min-height:22px">
  <span id="ed-err" style="color:#F87171;font:12px var(--dmc-fm)"></span>
</div>
""")

                                            with ui.element("div").style(
                                                "padding:12px 22px;border-top:1px solid var(--dmc-b1);"
                                                "display:flex;justify-content:flex-end;gap:8px;"
                                                "background:rgba(0,0,0,.1);"
                                            ):
                                                ui.button("Cancelar", on_click=dlg_ed.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

                                                async def _salvar_edicao(uid2=u_id):
                                                    vals = await ui.run_javascript("""({
                                                      nome:   document.getElementById('ed-nome').value.trim(),
                                                      email:  document.getElementById('ed-email').value.trim(),
                                                      tel:    document.getElementById('ed-tel').value.trim(),
                                                      cargo:  document.getElementById('ed-cargo').value.trim(),
                                                      senha:  document.getElementById('ed-senha').value,
                                                      senha2: document.getElementById('ed-senha2').value,
                                                      perfil: document.getElementById('ed-perfil').value,
                                                    })""")
                                                    if not vals.get("nome"):
                                                        await ui.run_javascript("document.getElementById('ed-err').textContent='Preencha o nome.'"); return
                                                    if not vals.get("email"):
                                                        await ui.run_javascript("document.getElementById('ed-err').textContent='Preencha o e-mail.'"); return
                                                    if vals["senha"] and len(vals["senha"]) < 4:
                                                        await ui.run_javascript("document.getElementById('ed-err').textContent='Senha mínimo 4 caracteres.'"); return
                                                    if vals["senha"] != vals["senha2"]:
                                                        await ui.run_javascript("document.getElementById('ed-err').textContent='As senhas não coincidem.'"); return
                                                    users_all = _load_users()
                                                    for uu in users_all:
                                                        if uu.get("id") == uid2:
                                                            uu["nome"]     = vals["nome"]
                                                            uu["email"]    = vals["email"]
                                                            uu["telefone"] = vals.get("tel", "")
                                                            uu["cargo"]    = vals.get("cargo", "")
                                                            uu["perfil"]   = vals.get("perfil", "FUNCIONÁRIO")
                                                            uu["admin"]    = vals.get("perfil") in ("DESENVOLVEDOR", "ADMINISTRADOR")
                                                            if vals["senha"]:
                                                                uu["senha_hash"] = _hash(vals["senha"])
                                                            break
                                                    _save_users(users_all)
                                                    dlg_ed.close()
                                                    ui.notify(f"✓ {vals['nome']} atualizado!", type="positive")
                                                    _render_users()

                                                ui.button("Salvar alterações", icon="save", on_click=_salvar_edicao).props(
                                                    'unelevated no-caps'
                                                ).classes('dmc-btn dmc-btn-primary').style("padding:0 20px")

                                            ui.run_javascript("""
setTimeout(function(){
  document.querySelectorAll('[data-target="ed-perfil"]').forEach(function(c){
    c.addEventListener('click', function(){ gcSelectPerfil(c); });
  });
  var edTel=document.getElementById('ed-tel');
  if(edTel) edTel.oninput=function(){ maskTelefone(this); };
}, 200);
""")
                                        dlg_ed.open()

                                    edit_btn = ui.element("button").classes("gc-icon-btn").style(
                                        "border-color:rgba(96,165,250,.3);color:#60A5FA;"
                                    )
                                    with edit_btn:
                                        ui.html('<span class="material-icons" style="font-size:14px">edit</span>')
                                    edit_btn.on("click", _editar)

                                    def _confirmar_del(u_id=uid, u_nome=nome):
                                        with ui.dialog() as dlg_conf, ui.card().style(
                                            "background:#111A11!important;"
                                            "border:1px solid #1E301E!important;"
                                            "border-radius:16px!important;padding:0;"
                                            "min-width:340px;color:#D4E8D4!important;"
                                            "box-shadow:0 24px 64px rgba(0,0,0,.85)!important;"
                                        ):
                                            with ui.element("div").style(
                                                "padding:18px 22px;border-bottom:1px solid var(--dmc-b1);"
                                                "display:flex;align-items:center;gap:12px;"
                                            ):
                                                ui.html(
                                                    '<div style="width:36px;height:36px;border-radius:9px;flex-shrink:0;'
                                                    'background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.25);'
                                                    'display:flex;align-items:center;justify-content:center;">'
                                                    '<span class="material-icons" style="font-size:17px;color:#F87171">person_remove</span></div>'
                                                )
                                                with ui.element("div"):
                                                    ui.html(f'<div style="font:700 14px var(--dmc-fd);color:var(--dmc-text)">Remover {u_nome}?</div>')
                                                    ui.html('<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:2px">Confirme com sua senha de administrador</div>')
                                            with ui.element("div").style("padding:20px 22px"):
                                                ui.html(
                                                    '<label class="gc-label" style="display:block;margin-bottom:6px">Sua senha</label>'
                                                    '<input id="del-pw" type="password" class="gc-input" placeholder="••••••••">'
                                                    '<div id="del-err" style="min-height:16px;color:#F87171;font:11px var(--dmc-fm);margin-top:6px"></div>'
                                                )
                                            with ui.element("div").style(
                                                "padding:12px 22px;border-top:1px solid var(--dmc-b1);"
                                                "display:flex;justify-content:flex-end;gap:8px;"
                                                "background:rgba(0,0,0,.1);"
                                            ):
                                                ui.button("Cancelar", on_click=dlg_conf.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

                                                async def _executar_del(uid2=u_id, unome2=u_nome):
                                                    from services.auth import check_login, current_user_name
                                                    pw = await ui.run_javascript("document.getElementById('del-pw').value")
                                                    if not check_login(current_user_name(), pw):
                                                        await ui.run_javascript(
                                                            "document.getElementById('del-err').textContent='Senha incorreta.';"
                                                            "document.getElementById('del-pw').value='';"
                                                            "document.getElementById('del-pw').focus();"
                                                        )
                                                        return
                                                    _save_users([x for x in _load_users() if x.get("id") != uid2])
                                                    dlg_conf.close()
                                                    ui.notify(f"'{unome2}' removido.", type="positive")
                                                    _render_users()

                                                ui.button("Confirmar remoção", on_click=_executar_del).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary').style(
                                                    "background:rgba(248,113,113,.15);border:1px solid rgba(248,113,113,.3);"
                                                    "color:#F87171;font-family:'DM Mono',monospace;font-size:12px;padding:0 16px;"
                                                )
                                            ui.run_javascript("setTimeout(function(){var p=document.getElementById('del-pw');if(p)p.focus();},200);")
                                        dlg_conf.open()

                                    del_btn = ui.element("button").classes("gc-icon-btn").style(
                                        "border-color:rgba(248,113,113,.3);color:#F87171;"
                                    )
                                    with del_btn:
                                        ui.html('<span class="material-icons" style="font-size:14px">person_remove</span>')
                                    del_btn.on("click", _confirmar_del)

            _render_users()

            # ════ COLUNA DIREITA — cadastrar novo usuário ════════════
            with ui.element("div").classes("gc-form-panel"):

                with ui.element("div").classes("gc-panel-hdr"):
                    ui.html('<span class="material-icons" style="font-size:13px;color:#4ADE80">person_add</span>')
                    ui.html("Cadastrar novo usuário")

                ui.html("""
<div class="gc-form-grid">
  <div class="gc-field">
    <label class="gc-label">Nome completo</label>
    <input class="gc-input" id="nu-nome" placeholder="Ex: João Silva" type="text" autofocus>
  </div>
  <div class="gc-field">
    <label class="gc-label">E-mail</label>
    <input class="gc-input" id="nu-email" placeholder="joao@email.com" type="email">
  </div>
  <div class="gc-field">
    <label class="gc-label">Telefone</label>
    <input class="gc-input" id="nu-tel" placeholder="(48) 9 9999-9999" type="tel">
  </div>
  <div class="gc-field">
    <label class="gc-label">Cargo / Função</label>
    <input class="gc-input" id="nu-cargo" placeholder="Ex: Técnico de Campo" type="text">
  </div>
  <div class="gc-field">
    <label class="gc-label">Senha</label>
    <input class="gc-input" id="nu-senha" placeholder="Mínimo 4 caracteres" type="password">
  </div>
  <div class="gc-field">
    <label class="gc-label">Confirmar senha</label>
    <input class="gc-input" id="nu-senha2" placeholder="Repita a senha" type="password">
  </div>
</div>
""")

                # Perfil de acesso
                with ui.element("div").classes("gc-perfil-wrap"):
                    ui.html(
                        '<div style="font:600 10px var(--dmc-mono);color:var(--dmc-muted2);'
                        'letter-spacing:.15em;text-transform:uppercase;'
                        'display:flex;align-items:center;gap:8px;margin-bottom:12px">'
                        '<span class="material-icons" style="font-size:13px">shield</span>'
                        'Perfil de acesso'
                        '<span style="flex:1;height:1px;background:var(--dmc-b1);display:inline-block"></span>'
                        '</div>'
                    )
                    ui.html(_pills_html("FUNCIONÁRIO", "nu-perfil"))

                # Footer: erro + botão salvar
                with ui.element("div").classes("gc-form-footer"):
                    ui.html('<span id="nu-err" style="color:#F87171;font:12px var(--dmc-fm);min-height:18px"></span>')

                    btn_salvar = ui.element("button").classes("dmc-btn dmc-btn-primary").style(
                        "padding:0 26px;flex-shrink:0;"
                    )
                    with btn_salvar:
                        ui.html('<span class="material-icons" style="font-size:15px">save</span>')
                        ui.html("Salvar usuário")

                    async def _salvar():
                        vals = await ui.run_javascript("""({
                          nome:   document.getElementById('nu-nome').value.trim(),
                          email:  document.getElementById('nu-email').value.trim(),
                          tel:    document.getElementById('nu-tel').value.trim(),
                          cargo:  document.getElementById('nu-cargo').value.trim(),
                          senha:  document.getElementById('nu-senha').value,
                          senha2: document.getElementById('nu-senha2').value,
                          perfil: document.getElementById('nu-perfil').value,
                        })""")

                        async def _err(msg):
                            await ui.run_javascript(f"document.getElementById('nu-err').textContent={repr(msg)}")

                        if not vals.get("nome"):
                            await _err("Preencha o nome."); return
                        if not vals.get("email"):
                            await _err("Preencha o e-mail."); return
                        if not vals.get("senha") or len(vals["senha"]) < 4:
                            await _err("Senha deve ter no mínimo 4 caracteres."); return
                        if vals["senha"] != vals["senha2"]:
                            await _err("As senhas não coincidem."); return

                        users = _load_users()
                        if any(u.get("email") == vals["email"] for u in users):
                            await _err("E-mail já cadastrado."); return

                        perfil = vals.get("perfil", "FUNCIONÁRIO")
                        users.append({
                            "id":         str(uuid.uuid4()),
                            "nome":       vals["nome"],
                            "email":      vals["email"],
                            "telefone":   vals.get("tel", ""),
                            "cargo":      vals.get("cargo", ""),
                            "senha_hash": _hash(vals["senha"]),
                            "perfil":     perfil,
                            "admin":      perfil in ("DESENVOLVEDOR", "ADMINISTRADOR"),
                        })
                        _save_users(users)

                        await ui.run_javascript("""
                          ['nu-nome','nu-email','nu-tel','nu-cargo','nu-senha','nu-senha2'].forEach(function(id){
                            var el=document.getElementById(id); if(el) el.value='';
                          });
                          document.getElementById('nu-err').textContent='';
                          var def=document.querySelector('[data-target="nu-perfil"][data-perfil="FUNCIONÁRIO"]');
                          if(def) gcSelectPerfil(def);
                        """)
                        ui.notify(f"✓ '{vals['nome']}' cadastrado!", type="positive")
                        _render_users()

                    btn_salvar.on("click", _salvar)

    # Anexa clicks nos pills do formulário de novo usuário + máscara de telefone
    ui.run_javascript("""
setTimeout(function(){
  document.querySelectorAll('[data-target="nu-perfil"]').forEach(function(c){
    c.addEventListener('click', function(){ gcSelectPerfil(c); });
  });
  var nuTel=document.getElementById('nu-tel');
  if(nuTel) nuTel.oninput=function(){ maskTelefone(this); };
}, 300);
""")
