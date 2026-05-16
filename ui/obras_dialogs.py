"""Diálogos de obras."""

import json as _json
from datetime import datetime, date as _date

from nicegui import ui

from services.auth import current_user_label, current_user_perfil
from services.clientes import load_clientes
from services.obras import add_obra, delete_obra, load_obras, update_obra_status
from ui.dialogs import _addr_block_html

_STATUS = {
    "ativo":     ("#4ADE80", "#14532D", "Ativo"),
    "pausado":   ("#FBBF24", "#78350F", "Pausado"),
    "concluido": ("#60A5FA", "#1E3A5F", "Concluído"),
}


# ── Nova Obra ─────────────────────────────────────────────────────────

def nova_obra_dialog(prefill_cliente: dict = None) -> None:
    clientes = load_clientes()
    clientes_js = _json.dumps([
        {"cpf": c.get("cpf", ""), "nome": c.get("nome", "")}
        for c in clientes
    ])
    prefill_js = _json.dumps(prefill_cliente) if prefill_cliente else "null"

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(860px,97vw)!important;max-height:92vh;"
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
                '<span class="material-icons" style="font-size:20px;color:var(--dmc-green)">construction</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Nova Obra</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">Vincule um cliente e defina o endereço da obra</div>')

        with ui.element("div").style("padding:22px 24px 8px;overflow-y:auto;flex:1"):

            # ── Seleção de cliente ────────────────────────────────────
            ui.html("""
            <div class="dmc-card">
              <div class="dmc-card-hdr">
                <span class="material-icons">person</span> Cliente
              </div>
              <div class="dmc-card-body">
                <div style="display:flex;gap:8px;align-items:flex-end;margin-bottom:8px">
                  <div style="flex:1;min-width:0">
                    <label class="dmc-label">Nome do Cliente</label>
                    <input class="dmc-input" id="f-ow-cliente-search" placeholder="Digite o nome para buscar...">
                  </div>
                  <button type="button" class="dmc-btn" id="btn-ow-buscar">
                    <span class="material-icons">search</span> Buscar
                  </button>
                </div>
                <div id="ow-results" style="display:none;margin-bottom:8px;
                  background:var(--dmc-bg3);border:1px solid var(--dmc-b1);
                  border-radius:10px;overflow:hidden;max-height:180px;overflow-y:auto"></div>
                <div id="ow-selected" style="display:none;
                  background:rgba(74,222,128,.06);border:1px solid var(--dmc-gd);
                  border-radius:10px;padding:12px 16px;align-items:center;gap:10px">
                  <span class="material-icons" style="color:var(--dmc-green);font-size:18px;flex-shrink:0">check_circle</span>
                  <div style="flex:1;min-width:0">
                    <div id="ow-nome" style="font:600 13px var(--dmc-fm);color:var(--dmc-text)"></div>
                    <div id="ow-cpf-lbl" style="font:11px var(--dmc-mono);color:var(--dmc-muted2);margin-top:2px"></div>
                  </div>
                  <button type="button" id="btn-ow-trocar"
                    class="dmc-btn dmc-btn-secondary dmc-btn-sm"
                    style="height:28px;padding:0 10px">Trocar</button>
                </div>
                <input type="hidden" id="f-ow-cpf">
              </div>
            </div>
            """)

            # ── Endereço da obra ──────────────────────────────────────
            with ui.element("div").classes("dmc-card").style("margin-bottom:0"):
                ui.html(
                    '<div class="dmc-card-hdr">'
                    '<span class="material-icons">construction</span> Endereço da Obra</div>'
                )
                with ui.element("div").classes("dmc-card-body"):
                    ui.html(_addr_block_html("ow"))

            # ── Datas da obra ─────────────────────────────────────────
            ui.html("""
            <div class="dmc-card" style="margin-top:14px">
              <div class="dmc-card-hdr">
                <span class="material-icons">date_range</span> Período da Obra
                <span style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-left:6px">(opcional)</span>
              </div>
              <div class="dmc-card-body">
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                  <div>
                    <label class="dmc-label">Data de Início</label>
                    <input class="dmc-input" type="date" id="f-ow-dt-ini"
                      style="color-scheme:dark;cursor:pointer">
                  </div>
                  <div>
                    <label class="dmc-label">Data de Conclusão</label>
                    <input class="dmc-input" type="date" id="f-ow-dt-fim"
                      style="color-scheme:dark;cursor:pointer">
                  </div>
                </div>
                <div id="ow-dt-err" style="display:none;font:11px var(--dmc-fm);
                  color:#F87171;margin-top:6px"></div>
              </div>
            </div>
            """)

            ui.element("div").style("height:12px")

        # ── Rodapé ────────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:space-between;align-items:center;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _collect():
                return await ui.run_javascript("""({
                  cpf:    (document.getElementById('f-ow-cpf')?.value||'').trim(),
                  nome:   (document.getElementById('ow-nome')?.textContent||'').trim(),
                  cep:    (document.getElementById('f-cep-ow')?.value||'').trim(),
                  log:    (document.getElementById('f-log-ow')?.value||'').trim(),
                  num:    (document.getElementById('f-num-ow')?.value||'').trim(),
                  comp:   (document.getElementById('f-comp-ow')?.value||'').trim(),
                  bairro: (document.getElementById('f-bairro-ow')?.value||'').trim(),
                  cidade: (document.getElementById('f-cidade-ow')?.value||'').trim(),
                  uf:     (document.getElementById('f-uf-ow')?.value||'').trim().toUpperCase(),
                  maps:   (document.getElementById('f-maps-ow')?.value||'').trim(),
                  dt_ini: (document.getElementById('f-ow-dt-ini')?.value||'').trim(),
                  dt_fim: (document.getElementById('f-ow-dt-fim')?.value||'').trim(),
                })""")

            def _iso_to_br(iso: str) -> str:
                """Convert YYYY-MM-DD → DD/MM/YYYY for storage."""
                if iso and len(iso) == 10:
                    try:
                        return _date.fromisoformat(iso).strftime("%d/%m/%Y")
                    except ValueError:
                        pass
                return ""

            def _build_obra(vals: dict) -> dict:
                ts = datetime.now().strftime("%Y%m%d%H%M%S")
                safe_cpf = vals["cpf"].replace(".", "").replace("-", "").replace("/", "_")
                return {
                    "id":           f"{ts}_{safe_cpf}",
                    "cliente_cpf":  vals["cpf"],
                    "cliente_nome": vals["nome"],
                    "obra_cep":     vals["cep"],
                    "obra_log":     vals["log"],
                    "obra_num":     vals["num"],
                    "obra_comp":    vals["comp"],
                    "obra_bairro":  vals["bairro"],
                    "obra_cidade":  vals["cidade"],
                    "obra_estado":  vals["uf"],
                    "obra_maps":    vals["maps"],
                    "status":       "ativo",
                    "data_inicio":  _iso_to_br(vals.get("dt_ini", "")),
                    "data_fim":     _iso_to_br(vals.get("dt_fim", "")),
                    "data":         datetime.now().strftime("%d/%m/%Y %H:%M"),
                }

            def _validate_dates(vals: dict) -> str | None:
                """Return error message string or None if OK."""
                ini = vals.get("dt_ini", "")
                fim = vals.get("dt_fim", "")
                if ini and fim:
                    try:
                        if _date.fromisoformat(ini) > _date.fromisoformat(fim):
                            return "A data de conclusão não pode ser anterior à data de início."
                    except ValueError:
                        return "Data inválida."
                return None

            async def salvar():
                vals = await _collect()
                if not vals.get("cpf"):
                    ui.notify("Selecione um cliente.", type="warning")
                    return
                if not vals.get("log"):
                    ui.notify("Preencha o logradouro.", type="warning")
                    return
                dt_err = _validate_dates(vals)
                if dt_err:
                    ui.notify(dt_err, type="warning")
                    ui.run_javascript(
                        f"var e=document.getElementById('ow-dt-err');"
                        f"if(e){{e.textContent={repr(dt_err)};e.style.display='block';}}"
                    )
                    return
                ui.run_javascript(
                    "var e=document.getElementById('ow-dt-err');if(e)e.style.display='none';"
                )
                add_obra(_build_obra(vals),
                         usuario=current_user_label(), perfil=current_user_perfil())
                ui.notify(f"✓ Obra cadastrada para '{vals['nome']}'!", type="positive")
                dlg.close()

            async def salvar_e_nova():
                vals = await _collect()
                if not vals.get("cpf"):
                    ui.notify("Selecione um cliente.", type="warning")
                    return
                if not vals.get("log"):
                    ui.notify("Preencha o logradouro.", type="warning")
                    return
                dt_err = _validate_dates(vals)
                if dt_err:
                    ui.notify(dt_err, type="warning")
                    return
                add_obra(_build_obra(vals),
                         usuario=current_user_label(), perfil=current_user_perfil())
                ui.notify("✓ Obra salva! Abrindo nova obra...", type="positive")
                dlg.close()
                nova_obra_dialog(prefill_cliente={"cpf": vals["cpf"], "nome": vals["nome"]})

            ui.button("Salvar Obra", icon="save", on_click=salvar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style("padding:0 18px")

    ui.run_javascript(f"""
    setTimeout(function(){{
      window._owClientes = {clientes_js};

      function owSelectCliente(c){{
        document.getElementById('f-ow-cpf').value  = c.cpf;
        document.getElementById('ow-nome').textContent  = c.nome;
        document.getElementById('ow-cpf-lbl').textContent = c.cpf;
        var sel = document.getElementById('ow-selected');
        var res = document.getElementById('ow-results');
        var inp = document.getElementById('f-ow-cliente-search');
        if(sel){{ sel.style.display='flex'; }}
        if(res) res.style.display='none';
        if(inp) inp.style.display='none';
        document.getElementById('btn-ow-buscar').style.display='none';
      }}

      function owBuscar(){{
        var q=(document.getElementById('f-ow-cliente-search')?.value||'').trim().toLowerCase();
        if(!q) return;
        var found=(window._owClientes||[]).filter(function(c){{
          return c.nome.toLowerCase().includes(q);
        }});
        var res=document.getElementById('ow-results');
        if(!res) return;
        res.innerHTML='';
        if(!found.length){{
          res.innerHTML='<div style="padding:12px 16px;font:12px var(--dmc-fm);color:var(--dmc-muted2)">Nenhum cliente encontrado</div>';
        }} else {{
          found.forEach(function(c){{
            var row=document.createElement('div');
            row.style.cssText='padding:10px 16px;cursor:pointer;border-bottom:1px solid var(--dmc-b1);display:flex;align-items:center;gap:10px;transition:background .15s';
            row.innerHTML='<span class="material-icons" style="font-size:15px;color:var(--dmc-green);flex-shrink:0">person</span>'
              +'<div><div style="font:500 13px var(--dmc-fm);color:var(--dmc-text)">'+c.nome+'</div>'
              +'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2)">'+c.cpf+'</div></div>';
            row.onmouseenter=function(){{this.style.background='rgba(74,222,128,.06)';}};
            row.onmouseleave=function(){{this.style.background='';}};
            row.onclick=function(){{owSelectCliente(c);}};
            res.appendChild(row);
          }});
        }}
        res.style.display='block';
      }}

      var buscarBtn=document.getElementById('btn-ow-buscar');
      var searchInp=document.getElementById('f-ow-cliente-search');
      var trocarBtn=document.getElementById('btn-ow-trocar');
      if(buscarBtn) buscarBtn.onclick=owBuscar;
      if(searchInp){{
        searchInp.onkeydown=function(e){{if(e.key==='Enter')owBuscar();}};
        searchInp.oninput=function(){{
          if(!this.value.trim()) document.getElementById('ow-results').style.display='none';
        }};
      }}
      if(trocarBtn) trocarBtn.onclick=function(){{
        document.getElementById('ow-selected').style.display='none';
        var inp=document.getElementById('f-ow-cliente-search');
        var btn=document.getElementById('btn-ow-buscar');
        if(inp){{inp.style.display='block';inp.value='';inp.focus();}}
        if(btn) btn.style.display='inline-flex';
        document.getElementById('f-ow-cpf').value='';
        document.getElementById('ow-results').style.display='none';
      }};

      // CEP + Maps
      var p='ow';
      var ci=document.getElementById('f-cep-'+p);
      var cb=document.getElementById('btn-cep-'+p);
      var mb=document.getElementById('btn-maps-'+p);
      if(ci){{
        ci.oninput=function(){{this.value=maskCEP(this.value);}};
        ci.onkeydown=function(e){{if(e.key==='Enter')buscarCep(p);}};
      }}
      if(cb) cb.onclick=function(){{buscarCep(p);}};
      if(mb) mb.onclick=function(){{
        var log=(document.getElementById('f-log-'+p)?.value||'').trim();
        var num=(document.getElementById('f-num-'+p)?.value||'').trim();
        var bairro=(document.getElementById('f-bairro-'+p)?.value||'').trim();
        var cidade=(document.getElementById('f-cidade-'+p)?.value||'').trim();
        var uf=(document.getElementById('f-uf-'+p)?.value||'').trim();
        var q=[log,num,bairro,cidade,uf].filter(Boolean).join(', ');
        var url=q?'https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(q):'https://maps.google.com';
        var mi=document.getElementById('f-maps-'+p);
        if(mi&&q) mi.value=url;
        window.open(url,'_blank','noopener,noreferrer');
      }};

      // Pré-preencher cliente se informado
      var pf={prefill_js};
      if(pf) owSelectCliente(pf);
    }}, 120);
    """)
    dlg.open()


# ── Ver Obras ─────────────────────────────────────────────────────────

def ver_obras_dialog() -> None:
    obras = load_obras()

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(920px,97vw)!important;max-height:90vh;"
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
                '<span class="material-icons" style="font-size:20px;color:var(--dmc-green)">engineering</span></div>'
            )
            with ui.element("div"):
                ui.html(f'<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Obras Cadastradas</div>')
                ui.html(f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">{len(obras)} obra(s) no total</div>')

        # ── Filtro de status ──────────────────────────────────────────
        filter_state = {"value": "todas"}
        list_area = ui.element("div").style("padding:0 22px 8px;overflow-y:auto;flex:1")

        def render_list():
            list_area.clear()
            with list_area:
                current = load_obras()
                fv = filter_state["value"]
                filtered = current if fv == "todas" else [o for o in current if o.get("status") == fv]

                if not filtered:
                    with ui.element("div").style("text-align:center;padding:48px 0"):
                        ui.html('<span class="material-icons" style="font-size:40px;color:var(--dmc-b2)">construction</span>')
                        ui.html('<div style="font:13px var(--dmc-fm);color:var(--dmc-muted2);margin-top:10px">Nenhuma obra encontrada.</div>')
                    return

                for obra in reversed(current if fv == "todas" else filtered):
                    color, bg, label = _STATUS.get(obra.get("status", "ativo"), ("#4ADE80", "#14532D", "Ativo"))
                    end = f"{obra.get('obra_log','')} {obra.get('obra_num','')}, {obra.get('obra_bairro','')}, {obra.get('obra_cidade','')} / {obra.get('obra_estado','')}".strip(", / ")

                    with ui.element("div").style(
                        "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);border-radius:12px;"
                        "padding:14px 16px;margin-bottom:8px;"
                    ):
                        with ui.element("div").style("display:flex;align-items:flex-start;gap:12px"):
                            ui.html(
                                f'<div style="width:36px;height:36px;border-radius:9px;flex-shrink:0;'
                                f'background:{bg};border:1px solid {color}33;'
                                f'display:flex;align-items:center;justify-content:center;">'
                                f'<span class="material-icons" style="font-size:18px;color:{color}">construction</span></div>'
                            )
                            with ui.element("div").style("flex:1;min-width:0"):
                                with ui.element("div").style("display:flex;align-items:center;gap:8px;margin-bottom:4px"):
                                    ui.html(f'<span style="font:600 14px var(--dmc-fm);color:var(--dmc-text)">{obra.get("cliente_nome","")}</span>')
                                    ui.html(
                                        f'<span style="font:10px var(--dmc-mono);padding:2px 8px;border-radius:4px;'
                                        f'background:{bg};color:{color};border:1px solid {color}44">{label}</span>'
                                    )
                                ui.html(
                                    f'<div style="display:flex;align-items:center;gap:5px;'
                                    f'font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:2px">'
                                    f'<span class="material-icons" style="font-size:13px">location_on</span>'
                                    f'<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{end}</span></div>'
                                )
                                ui.html(f'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2)">{obra.get("data","")}</div>')

                            # Ações
                            with ui.element("div").style("display:flex;flex-direction:column;gap:4px;flex-shrink:0"):
                                status_opts = [s for s in _STATUS if s != obra.get("status")]
                                for ns in status_opts:
                                    sc, _, sl = _STATUS[ns]
                                    sb = ui.element("button").classes("dmc-btn dmc-btn-sm").style(
                                        f"color:{sc};border-color:{sc}44;"
                                    )
                                    with sb:
                                        ui.html(f"<span>→ {sl}</span>")
                                    sb.on("click", lambda oid=obra["id"], s=ns: [
                                        update_obra_status(oid, s,
                                            current_user_label(), current_user_perfil()),
                                        render_list()
                                    ])

                                del_btn = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
                                with del_btn:
                                    ui.html('<span class="material-icons" style="font-size:11px;vertical-align:middle">delete</span> Excluir')
                                del_btn.on("click", lambda oid=obra["id"], on=obra.get("cliente_nome", ""): [
                                    delete_obra(oid, nome=on,
                                        usuario=current_user_label(), perfil=current_user_perfil()),
                                    render_list()
                                ])

                        if obra.get("obra_maps"):
                            maps_btn = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm").style(
                                "margin-top:8px"
                            )
                            with maps_btn:
                                ui.html('<span class="material-icons" style="font-size:13px">map</span><span>Ver no Maps</span>')
                            maps_btn.on("click", lambda u=obra["obra_maps"]: ui.run_javascript(
                                f"window.open({repr(u)},'_blank','noopener,noreferrer');"
                            ))

        # Filtros
        with ui.element("div").style(
            "padding:14px 22px 0;display:flex;gap:6px;flex-shrink:0"
        ):
            for fid, (fc, _, fl) in [("todas", ("#8BAA8B", "", "Todas")), *_STATUS.items()]:
                is_active = filter_state["value"] == fid

                def make_filter(f=fid):
                    filter_state["value"] = f
                    render_list()

                fb = ui.element("button").style(
                    f"padding:5px 14px;border-radius:20px;font:11px var(--dmc-fm);cursor:pointer;transition:all .15s;"
                    f"{'background:rgba(74,222,128,.12);border:1px solid var(--dmc-gd);color:var(--dmc-green)' if fid == 'todas' and is_active else ''}"
                    f"{'background:transparent;border:1px solid var(--dmc-b2);color:var(--dmc-muted)' if not is_active else ''}"
                )
                with fb:
                    ui.html(f"<span>{fl}</span>")
                fb.on("click", lambda f=fid: [filter_state.__setitem__("value", f), render_list()])

        render_list()

        with ui.element("div").style(
            "padding:12px 22px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:space-between;align-items:center;flex-shrink:0;"
        ):
            ui.button("Fechar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')
            ui.button("Nova Obra", icon="add", on_click=lambda: [dlg.close(), nova_obra_dialog()]).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary')

    dlg.open()
