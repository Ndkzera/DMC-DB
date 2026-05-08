"""Página de Registro de Campo — /campo"""

import asyncio
import base64
import json
from datetime import date, datetime

from nicegui import app as _app, ui

from config import FOTOS_PONTO_DIR
from services.agenda import fmt_event, get_events_for_month, is_connected
from services.ponto import add_registro, load_ponto
from ui.styles import BOOTSTRAP_CDN, CSS, UTILS_JS

_COLOR_MAP = {
    "1":"#a4bdfc","2":"#7ae7bf","3":"#dbadff","4":"#ff887c","5":"#fbd75b",
    "6":"#ffb878","7":"#46d6db","8":"#e1e1e1","9":"#5484ed","10":"#51b749","11":"#dc2127",
}
_DEF = "#4ADE80"

_PAGE_CSS = """
<style>
html, body, .nicegui-content {
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}
.campo-page {
  min-height: 100vh;
  width: 100%;
  background: var(--dmc-bg);
  display: flex;
  flex-direction: column;
}
.campo-header {
  position: sticky; top: 0; z-index: 100;
  background: var(--dmc-header-bg); backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--dmc-b1);
  padding: 0 24px;
  height: 64px;
  display: flex; align-items: center; gap: 16px;
  flex-shrink: 0;
}
.campo-body {
  flex: 1;
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 0;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 24px;
  box-sizing: border-box;
  align-items: flex-start;
}
.campo-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.campo-col:first-child {
  padding-right: 24px;
  border-right: 1px solid var(--dmc-b1);
}
.campo-col:last-child {
  padding-left: 24px;
}
@media (max-width: 768px) {
  .campo-body {
    grid-template-columns: 1fr;
    padding: 16px;
    padding-bottom: calc(24px + env(safe-area-inset-bottom, 0px));
    gap: 20px;
  }
  .campo-col:first-child {
    padding-right: 0;
    border-right: none;
    border-bottom: 1px solid var(--dmc-b1);
    padding-bottom: 20px;
  }
  .campo-col:last-child { padding-left: 0; }
  .campo-header {
    padding: 0 14px;
    height: 56px;
    gap: 10px;
  }
  .campo-header img { height: 28px !important; }
  .dmc-card-body { padding: 14px 16px !important; }
  .dmc-input { height: 48px !important; font-size: 15px !important; }
  .dmc-tipo-btn { height: 48px !important; font-size: 14px !important; }
}
.campo-section-title {
  font: 600 11px var(--dmc-mono);
  color: var(--dmc-muted2);
  letter-spacing: .14em;
  text-transform: uppercase;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.campo-evt {
  background: var(--dmc-bg2);
  border: 1px solid var(--dmc-b1);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 8px;
  transition: border-color .15s;
}
.campo-evt:hover { border-color: var(--dmc-b2); }
</style>
"""


