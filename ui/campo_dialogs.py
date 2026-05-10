"""Diálogos de Campo — Agenda do Dia, Checkin/Checkout, Histórico."""

import asyncio
import base64
import json as _json
from datetime import date, datetime

from nicegui import app as _app, ui

from config import FOTOS_PONTO_DIR
from services.agenda import fmt_event, get_events_for_month, is_connected
from services.auth import current_user_label, current_user_name, current_user_perfil
from services.ponto import add_registro, delete_registro, load_ponto
from ui.agenda_dialogs import conectar_agenda_dialog

_TIPO_COLOR = {
    "checkin":  ("#4ADE80", "#14532D", "Check-in"),
    "checkout": ("#60A5FA", "#1E3A5F", "Check-out"),
}

_COLOR_MAP = {
    "1":"#a4bdfc","2":"#7ae7bf","3":"#dbadff","4":"#ff887c","5":"#fbd75b",
    "6":"#ffb878","7":"#46d6db","8":"#e1e1e1","9":"#5484ed","10":"#51b749","11":"#dc2127",
}
_DEF_COLOR = "#4ADE80"


def _usuario_no_evento(description: str, username: str) -> bool:
    """Retorna True se username está na linha Equipe: ou Responsável: do evento."""
    u = username.strip().lower()
    if not u:
        return False
    for line in (description or "").split("\n"):
        if line.startswith(("Equipe:", "Responsável:")):
            valor = line.split(":", 1)[1]
            membros = [m.strip().lower() for m in valor.split(",") if m.strip()]
            if u in membros:
                return True
    return False


# ── Definir / obter usuário ────────────────────────────────────────────

def _get_username() -> str:
    return _app.storage.browser.get("dmc_usuario", "")


def _set_username_dialog(on_confirm) -> None:
    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:16px!important;padding:0;min-width:360px;color:var(--dmc-text)!important;"
    ):
        with ui.element("div").style(
            "padding:18px 22px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:12px;"
        ):
            ui.html(
                '<div style="width:36px;height:36px;border-radius:9px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid var(--dmc-gd);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:18px;color:var(--dmc-green)">badge</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 15px var(--dmc-fd);color:var(--dmc-text)">Identificação</div>')
                ui.html('<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2)">Como você quer ser identificado?</div>')

        with ui.element("div").style("padding:20px 22px"):
            ui.html('<label class="dmc-label">Seu nome</label>')
            nome_inp = ui.input(placeholder="Ex: João Silva").props(
                'outlined dense id="set-username-inp"'
            ).style(
                "background:var(--dmc-bg)!important;color:var(--dmc-text)!important;"
                "font-family:'Inter',sans-serif!important;width:100%;"
            )

        with ui.element("div").style(
            "padding:12px 22px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:8px;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            def _confirmar():
                nome = nome_inp.value.strip()
                if not nome:
                    ui.notify("Digite seu nome.", type="warning")
                    return
                _app.storage.browser["dmc_usuario"] = nome
                dlg.close()
                on_confirm()

            ui.button("Confirmar", on_click=_confirmar).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary').style(
                "font-family:'DM Mono',monospace;font-weight:600"
            )
    dlg.open()


# ── Agenda de Campo ───────────────────────────────────────────────────

def agenda_campo_dialog() -> None:
    if not is_connected():
        conectar_agenda_dialog()
        return

    today = date.today()
    _DIAS  = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
    _MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
              "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    titulo_data = f"{_DIAS[today.weekday()]}, {today.day} de {_MESES[today.month-1]}"

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(800px,97vw)!important;max-height:85vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        ui.button(icon="close", on_click=dlg.close).props('flat round dense').style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">today</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 15px var(--dmc-fd);color:var(--dmc-text)">Agenda de Campo</div>')
                ui.html(f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">{titulo_data}</div>')

        list_area = ui.element("div").style("padding:16px 20px;overflow-y:auto;flex:1")

        async def _carregar():
            list_area.clear()
            username = current_user_name()
            perfil   = current_user_perfil()
            admin    = perfil in ("DESENVOLVEDOR", "ADMINISTRADOR")

            with list_area:
                try:
                    raw = await asyncio.to_thread(get_events_for_month, today.year, today.month)
                    hoje_str = today.isoformat()
                    todos_hoje = [
                        fmt_event(e) for e in raw
                        if fmt_event(e).get("date_key") == hoje_str
                    ]
                    # Filtra por equipe (admin vê tudo)
                    eventos_hoje = todos_hoje if admin else [
                        ev for ev in todos_hoje
                        if _usuario_no_evento(ev.get("description", ""), username)
                    ]
                    eventos_hoje.sort(key=lambda e: e.get("time_str", ""))

                    if not eventos_hoje:
                        with ui.element("div").style("text-align:center;padding:40px 0"):
                            ui.html('<span class="material-icons" style="font-size:36px;color:var(--dmc-b2)">event_busy</span>')
                            msg = "Sem eventos hoje." if admin else "Nenhum evento atribuído a você hoje."
                            ui.html(f'<div style="font:13px var(--dmc-fm);color:var(--dmc-muted2);margin-top:10px">{msg}</div>')
                    else:
                        ui.html(
                            f'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                            f'letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px">'
                            f'{len(eventos_hoje)} evento(s) hoje</div>'
                        )
                        for ev in eventos_hoje:
                            dot = _COLOR_MAP.get(ev["color"], _DEF_COLOR)
                            with ui.element("div").style(
                                f"background:var(--dmc-bg3);border:1px solid var(--dmc-b1);"
                                f"border-left:3px solid {dot};border-radius:10px;"
                                f"padding:12px 14px;margin-bottom:8px;"
                            ):
                                ui.html(f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text);margin-bottom:4px">{ev["title"]}</div>')
                                ui.html(
                                    f'<div style="display:flex;align-items:center;gap:5px;'
                                    f'font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                                    f'<span class="material-icons" style="font-size:12px">schedule</span>'
                                    f'{ev["time_str"]}</div>'
                                )
                                if ev.get("location"):
                                    ui.html(
                                        f'<div style="display:flex;align-items:center;gap:5px;'
                                        f'font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:3px">'
                                        f'<span class="material-icons" style="font-size:12px">location_on</span>'
                                        f'{ev["location"]}</div>'
                                    )
                                if ev.get("description"):
                                    desc = ev["description"][:100] + ("…" if len(ev["description"]) > 100 else "")
                                    ui.html(f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:4px">{desc}</div>')

                except Exception as exc:
                    ui.html(f'<div style="color:#F87171;font:12px var(--dmc-fm)">Erro ao carregar: {exc}</div>')

    dlg.open()
    ui.timer(0.05, _carregar, once=True)


# ── Checkin / Checkout ────────────────────────────────────────────────

def checkin_dialog() -> None:
    username = _get_username()
    if not username:
        _set_username_dialog(checkin_dialog)
        return

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(640px,97vw)!important;max-height:92vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        ui.button(icon="close", on_click=dlg.close).props('flat round dense').style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid var(--dmc-gd);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:var(--dmc-green)">fingerprint</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 15px var(--dmc-fd);color:var(--dmc-text)">Registro de Campo</div>')
                ui.html(f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">Equipe · {username}</div>')

        with ui.element("div").style("padding:22px 24px;overflow-y:auto;flex:1"):

            # ── Tipo: Checkin / Checkout ──────────────────────────────
            ui.html("""
            <div style="margin-bottom:20px">
              <div class="dmc-label" style="margin-bottom:10px">Tipo de Registro</div>
              <div style="display:flex;gap:10px">
                <button class="dmc-tipo-btn active" id="ponto-btn-ci" data-tipo="checkin">
                  <span class="material-icons" style="font-size:16px">login</span>
                  <span>Check-in</span>
                </button>
                <button class="dmc-tipo-btn" id="ponto-btn-co" data-tipo="checkout">
                  <span class="material-icons" style="font-size:16px">logout</span>
                  <span>Check-out</span>
                </button>
              </div>
            </div>
            """)

            # ── Dados da obra ─────────────────────────────────────────
            ui.html(f"""
            <div class="dmc-card" style="margin-bottom:16px">
              <div class="dmc-card-hdr">
                <span class="material-icons">construction</span> Obra
              </div>
              <div class="dmc-card-body">
                <div style="margin-bottom:12px">
                  <label class="dmc-label">Nome da Obra</label>
                  <input class="dmc-input" id="ponto-obra" placeholder="Ex: Residência Silva">
                </div>
                <div>
                  <label class="dmc-label">Localização</label>
                  <input class="dmc-input" id="ponto-local" placeholder="Ex: Rua das Flores, 100 — Florianópolis">
                </div>
              </div>
            </div>
            """)

            # ── Foto ──────────────────────────────────────────────────
            ui.html("""
            <div class="dmc-card" style="margin-bottom:16px">
              <div class="dmc-card-hdr">
                <span class="material-icons">photo_camera</span> Foto
              </div>
              <div class="dmc-card-body">
                <div id="ponto-preview-wrap" style="display:none;margin-bottom:12px">
                  <img id="ponto-preview" style="width:100%;max-height:220px;object-fit:cover;
                    border-radius:8px;border:1px solid var(--dmc-b1)">
                </div>
                <label style="display:flex;align-items:center;justify-content:center;gap:8px;
                  height:80px;border:1.5px dashed var(--dmc-b2);border-radius:10px;
                  cursor:pointer;transition:all .2s;background:var(--dmc-bg)"
                  id="ponto-photo-lbl">
                  <span class="material-icons" style="color:var(--dmc-muted2)">add_a_photo</span>
                  <span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Toque para tirar foto ou selecionar</span>
                  <input type="file" id="ponto-photo" accept="image/*" capture="environment"
                    style="display:none">
                </label>
              </div>
            </div>
            """)

            # ── Data/hora (leitura) ───────────────────────────────────
            ui.html("""
            <div style="display:flex;align-items:center;gap:8px;padding:10px 14px;
              background:rgba(255,255,255,.03);border:1px solid var(--dmc-b1);border-radius:10px">
              <span class="material-icons" style="font-size:16px;color:var(--dmc-muted2)">schedule</span>
              <span id="ponto-dt" style="font:12px var(--dmc-mono);color:var(--dmc-muted2)">—</span>
            </div>
            """)

        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def registrar():
                vals = await ui.run_javascript("""
                new Promise(function(resolve){
                  var fi = document.getElementById('ponto-photo');
                  var data = {
                    tipo:  (document.querySelector('.dmc-tipo-btn.active[id^=ponto]')?.dataset?.tipo)||'checkin',
                    obra:  (document.getElementById('ponto-obra')?.value||'').trim(),
                    local: (document.getElementById('ponto-local')?.value||'').trim(),
                    photo_name: fi&&fi.files[0]?fi.files[0].name:null,
                    photo_b64: null
                  };
                  if(fi&&fi.files[0]){
                    var r=new FileReader();
                    r.onload=function(e){data.photo_b64=e.target.result;resolve(data);};
                    r.readAsDataURL(fi.files[0]);
                  } else { resolve(data); }
                })
                """)

                if not vals.get("obra"):
                    ui.notify("Preencha o nome da obra.", type="warning")
                    return

                now = datetime.now()
                ts  = now.strftime("%Y%m%d%H%M%S")
                foto_path = ""

                if vals.get("photo_b64"):
                    try:
                        header, encoded = vals["photo_b64"].split(",", 1)
                        ext = ".jpg"
                        if "png" in header:  ext = ".png"
                        elif "webp" in header: ext = ".webp"
                        safe_user = "".join(c for c in username if c.isalnum() or c in "_-")[:20]
                        fname = f"{ts}_{safe_user}{ext}"
                        (FOTOS_PONTO_DIR / fname).write_bytes(base64.b64decode(encoded))
                        foto_path = str(FOTOS_PONTO_DIR / fname)
                    except Exception:
                        foto_path = ""

                registro = {
                    "id":        ts,
                    "usuario":   username,
                    "equipe":    "usuário",
                    "tipo":      vals.get("tipo", "checkin"),
                    "obra":      vals["obra"],
                    "local":     vals.get("local", ""),
                    "foto":      foto_path,
                    "data":      now.strftime("%d/%m/%Y"),
                    "hora":      now.strftime("%H:%M:%S"),
                    "timestamp": now.isoformat(),
                }
                add_registro(registro, perfil=current_user_perfil())

                tipo_label = "Check-in" if registro["tipo"] == "checkin" else "Check-out"
                ui.notify(f"✓ {tipo_label} registrado — {now.strftime('%H:%M')}", type="positive")
                dlg.close()

            ui.button("Registrar", icon="check", on_click=registrar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style("padding:0 22px")

    ui.run_javascript("""
    setTimeout(function(){
      // Tipo toggle
      document.querySelectorAll('[id^=ponto-btn]').forEach(function(b){
        b.onclick=function(){
          document.querySelectorAll('[id^=ponto-btn]').forEach(function(x){x.classList.remove('active');});
          b.classList.add('active');
        };
      });
      // Relogio
      function tickPonto(){
        var el=document.getElementById('ponto-dt');
        if(el){
          var d=new Date();
          el.textContent=d.toLocaleDateString('pt-BR')+' · '+d.toLocaleTimeString('pt-BR');
        }
        if(document.getElementById('ponto-dt')) setTimeout(tickPonto,1000);
      }
      tickPonto();
      // Preview foto
      var fi=document.getElementById('ponto-photo');
      var lbl=document.getElementById('ponto-photo-lbl');
      if(fi){
        fi.onchange=function(){
          if(fi.files[0]){
            var r=new FileReader();
            r.onload=function(e){
              var img=document.getElementById('ponto-preview');
              var wrap=document.getElementById('ponto-preview-wrap');
              if(img){img.src=e.target.result;}
              if(wrap){wrap.style.display='block';}
              if(lbl){
                lbl.style.height='36px';
                lbl.querySelector('span:last-of-type').textContent=fi.files[0].name;
              }
            };
            r.readAsDataURL(fi.files[0]);
          }
        };
      }
    }, 120);
    """)
    dlg.open()


# ── Histórico de Checkin/Out ──────────────────────────────────────────

def historico_dialog() -> None:
    todos_usuarios = sorted({r.get("usuario", "") for r in load_ponto() if r.get("usuario")})

    filter_state: dict = {"tipo": "todos", "usuario": ""}

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(860px,97vw)!important;max-height:92vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#60A5FA">history</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 15px var(--dmc-fd);color:var(--dmc-text)">Histórico de Campo</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">Registros de checkin e checkout</div>')

        # Seletor de funcionário — cards clicáveis
        emp_area = ui.element("div").style(
            "padding:14px 20px;border-bottom:1px solid var(--dmc-b1);flex-shrink:0;"
        )

        # Chips de tipo
        with ui.element("div").style(
            "padding:8px 20px;border-bottom:1px solid var(--dmc-b1);"
            "flex-shrink:0;"
        ):
            tipo_area = ui.element("div").style("display:flex;gap:6px;flex-wrap:wrap")

        list_area = ui.element("div").style("padding:12px 20px;overflow-y:auto;flex:1")

        def render_emp():
            emp_area.clear()
            with emp_area:
                ui.html(
                    '<div style="font:9px var(--dmc-mono);color:var(--dmc-muted2);'
                    'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">Funcionário</div>'
                )
                if not todos_usuarios:
                    ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Nenhum registro encontrado.</div>')
                    return
                with ui.element("div").style("display:flex;gap:8px;flex-wrap:wrap"):
                    for u in todos_usuarios:
                        active = filter_state["usuario"] == u
                        initials = "".join(p[0].upper() for p in u.split()[:2])
                        border = "1.5px solid var(--dmc-green)" if active else "1px solid var(--dmc-b1)"
                        bg = "rgba(74,222,128,.08)" if active else "var(--dmc-bg3)"
                        card = ui.element("div").style(
                            f"background:{bg};border:{border};border-radius:10px;"
                            "padding:8px 14px;cursor:pointer;display:flex;align-items:center;gap:8px;"
                            "transition:border .15s;"
                        )
                        with card:
                            ui.html(
                                f'<div style="width:30px;height:30px;border-radius:7px;flex-shrink:0;'
                                f'background:{"rgba(74,222,128,.15)" if active else "rgba(255,255,255,.06)"};'
                                f'display:flex;align-items:center;justify-content:center;'
                                f'font:700 11px var(--dmc-mono);color:{"#4ADE80" if active else "var(--dmc-muted2)"}">'
                                f'{initials}</div>'
                            )
                            ui.html(
                                f'<span style="font:500 13px var(--dmc-fm);color:var(--dmc-text)">{u}</span>'
                            )
                            if active:
                                ui.html(
                                    '<span class="material-icons" '
                                    'style="font-size:16px;color:var(--dmc-green);margin-left:4px">check_circle</span>'
                                )

                        def _select(name=u):
                            filter_state["usuario"] = "" if filter_state["usuario"] == name else name
                            render_emp()
                            render_hist()

                        card.on("click", _select)

        def render_tipo():
            tipo_area.clear()
            with tipo_area:
                for fid, flabel in [("todos", "Todos"), ("checkin", "Check-in"), ("checkout", "Check-out")]:
                    ativo = filter_state["tipo"] == fid
                    cor = "#60A5FA" if fid == "checkout" else "#4ADE80"
                    sty = (
                        f"padding:5px 14px;border-radius:20px;font:11px var(--dmc-mono);"
                        f"cursor:pointer;transition:all .15s;letter-spacing:.04em;"
                        + (f"background:{cor}22;border:1px solid {cor}55;color:{cor};font-weight:700;"
                           if ativo else
                           "background:transparent;border:1px solid var(--dmc-b2);color:var(--dmc-muted);font-weight:400;")
                    )
                    fb = ui.element("button").style(sty)
                    with fb:
                        ui.html(f"<span>{flabel}</span>")
                    fb.on("click", lambda f=fid: [filter_state.__setitem__("tipo", f), render_tipo(), render_hist()])

        def render_hist():
            list_area.clear()
            with list_area:
                if not filter_state["usuario"]:
                    with ui.element("div").style("text-align:center;padding:40px 0"):
                        ui.html('<span class="material-icons" style="font-size:40px;color:var(--dmc-b2)">person_search</span>')
                        ui.html('<div style="font:13px var(--dmc-fm);color:var(--dmc-muted2);margin-top:10px">Selecione um funcionário acima para ver os registros.</div>')
                    return

                registros = list(reversed(load_ponto()))
                if filter_state["tipo"] != "todos":
                    registros = [r for r in registros if r.get("tipo") == filter_state["tipo"]]
                registros = [r for r in registros if r.get("usuario") == filter_state["usuario"]]

                if not registros:
                    with ui.element("div").style("text-align:center;padding:40px 0"):
                        ui.html('<span class="material-icons" style="font-size:40px;color:var(--dmc-b2)">history_toggle_off</span>')
                        ui.html('<div style="font:13px var(--dmc-fm);color:var(--dmc-muted2);margin-top:10px">Nenhum registro encontrado.</div>')
                    return

                ui.html(
                    f'<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                    f'letter-spacing:.1em;text-transform:uppercase;margin-bottom:10px">'
                    f'{len(registros)} registro{"s" if len(registros) != 1 else ""}</div>'
                )

                for r in registros:
                    color, bg, label = _TIPO_COLOR.get(r.get("tipo", "checkin"), _TIPO_COLOR["checkin"])
                    icon = "login" if r.get("tipo") == "checkin" else "logout"

                    with ui.element("div").style(
                        "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);border-radius:12px;"
                        "padding:12px 14px;margin-bottom:8px;display:flex;align-items:center;gap:12px;"
                    ):
                        ui.html(
                            f'<div style="width:36px;height:36px;border-radius:9px;flex-shrink:0;'
                            f'background:{bg};border:1px solid {color}44;'
                            f'display:flex;align-items:center;justify-content:center;">'
                            f'<span class="material-icons" style="font-size:18px;color:{color}">{icon}</span></div>'
                        )

                        with ui.element("div").style("flex:1;min-width:0"):
                            with ui.element("div").style(
                                "display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap"
                            ):
                                ui.html(
                                    f'<span style="font:600 10px var(--dmc-mono);padding:2px 8px;border-radius:4px;'
                                    f'background:{bg};color:{color};border:1px solid {color}44;flex-shrink:0">{label}</span>'
                                )
                                ui.html(
                                    f'<span style="font:500 13px var(--dmc-fm);color:var(--dmc-text)">'
                                    f'{r.get("usuario", "")}</span>'
                                )
                                ui.html(
                                    f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                                    f'margin-left:auto;flex-shrink:0">'
                                    f'{r.get("data", "")} · {r.get("hora", "")}</span>'
                                )
                            ui.html(
                                f'<div style="display:flex;align-items:center;gap:4px;'
                                f'font:12px var(--dmc-fm);color:var(--dmc-muted2)">'
                                f'<span class="material-icons" style="font-size:12px">construction</span>'
                                f'<span style="color:var(--dmc-text);font-weight:500">{r.get("obra", "—")}</span></div>'
                            )
                            if r.get("local"):
                                ui.html(
                                    f'<div style="display:flex;align-items:center;gap:4px;'
                                    f'font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:2px">'
                                    f'<span class="material-icons" style="font-size:11px">location_on</span>'
                                    f'{r["local"]}</div>'
                                )

                        with ui.element("div").style("display:flex;gap:6px;flex-shrink:0;align-items:center"):
                            if r.get("foto"):
                                async def _ver_foto(path=r["foto"]):
                                    from pathlib import Path as _P
                                    fname = _P(path).name
                                    await ui.run_javascript(f"window.open('/fotos_ponto/{fname}','_blank')")

                                foto_btn = ui.element("button").classes("dmc-btn dmc-btn-icon").style(
                                    "color:#60A5FA;border-color:rgba(96,165,250,.2)"
                                ).props('title="Ver foto"')
                                with foto_btn:
                                    ui.html('<span class="material-icons" style="font-size:15px">photo</span>')
                                foto_btn.on("click", _ver_foto)

                            del_btn = ui.element("button").classes("dmc-btn dmc-btn-icon").style(
                                "color:#F87171;border-color:rgba(248,113,113,.2)"
                            ).props('title="Excluir"')
                            with del_btn:
                                ui.html('<span class="material-icons" style="font-size:15px">delete_outline</span>')
                            del_btn.on("click", lambda rid=r["id"]: [
                                delete_registro(rid, current_user_label(), current_user_perfil()),
                                render_hist(),
                            ])

        render_emp()
        render_tipo()
        render_hist()

    dlg.open()