@ui.page("/campo")
def campo_page():
    from services.auth import check_login, is_authenticated, current_user_name, current_user_perfil, logout_user

    # Sempre sincroniza com a sessão principal (garante troca de usuário)
    if is_authenticated():
        _app.storage.user["campo_usuario"] = current_user_name()

    username = _app.storage.user.get("campo_usuario", "")

    ui.dark_mode().enable()
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">')
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(UTILS_JS)
    ui.add_head_html(_PAGE_CSS)

    # ── Login de campo ────────────────────────────────────────────────
    if not username:
        with ui.element("div").style(
            "min-height:100vh;display:flex;align-items:center;justify-content:center;"
            "background:var(--dmc-bg);padding:24px;"
        ):
            with ui.element("div").style(
                "background:var(--dmc-bg2);border:1px solid var(--dmc-b1);border-radius:18px;"
                "padding:36px 32px;width:100%;max-width:380px;"
            ):
                ui.html(
                    '<img src="https://dmctopografia.com/wp-content/uploads/2023/03/Martins.png" '
                    'style="width:80px;margin:0 auto 18px;display:block;opacity:.9">'
                )
                ui.html(
                    '<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text);'
                    'text-align:center;margin-bottom:4px">Registro de Campo</div>'
                )
                ui.html(
                    '<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);'
                    'text-align:center;letter-spacing:.08em;margin-bottom:28px">Identifique-se para continuar</div>'
                )

                ui.html("""
<div style="margin-bottom:14px">
  <label style="display:block;font:10px 'DM Mono',monospace;color:var(--dmc-muted2);
    letter-spacing:.14em;text-transform:uppercase;margin-bottom:5px">Usuário / E-mail</label>
  <input id="cl-user" type="text" autocomplete="username" class="dmc-input"
    style="height:44px;font-size:14px;padding:9px 12px"
    placeholder="nome ou e-mail" />
</div>
<div style="margin-bottom:6px">
  <label style="display:block;font:10px 'DM Mono',monospace;color:var(--dmc-muted2);
    letter-spacing:.14em;text-transform:uppercase;margin-bottom:5px">Senha</label>
  <input id="cl-pass" type="password" autocomplete="current-password" class="dmc-input"
    style="height:44px;font-size:14px;padding:9px 12px"
    placeholder="••••••••" />
</div>
<div id="cl-err" style="min-height:18px;color:#F87171;font-size:12px;
  text-align:center;margin-bottom:10px"></div>
""")

                btn_entrar = ui.element("button").props('id="cl-btn-enter"').classes(
                    "dmc-btn dmc-btn-primary"
                ).style("width:100%;height:44px;margin-top:4px;border-radius:10px!important")
                with btn_entrar:
                    ui.html("Entrar")

                async def _fazer_login():
                    result = await ui.run_javascript(
                        "({u:document.getElementById('cl-user').value.trim(),"
                        " p:document.getElementById('cl-pass').value})"
                    )
                    user = check_login(result.get("u", ""), result.get("p", ""))
                    if user:
                        _app.storage.user["campo_usuario"] = user["nome"]
                        ui.navigate.to("/campo")
                    else:
                        await ui.run_javascript(
                            "document.getElementById('cl-err').textContent='Usuário ou senha incorretos';"
                            "document.getElementById('cl-pass').value='';"
                            "document.getElementById('cl-pass').focus();"
                        )

                btn_entrar.on("click", _fazer_login)

                ui.run_javascript("""
setTimeout(function(){
  var p=document.getElementById('cl-pass');
  var u=document.getElementById('cl-user');
  var btn=document.getElementById('cl-btn-enter');
  if(u) u.addEventListener('keydown',function(e){if(e.key==='Enter')p&&p.focus();});
  if(p) p.addEventListener('keydown',function(e){if(e.key==='Enter')btn&&btn.click();});
},300);
""")
        return

    today = date.today()
    _DIAS  = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
    _MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
              "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    data_label = f"{_DIAS[today.weekday()]}, {today.day} de {_MESES[today.month-1]}"

    def _user_in_event(description: str) -> bool:
        """Retorna True se o usuário logado está na Equipe (ou Responsável) do evento."""
        u = username.strip().lower()
        for line in (description or "").split("\n"):
            if line.startswith(("Equipe:", "Responsável:")):
                valor = line.split(":", 1)[1]
                membros = [m.strip().lower() for m in valor.split(",") if m.strip()]
                if u in membros:
                    return True
        return False

    def _get_modifier(description: str) -> str:
        for line in (description or "").split("\n"):
            if line.startswith("Modificador:"):
                return line.split(":", 1)[1].strip()
        return ""

    # ── Página principal ──────────────────────────────────────────────
    with ui.element("div").classes("campo-page"):

        # ── Header ───────────────────────────────────────────────────
        with ui.element("div").classes("campo-header"):
            ui.html(
                '<img src="https://dmctopografia.com/wp-content/uploads/2023/03/Martins.png" '
                'style="height:36px;opacity:.92;flex-shrink:0">'
            )
            with ui.element("div").style("display:flex;flex-direction:column;gap:1px;line-height:1"):
                ui.html('<span style="font:700 15px \'Syne\',sans-serif;color:var(--dmc-text)">Registro de Campo</span>')
                ui.html('<span style="font:10px \'Inter\',sans-serif;color:var(--dmc-muted2);letter-spacing:.1em;text-transform:uppercase">DMC Topografia</span>')
            ui.element("div").style("flex:1")
            ui.html(
                f'<div style="display:flex;align-items:center;gap:7px;padding:6px 12px;'
                f'background:rgba(74,222,128,.06);border:1px solid var(--dmc-gd);border-radius:20px">'
                f'<span class="material-icons" style="font-size:14px;color:var(--dmc-green)">person</span>'
                f'<span style="font:500 12px var(--dmc-fm);color:var(--dmc-text)">{username}</span>'
                f'</div>'
            )
            if current_user_perfil() == "FUNCIONÁRIO CAMPO":
                def _sair():
                    logout_user()
                    _app.storage.user.pop("campo_usuario", None)
                    ui.navigate.to("/login")
                ui.button(icon="logout", on_click=_sair).props(
                    'flat round dense'
                ).style("color:#F87171;margin-left:8px")
            else:
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
                    'flat round dense'
                ).style("color:var(--dmc-muted);margin-left:8px")

        # ── Body: 2 colunas ───────────────────────────────────────────
        with ui.element("div").classes("campo-body"):

            # ════ COLUNA ESQUERDA — Agenda do dia ════════════════════
            with ui.element("div").classes("campo-col"):
                ui.html(
                    f'<div class="campo-section-title">'
                    f'<span class="material-icons" style="font-size:14px;color:#FBBF24">today</span>'
                    f'Agenda do dia — {data_label}</div>'
                )
                agenda_area = ui.element("div")

            # ════ COLUNA DIREITA — Obras + Formulário ════════════════
            with ui.element("div").classes("campo-col"):

                # Obras atribuídas ao funcionário (populado por _load_agenda)
                obras_area = ui.element("div")

                ui.html(
                    '<div class="campo-section-title">'
                    '<span class="material-icons" style="font-size:14px;color:var(--dmc-green)">fingerprint</span>'
                    'Registrar Ponto</div>'
                )

                # Tipo Checkin / Checkout
                ui.html("""
                <div class="dmc-card">
                  <div class="dmc-card-hdr"><span class="material-icons">toggle_on</span> Tipo</div>
                  <div class="dmc-card-body" style="padding:14px 20px">
                    <div style="display:flex;gap:10px">
                      <button class="dmc-tipo-btn active" id="cp-btn-ci" data-tipo="checkin">
                        <span class="material-icons" style="font-size:16px">login</span>
                        <span>Check-in</span>
                      </button>
                      <button class="dmc-tipo-btn" id="cp-btn-co" data-tipo="checkout">
                        <span class="material-icons" style="font-size:16px">logout</span>
                        <span>Check-out</span>
                      </button>
                    </div>
                  </div>
                </div>
                """)

                # Hidden input — modifier is filled automatically from the agenda event
                ui.html('<input type="hidden" id="cp-modificador" value="">')

                # Dados da obra
                ui.html("""
                <div class="dmc-card">
                  <div class="dmc-card-hdr"><span class="material-icons">construction</span> Obra</div>
                  <div class="dmc-card-body">
                    <div style="margin-bottom:12px">
                      <label class="dmc-label">Nome da Obra</label>
                      <input class="dmc-input" id="cp-obra" placeholder="Ex: Residência Silva">
                    </div>
                    <div>
                      <label class="dmc-label">Localização</label>
                      <input class="dmc-input" id="cp-local" placeholder="Ex: Rua das Flores, 100 — Florianópolis">
                    </div>
                  </div>
                </div>
                """)

                # Foto / Observações / Imagens — id no HTML puro, sem wrapper Vue
                ui.html("""
<div id="cp-photos-section" style="display:none;flex-direction:column;gap:16px;width:100%">

  <div class="dmc-card">
    <div class="dmc-card-hdr"><span class="material-icons">photo_camera</span> Foto</div>
    <div class="dmc-card-body">
      <div id="cp-preview-wrap" style="display:none;margin-bottom:12px">
        <img id="cp-preview" style="width:100%;max-height:260px;object-fit:cover;
          border-radius:10px;border:1px solid var(--dmc-b1)">
      </div>
      <div id="cp-photo-lbl" style="display:flex;align-items:center;
        justify-content:center;gap:10px;height:88px;border:1.5px dashed var(--dmc-b2);
        border-radius:12px;cursor:pointer;background:var(--dmc-bg)">
        <span class="material-icons" style="font-size:22px;color:var(--dmc-muted2)">add_a_photo</span>
        <div>
          <div style="font:500 13px var(--dmc-fm);color:var(--dmc-muted2)">Tirar foto / Selecionar</div>
          <div id="cp-photo-name" style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:2px">JPG, PNG ou WEBP</div>
        </div>
        <input type="file" id="cp-photo" accept="image/*" style="display:none">
      </div>
    </div>
  </div>

  <div class="dmc-card">
    <div class="dmc-card-hdr"><span class="material-icons">notes</span> Observações</div>
    <div class="dmc-card-body">
      <textarea id="cp-obs" class="dmc-input" rows="3"
        placeholder="Informações adicionais sobre a obra, condições do terreno, etc."
        style="height:auto;min-height:80px;resize:vertical;padding:10px 12px;line-height:1.5"></textarea>
    </div>
  </div>

  <div class="dmc-card">
    <div class="dmc-card-hdr"><span class="material-icons">photo_library</span> Imagens Adicionais</div>
    <div class="dmc-card-body">
      <div id="cp-extra-preview" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px"></div>
      <div id="cp-extra-lbl" style="display:flex;align-items:center;
        justify-content:center;gap:10px;height:60px;border:1.5px dashed var(--dmc-b2);
        border-radius:12px;cursor:pointer;background:var(--dmc-bg)">
        <span class="material-icons" style="font-size:20px;color:var(--dmc-muted2)">add_photo_alternate</span>
        <span style="font:500 12px var(--dmc-fm);color:var(--dmc-muted2)">Adicionar imagens</span>
        <input type="file" id="cp-extra-photos" accept="image/*" multiple style="display:none">
      </div>
    </div>
  </div>

</div>
                """)

                # Data/hora + botão
                with ui.element("div").style(
                    "display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;"
                ):
                    ui.html(
                        '<div style="display:flex;align-items:center;gap:8px;padding:10px 14px;'
                        'background:var(--dmc-bg2);border:1px solid var(--dmc-b1);border-radius:10px;flex:1">'
                        '<span class="material-icons" style="font-size:16px;color:var(--dmc-muted2)">schedule</span>'
                        '<span id="cp-dt" style="font:12px var(--dmc-mono);color:var(--dmc-muted2)">—</span>'
                        '</div>'
                    )

                    async def registrar():
                        vals = await ui.run_javascript("""
                        new Promise(function(resolve){
                          function _rb64(file){
                            return new Promise(function(res){
                              var r=new FileReader();
                              r.onload=function(e){res(e.target.result);};
                              r.readAsDataURL(file);
                            });
                          }
                          var fi=document.getElementById('cp-photo');
                          var fiex=document.getElementById('cp-extra-photos');
                          var data={
                            tipo:(document.querySelector('.dmc-tipo-btn.active[id^=cp-btn]')?.dataset?.tipo)||'checkin',
                            modificador:(document.getElementById('cp-modificador')?.value||'').trim(),
                            obra:(document.getElementById('cp-obra')?.value||'').trim(),
                            local:(document.getElementById('cp-local')?.value||'').trim(),
                            obs:(document.getElementById('cp-obs')?.value||'').trim(),
                            photo_name:fi&&fi.files[0]?fi.files[0].name:null,
                            photo_b64:null,
                            extra_photos:[]
                          };
                          var tasks=[];
                          if(fi&&fi.files[0])
                            tasks.push(_rb64(fi.files[0]).then(function(b64){data.photo_b64=b64;}));
                          if(fiex&&fiex.files.length)
                            Array.from(fiex.files).forEach(function(f){
                              tasks.push(_rb64(f).then(function(b64){
                                data.extra_photos.push({name:f.name,b64:b64});
                              }));
                            });
                          Promise.all(tasks).then(function(){resolve(data);});
                        })
                        """)

                        if not vals or not isinstance(vals, dict):
                            ui.notify("Erro ao coletar dados. Tente novamente.", type="negative")
                            print(f"[campo] registrar: vals inválido: {vals!r}")
                            return

                        if not vals.get("obra"):
                            ui.notify("Preencha o nome da obra.", type="warning")
                            return

                        now = datetime.now()
                        ts  = now.strftime("%Y%m%d%H%M%S")

                        # Pasta da obra dentro de fotos_ponto
                        _inv = set(r'\/:*?"<>|')
                        _safe_obra = "".join(c for c in vals["obra"] if c not in _inv).strip() or "outros"
                        obra_dir = FOTOS_PONTO_DIR / _safe_obra
                        imgs_dir = obra_dir / "Imagens"
                        print(f"[campo] salvando em: {obra_dir}")
                        try:
                            obra_dir.mkdir(parents=True, exist_ok=True)
                            imgs_dir.mkdir(exist_ok=True)
                        except Exception as _e:
                            ui.notify(f"Erro ao criar pasta: {_e}", type="negative")
                            print(f"[campo] erro mkdir: {_e} | path={obra_dir}")
                            return

                        foto_path = ""
                        if vals.get("photo_b64"):
                            try:
                                header, encoded = vals["photo_b64"].split(",", 1)
                                ext = ".jpg"
                                if "png" in header: ext = ".png"
                                elif "webp" in header: ext = ".webp"
                                safe_user = "".join(c for c in username if c.isalnum() or c in "_-")[:20]
                                fname = f"{ts}_{safe_user}{ext}"
                                (imgs_dir / fname).write_bytes(base64.b64decode(encoded))
                                foto_path = str(imgs_dir / fname)
                            except Exception as _e:
                                print(f"[campo] erro foto: {_e}")

                        obs_text = vals.get("obs", "").strip()
                        if obs_text:
                            try:
                                (obra_dir / f"{ts}_obs.txt").write_text(obs_text, encoding="utf-8")
                            except Exception as _e:
                                print(f"[campo] erro obs: {_e}")

                        extra_paths = []
                        for i, ep in enumerate(vals.get("extra_photos", []), 1):
                            try:
                                header, encoded = ep["b64"].split(",", 1)
                                ext = ".jpg"
                                if "png" in header: ext = ".png"
                                elif "webp" in header: ext = ".webp"
                                fname = f"{ts}_img_{i:02d}{ext}"
                                (imgs_dir / fname).write_bytes(base64.b64decode(encoded))
                                extra_paths.append(str(imgs_dir / fname))
                            except Exception as _e:
                                print(f"[campo] erro img {i}: {_e}")

                        add_registro({
                            "id":               ts,
                            "usuario":          username,
                            "equipe":           "usuário",
                            "tipo":             vals.get("tipo", "checkin"),
                            "modificador":      vals.get("modificador", ""),
                            "obra":             vals["obra"],
                            "local":            vals.get("local", ""),
                            "foto":             foto_path,
                            "observacoes":      obs_text,
                            "fotos_adicionais": extra_paths,
                            "data":             now.strftime("%d/%m/%Y"),
                            "hora":             now.strftime("%H:%M:%S"),
                            "timestamp":        now.isoformat(),
                        })

                        tipo_label = "Check-in" if vals.get("tipo") == "checkin" else "Check-out"
                        ui.notify(f"✓ {tipo_label} registrado — {now.strftime('%H:%M')}", type="positive")

                        if vals.get("tipo") == "checkout":
                            await _load_agenda()

                        await ui.run_javascript("""
                        document.getElementById('cp-obra').value='';
                        document.getElementById('cp-local').value='';
                        document.getElementById('cp-modificador').value='';
                        document.getElementById('cp-photo').value='';
                        document.getElementById('cp-preview-wrap').style.display='none';
                        document.getElementById('cp-photo-name').textContent='JPG, PNG ou WEBP';
                        var lbl=document.getElementById('cp-photo-lbl');
                        if(lbl) lbl.style.height='88px';
                        var obs=document.getElementById('cp-obs');
                        if(obs) obs.value='';
                        var ep=document.getElementById('cp-extra-photos');
                        if(ep) ep.value='';
                        var epv=document.getElementById('cp-extra-preview');
                        if(epv) epv.innerHTML='';
                        var sec=document.getElementById('cp-photos-section');
                        if(sec) sec.style.display='none';
                        """)

                    ui.button("Registrar", icon="check", on_click=registrar).props(
                        'unelevated no-caps'
                    ).classes('dmc-btn dmc-btn-primary').style("padding:0 28px;height:42px")

    # ── Carrega agenda e obras atribuídas ─────────────────────────────
    async def _load_agenda():
        agenda_area.clear()
        obras_area.clear()
        user_obras: list = []

        with agenda_area:
            if not is_connected():
                with ui.element("div").style(
                    "padding:20px;text-align:center;background:var(--dmc-bg2);"
                    "border:1px solid var(--dmc-b1);border-radius:12px;"
                ):
                    ui.html('<span class="material-icons" style="font-size:32px;color:var(--dmc-b2)">calendar_off</span>')
                    ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:8px">Google Agenda não conectado.</div>')
            else:
                try:
                    raw = await asyncio.to_thread(get_events_for_month, today.year, today.month)
                    hoje_str = today.isoformat()
                    eventos = sorted(
                        [fmt_event(e) for e in raw if fmt_event(e).get("date_key") == hoje_str],
                        key=lambda e: e.get("time_str", "")
                    )
                    user_obras = [ev for ev in eventos if _user_in_event(ev.get("description", ""))]
                    if not user_obras:
                        with ui.element("div").style(
                            "padding:28px 16px;text-align:center;"
                            "background:var(--dmc-bg2);border:1px dashed var(--dmc-b1);border-radius:12px;"
                        ):
                            ui.html('<span class="material-icons" style="font-size:32px;color:var(--dmc-b2)">event_busy</span>')
                            ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:8px">Sem obras atribuídas para hoje.</div>')
                    else:
                        for ev in user_obras:
                            dot = _COLOR_MAP.get(ev["color"], _DEF)
                            with ui.element("div").classes("campo-evt").style(f"border-left:3px solid {dot};"):
                                ui.html(f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text);margin-bottom:5px">{ev["title"]}</div>')
                                ui.html(
                                    f'<div style="display:flex;align-items:center;gap:5px;font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                                    f'<span class="material-icons" style="font-size:12px">schedule</span>{ev["time_str"]}</div>'
                                )
                                if ev.get("location"):
                                    ui.html(
                                        f'<div style="display:flex;align-items:center;gap:5px;'
                                        f'font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:3px">'
                                        f'<span class="material-icons" style="font-size:12px">location_on</span>{ev["location"]}</div>'
                                    )
                                if ev.get("description"):
                                    desc = ev["description"][:120] + ("…" if len(ev["description"]) > 120 else "")
                                    ui.html(f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:4px;line-height:1.45">{desc}</div>')
                except Exception as exc:
                    ui.html(f'<div style="color:#F87171;font:12px var(--dmc-fm);padding:12px">Erro ao carregar agenda: {exc}</div>')

        # ── Obras atribuídas ao funcionário (filtra já registradas) ───
        with obras_area:
            if not user_obras:
                return

            # Count complete sessions (checkin + checkout pair) per obra today
            from collections import Counter
            hoje_data = today.strftime("%d/%m/%Y")
            registros_hoje = [
                r for r in load_ponto()
                if r.get("usuario") == username and r.get("data") == hoje_data
            ]
            checkins_count: Counter = Counter(
                r["obra"] for r in registros_hoje if r.get("tipo") == "checkin"
            )
            checkouts_count: Counter = Counter(
                r["obra"] for r in registros_hoje if r.get("tipo") == "checkout"
            )
            # Only a complete pair (checkin + checkout) removes an event slot
            completed: Counter = Counter(
                {obra: min(checkins_count[obra], checkouts_count[obra])
                 for obra in checkins_count}
            )

            # Remove one slot per complete session (handles duplicate event titles)
            pending_obras = []
            for ev in user_obras:
                nome = ev["title"]
                if completed[nome] > 0:
                    completed[nome] -= 1
                else:
                    pending_obras.append(ev)

            if not pending_obras:
                return

            ui.html(
                '<div class="campo-section-title" style="margin-bottom:10px">'
                '<span class="material-icons" style="font-size:14px;color:#60A5FA">assignment_ind</span>'
                'Obras do dia — clique para preencher</div>'
            )
            for ev in pending_obras:
                dot = _COLOR_MAP.get(ev["color"], _DEF)
                obra_nome  = ev["title"]
                obra_local = ev.get("location", "")
                obra_hora  = ev.get("time_str", "")
                obra_mod   = _get_modifier(ev.get("description", ""))
                with ui.element("div").style(
                    f"background:var(--dmc-bg2);border:1px solid var(--dmc-b1);"
                    f"border-left:3px solid {dot};border-radius:10px;"
                    f"padding:11px 14px;margin-bottom:8px;"
                ):
                    with ui.element("div").style(
                        "display:flex;align-items:flex-start;justify-content:space-between;gap:10px"
                    ):
                        with ui.element("div").style("flex:1;min-width:0"):
                            ui.html(
                                f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text);'
                                f'margin-bottom:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                f'{obra_nome}</div>'
                            )
                            if obra_hora:
                                ui.html(
                                    f'<div style="display:flex;align-items:center;gap:5px;'
                                    f'font:11px var(--dmc-mono);color:var(--dmc-muted2);margin-bottom:2px">'
                                    f'<span class="material-icons" style="font-size:12px">schedule</span>'
                                    f'{obra_hora}</div>'
                                )
                            if obra_local:
                                ui.html(
                                    f'<div style="display:flex;align-items:center;gap:5px;'
                                    f'font:11px var(--dmc-fm);color:var(--dmc-muted2);'
                                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                    f'<span class="material-icons" style="font-size:12px">location_on</span>'
                                    f'{obra_local}</div>'
                                )
                        btn_fill = ui.element("button").style(
                            "padding:5px 10px;background:rgba(96,165,250,.12);"
                            "border:1px solid rgba(96,165,250,.3);border-radius:7px;"
                            "font:600 10px var(--dmc-mono);color:#60A5FA;cursor:pointer;"
                            "letter-spacing:.05em;white-space:nowrap;flex-shrink:0;transition:all .15s;"
                        )
                        with btn_fill:
                            ui.html('<span class="material-icons" style="font-size:13px;vertical-align:middle;margin-right:3px">edit_note</span>Usar')
                        btn_fill.on("click", lambda o=obra_nome, l=obra_local, m=obra_mod: ui.run_javascript(
                            f"cpShowTypePicker({json.dumps(o)},{json.dumps(l)},{json.dumps(m)});"
                        ))
            ui.element("div").style(
                "border-bottom:1px solid var(--dmc-b1);margin:4px 0 14px"
            )

    ui.timer(0.1, _load_agenda, once=True)

    # ── Popup seleção de tipo (checkin/checkout) ──────────────────────
    ui.html("""
<div id="cp-type-picker" style="display:none;position:fixed;inset:0;z-index:9999;
  background:rgba(0,0,0,.55);align-items:center;justify-content:center">
  <div style="background:var(--dmc-bg2);border:1px solid var(--dmc-b1);border-radius:18px;
    padding:24px 22px;width:90%;max-width:310px;box-shadow:0 24px 64px rgba(0,0,0,.45)">
    <div style="font:600 13px var(--dmc-mono);color:var(--dmc-muted2);letter-spacing:.12em;
      text-transform:uppercase;text-align:center;margin-bottom:8px">Tipo de Registro</div>
    <div id="cp-type-obra-name" style="font:500 13px var(--dmc-fm);color:var(--dmc-text);
      text-align:center;margin-bottom:20px;overflow:hidden;text-overflow:ellipsis;
      white-space:nowrap"></div>
    <div style="display:flex;gap:10px">
      <button id="cp-type-ci" style="flex:1;display:flex;flex-direction:column;align-items:center;
        gap:7px;padding:14px 8px;background:rgba(74,222,128,.08);
        border:1.5px solid var(--dmc-gd);border-radius:12px;cursor:pointer;transition:all .15s">
        <span class="material-icons" style="font-size:22px;color:var(--dmc-green)">login</span>
        <span style="font:600 12px var(--dmc-fm);color:var(--dmc-text)">Check-in</span>
      </button>
      <button id="cp-type-co" style="flex:1;display:flex;flex-direction:column;align-items:center;
        gap:7px;padding:14px 8px;background:rgba(96,165,250,.08);
        border:1.5px solid rgba(96,165,250,.35);border-radius:12px;cursor:pointer;transition:all .15s">
        <span class="material-icons" style="font-size:22px;color:#60A5FA">logout</span>
        <span style="font:600 12px var(--dmc-fm);color:var(--dmc-text)">Check-out</span>
      </button>
    </div>
    <button id="cp-type-cancel" style="width:100%;margin-top:12px;padding:9px;
      background:transparent;border:1px solid var(--dmc-b1);border-radius:10px;
      font:500 12px var(--dmc-fm);color:var(--dmc-muted2);cursor:pointer">
      Cancelar
    </button>
  </div>
</div>
""")

    # JS: tipo toggle + relógio + foto preview + picker
    ui.run_javascript("""
    setTimeout(function(){
      document.querySelectorAll('[id^=cp-btn]').forEach(function(b){
        b.onclick=function(){
          document.querySelectorAll('[id^=cp-btn]').forEach(function(x){x.classList.remove('active');});
          b.classList.add('active');
        };
      });

      // ── Type picker popup ────────────────────────────────────────────
      var _cpPending={o:'',l:'',m:''};
      window.cpShowTypePicker=function(o,l,m){
        _cpPending={o:o,l:l,m:m};
        var nm=document.getElementById('cp-type-obra-name');
        if(nm) nm.textContent=o;
        var pk=document.getElementById('cp-type-picker');
        if(pk){ pk.style.display='flex'; }
      };
      function cpHidePicker(){ var pk=document.getElementById('cp-type-picker'); if(pk) pk.style.display='none'; }
      function cpTogglePhotos(){
        var obra=(document.getElementById('cp-obra')?.value||'').trim();
        var sec=document.getElementById('cp-photos-section');
        if(sec) sec.style.display=obra?'flex':'none';
      }
      var _obraInput=document.getElementById('cp-obra');
      if(_obraInput) _obraInput.addEventListener('input', cpTogglePhotos);

      function cpApplyType(tipo){
        cpHidePicker();
        document.querySelectorAll('[id^=cp-btn]').forEach(function(x){x.classList.remove('active');});
        var btn=tipo==='checkin'?document.getElementById('cp-btn-ci'):document.getElementById('cp-btn-co');
        if(btn) btn.classList.add('active');
        var oi=document.getElementById('cp-obra');  if(oi) oi.value=_cpPending.o;
        var li=document.getElementById('cp-local'); if(li) li.value=_cpPending.l;
        var mi=document.getElementById('cp-modificador'); if(mi) mi.value=_cpPending.m;
        oi&&oi.scrollIntoView({behavior:'smooth',block:'nearest'});
        cpTogglePhotos();
      }
      var ci=document.getElementById('cp-type-ci');    if(ci) ci.onclick=function(){cpApplyType('checkin');};
      var co=document.getElementById('cp-type-co');    if(co) co.onclick=function(){cpApplyType('checkout');};
      var cc=document.getElementById('cp-type-cancel');if(cc) cc.onclick=cpHidePicker;
      var pk=document.getElementById('cp-type-picker');
      if(pk) pk.onclick=function(e){if(e.target===this) cpHidePicker();};
      // ────────────────────────────────────────────────────────────────
      (function tick(){
        var el=document.getElementById('cp-dt');
        if(el){
          var d=new Date();
          el.textContent=d.toLocaleDateString('pt-BR')+' · '+d.toLocaleTimeString('pt-BR');
          setTimeout(tick,1000);
        }
      })();
      // Programmatic click — input.click() inside a click handler IS a trusted user gesture
      var _pLbl=document.getElementById('cp-photo-lbl');
      var _pInp=document.getElementById('cp-photo');
      if(_pLbl&&_pInp) _pLbl.addEventListener('click',function(){ _pInp.click(); });
      var _eLbl=document.getElementById('cp-extra-lbl');
      var _eInp=document.getElementById('cp-extra-photos');
      if(_eLbl&&_eInp) _eLbl.addEventListener('click',function(){ _eInp.click(); });

      var fi=document.getElementById('cp-photo');
      if(fi){
        fi.onchange=function(){
          if(fi.files[0]){
            var r=new FileReader();
            r.onload=function(e){
              var img=document.getElementById('cp-preview');
              var wrap=document.getElementById('cp-preview-wrap');
              var nm=document.getElementById('cp-photo-name');
              var lbl=document.getElementById('cp-photo-lbl');
              if(img) img.src=e.target.result;
              if(wrap) wrap.style.display='block';
              if(nm) nm.textContent=fi.files[0].name;
              if(lbl) lbl.style.height='40px';
            };
            r.readAsDataURL(fi.files[0]);
          }
        };
      }
      var fiex=document.getElementById('cp-extra-photos');
      if(fiex){
        fiex.onchange=function(){
          var prev=document.getElementById('cp-extra-preview');
          if(!prev) return;
          prev.innerHTML='';
          Array.from(fiex.files).forEach(function(f){
            var r=new FileReader();
            r.onload=function(e){
              var img=document.createElement('img');
              img.src=e.target.result;
              img.style.cssText='width:64px;height:64px;object-fit:cover;border-radius:8px;border:1px solid var(--dmc-b1)';
              prev.appendChild(img);
            };
            r.readAsDataURL(f);
          });
        };
      }
    }, 120);
    """)
