"""Diálogos de Técnicos Cadastrados."""

from datetime import datetime

from nicegui import ui

from services.auth import current_user_label, current_user_perfil
from services.clientes import fmt_cpf, fmt_tel
from services.tecnicos import add_tecnico, delete_tecnico, load_tecnicos, update_tecnico


# ── Bloco de endereço reutilizável ───────────────────────────────────────

def _tc_addr_html(prefix: str) -> str:
    return f"""
<div style="display:flex;gap:8px;align-items:flex-end;margin-bottom:4px">
  <div style="flex:1;min-width:0">
    <label class="dmc-label">CEP</label>
    <input class="dmc-input" id="tc-cep-{prefix}" placeholder="00000-000" maxlength="9"
      inputmode="numeric">
  </div>
  <button type="button" class="dmc-btn" id="tc-btn-cep-{prefix}">
    <span class="material-icons">search</span> Buscar CEP
  </button>
</div>
<div id="tc-cep-status-{prefix}" class="dmc-status" style="margin-bottom:8px;color:transparent">_</div>
<div style="display:grid;grid-template-columns:1fr 72px;gap:8px;margin-bottom:8px">
  <div>
    <label class="dmc-label">Logradouro / Rua</label>
    <input class="dmc-input" id="tc-log-{prefix}" placeholder="RUA, AV., ROD..."
      oninput="this.value=this.value.toUpperCase()">
  </div>
  <div>
    <label class="dmc-label">Nº</label>
    <input class="dmc-input" id="tc-num-{prefix}" placeholder="000"
      oninput="this.value=this.value.toUpperCase()">
  </div>
</div>
<div style="margin-bottom:8px">
  <label class="dmc-label">Complemento</label>
  <input class="dmc-input" id="tc-comp-{prefix}" placeholder="APTO, BLOCO, SALA..."
    oninput="this.value=this.value.toUpperCase()">
</div>
<div style="display:grid;grid-template-columns:1fr 1fr 52px;gap:8px;margin-bottom:8px">
  <div>
    <label class="dmc-label">Bairro</label>
    <input class="dmc-input" id="tc-bairro-{prefix}" placeholder="BAIRRO"
      oninput="this.value=this.value.toUpperCase()">
  </div>
  <div>
    <label class="dmc-label">Cidade</label>
    <input class="dmc-input" id="tc-cidade-{prefix}" placeholder="CIDADE"
      oninput="this.value=this.value.toUpperCase()">
  </div>
  <div>
    <label class="dmc-label">UF</label>
    <input class="dmc-input" id="tc-uf-{prefix}" placeholder="SC" maxlength="2"
      oninput="this.value=this.value.toUpperCase()">
  </div>
</div>
<div style="display:flex;gap:8px;align-items:flex-end">
  <div style="flex:1;min-width:0">
    <label class="dmc-label">Link Google Maps</label>
    <input class="dmc-input" id="tc-maps-{prefix}" placeholder="Cole o link aqui...">
  </div>
  <button type="button" class="dmc-btn" id="tc-btn-maps-{prefix}">
    <span class="material-icons">map</span> Maps
  </button>
</div>
"""


# ── JS para busca de CEP (prefixo tc-) ───────────────────────────────────

_CEP_JS = """
async function tcBuscarCep(prefix) {
  var el = document.getElementById('tc-cep-' + prefix);
  if (!el) return;
  var cep = el.value.replace(/\\D/g, '');
  if (cep.length !== 8) { tcSetCepStatus(prefix, 'CEP inválido', '#F87171'); return; }
  tcSetCepStatus(prefix, 'Buscando...', '#6B8F6B');
  try {
    var r = await fetch('/api/cep/' + cep);
    var d = await r.json();
    if (d.erro) { tcSetCepStatus(prefix, 'CEP não encontrado', '#F87171'); return; }
    document.getElementById('tc-log-' + prefix).value = (d.logradouro || '').toUpperCase();
    document.getElementById('tc-bairro-' + prefix).value = (d.bairro || '').toUpperCase();
    document.getElementById('tc-cidade-' + prefix).value = (d.localidade || '').toUpperCase();
    document.getElementById('tc-uf-' + prefix).value = (d.uf || '').toUpperCase();
    tcSetCepStatus(prefix, '✓ Endereço encontrado', '#4ADE80');
  } catch(e) { tcSetCepStatus(prefix, 'Erro ao buscar CEP', '#F87171'); }
}
function tcSetCepStatus(prefix, msg, color) {
  var el = document.getElementById('tc-cep-status-' + prefix);
  if (el) { el.textContent = msg; el.style.color = color; }
}
"""


# ── Diálogo Cadastrar ─────────────────────────────────────────────────────

def cadastrar_tecnico_dialog(on_saved=None) -> None:
    _FORM_IDS = [
        "tc-nome", "tc-cft", "tc-doc", "tc-tel",
        "tc-cep-end", "tc-log-end", "tc-num-end", "tc-comp-end",
        "tc-bairro-end", "tc-cidade-end", "tc-uf-end", "tc-maps-end",
    ]

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(900px,98vw)!important;max-height:92vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        # Cabeçalho
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">engineering</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Cadastrar Técnico</div>')
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    'Preencha os dados e clique em Salvar Técnico</div>'
                )

        # Corpo
        with ui.element("div").style("padding:22px 24px 8px;overflow-y:auto;flex:1"):

            # Dados do técnico
            ui.html("""
            <div class="dmc-card">
              <div class="dmc-card-hdr">
                <span class="material-icons">engineering</span> Dados do Técnico
              </div>
              <div class="dmc-card-body">
                <div style="margin-bottom:12px">
                  <label class="dmc-label">Nome Completo</label>
                  <input class="dmc-input" id="tc-nome" placeholder="NOME COMPLETO"
                    oninput="this.value=this.value.toUpperCase()">
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;align-items:flex-end">
                  <div>
                    <label class="dmc-label">CPF</label>
                    <input class="dmc-input" id="tc-doc" placeholder="000.000.000-00"
                      inputmode="numeric" oninput="this.value=maskCPF(this.value)">
                  </div>
                  <div>
                    <label class="dmc-label">CFT</label>
                    <input class="dmc-input" id="tc-cft" placeholder="00000/SC"
                      oninput="this.value=this.value.toUpperCase()">
                  </div>
                  <div>
                    <label class="dmc-label">Telefone</label>
                    <input class="dmc-input" id="tc-tel" placeholder="(00) 00000-0000"
                      oninput="this.value=maskTel(this.value)">
                  </div>
                </div>
              </div>
            </div>
            """)

            # Endereço
            with ui.element("div").classes("dmc-card"):
                ui.html(
                    '<div class="dmc-card-hdr">'
                    '<span class="material-icons">home</span> Endereço</div>'
                )
                with ui.element("div").classes("dmc-card-body"):
                    ui.html(_tc_addr_html("end"))

            ui.element("div").style("height:12px")

        # Rodapé
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props("flat no-caps").classes("dmc-btn dmc-btn-ghost")

            async def salvar():
                vals = await ui.run_javascript("""({
                  nome: (document.getElementById('tc-nome')?.value||'').trim().toUpperCase(),
                  cft:  (document.getElementById('tc-cft')?.value||'').trim().toUpperCase(),
                  doc:  (document.getElementById('tc-doc')?.value||'').trim(),
                  tel:  (document.getElementById('tc-tel')?.value||'').trim(),
                  end_log:    (document.getElementById('tc-log-end')?.value||'').trim().toUpperCase(),
                  end_num:    (document.getElementById('tc-num-end')?.value||'').trim().toUpperCase(),
                  end_comp:   (document.getElementById('tc-comp-end')?.value||'').trim().toUpperCase(),
                  end_bairro: (document.getElementById('tc-bairro-end')?.value||'').trim().toUpperCase(),
                  end_cidade: (document.getElementById('tc-cidade-end')?.value||'').trim().toUpperCase(),
                  end_uf:     (document.getElementById('tc-uf-end')?.value||'').trim().toUpperCase(),
                  end_maps:   (document.getElementById('tc-maps-end')?.value||'').trim(),
                })""")

                if not vals.get("nome") or not vals.get("doc"):
                    ui.notify("Preencha pelo menos Nome e CPF.", type="warning")
                    return

                tecnico = {
                    "nome":       vals["nome"],
                    "cft":        vals["cft"],
                    "cpf":        fmt_cpf(vals["doc"]),
                    "telefone":   fmt_tel(vals["tel"]),
                    "end_log":    vals["end_log"],
                    "end_num":    vals["end_num"],
                    "end_comp":   vals["end_comp"],
                    "end_bairro": vals["end_bairro"],
                    "end_cidade": vals["end_cidade"],
                    "end_estado": vals["end_uf"],
                    "end_maps":   vals["end_maps"],
                    "data":       datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                add_tecnico(tecnico, usuario=current_user_label(), perfil=current_user_perfil())
                ui.notify(f"✓ Técnico '{vals['nome']}' cadastrado!", type="positive")
                if on_saved:
                    on_saved()
                dlg.close()

            ui.button("Salvar Técnico", on_click=salvar).props("unelevated no-caps").classes("dmc-btn dmc-btn-primary").style("padding:0 22px")

    # JS: CEP + masks
    ids_js = ",".join(f"'{i}'" for i in _FORM_IDS)
    ui.run_javascript(f"""
    setTimeout(function() {{
      // Limpa campos
      [{ids_js}].forEach(function(id) {{
        var el = document.getElementById(id);
        if (el) el.value = '';
      }});

      // Máscaras CPF / Tel
      var docInp = document.getElementById('tc-doc');
      if (docInp) docInp.oninput = function() {{ this.value = maskCPF(this.value); }};
      var telInp = document.getElementById('tc-tel');
      if (telInp) telInp.oninput = function() {{ this.value = maskTel(this.value); }};

      // CEP
      var ci = document.getElementById('tc-cep-end');
      var cb = document.getElementById('tc-btn-cep-end');
      if (ci) {{
        ci.oninput = function() {{ this.value = maskCEP(this.value); }};
        ci.onkeydown = function(e) {{ if (e.key === 'Enter') tcBuscarCep('end'); }};
      }}
      if (cb) cb.onclick = function() {{ tcBuscarCep('end'); }};

      // Maps
      var mb = document.getElementById('tc-btn-maps-end');
      if (mb) mb.onclick = function() {{
        var v = document.getElementById('tc-maps-end')?.value?.trim();
        if (v) window.open(v, '_blank', 'noopener,noreferrer');
      }};
    }}, 120);
    """)

    dlg.open()


# ── Diálogo Ver / Gerenciar Técnicos ─────────────────────────────────────

def ver_tecnicos_dialog() -> None:

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(860px,97vw)!important;max-height:92vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        # Cabeçalho
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">engineering</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Técnicos Cadastrados</div>')
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    'Lista de técnicos · clique para editar ou excluir</div>'
                )

        # Corpo
        with ui.element("div").style("padding:20px 24px;overflow-y:auto;flex:1;min-height:0"):

            # Busca
            with ui.element("div").style("display:flex;gap:10px;margin-bottom:16px"):
                busca = ui.input(placeholder="Buscar por nome, CFT ou CPF...").style(
                    "flex:1;background:var(--dmc-bg3)!important;"
                    "border:1px solid var(--dmc-b1)!important;border-radius:8px!important;"
                ).props("dense outlined clearable")

                ui.button("Novo Técnico", icon="add", on_click=lambda: [
                    dlg.close(),
                    cadastrar_tecnico_dialog(on_saved=ver_tecnicos_dialog),
                ]).props("unelevated no-caps").classes("dmc-btn dmc-btn-primary")

            lista_container = ui.element("div")

            def _render_lista(filtro: str = ""):
                lista_container.clear()
                tecnicos = load_tecnicos()
                q = filtro.strip().lower()
                if q:
                    tecnicos = [
                        t for t in tecnicos
                        if q in t.get("nome", "").lower()
                        or q in t.get("cft", "").lower()
                        or q in t.get("cpf", "").lower()
                    ]

                with lista_container:
                    if not tecnicos:
                        ui.html(
                            '<div style="text-align:center;padding:40px 0;color:var(--dmc-muted2);'
                            'font:13px var(--dmc-fm)">Nenhum técnico encontrado.</div>'
                        )
                        return

                    ui.html(
                        f'<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                        f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:10px">'
                        f'{len(tecnicos)} técnico{"s" if len(tecnicos) != 1 else ""}</div>'
                    )

                    for t in tecnicos:
                        initials = "".join(p[0] for p in t.get("nome", "?").split()[:2]).upper()
                        end_str = ", ".join(filter(None, [
                            f"{t.get('end_log','')} {t.get('end_num','')}".strip(),
                            t.get("end_bairro", ""),
                            f"{t.get('end_cidade','')} / {t.get('end_estado','')}".strip("/ "),
                        ]))

                        with ui.element("div").style(
                            "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);"
                            "border-radius:14px;padding:14px 16px;margin-bottom:8px;"
                            "display:flex;align-items:center;gap:14px;"
                        ):
                            # Avatar
                            ui.html(
                                f'<div style="width:42px;height:42px;border-radius:10px;flex-shrink:0;'
                                f'background:rgba(251,191,36,.10);border:1px solid rgba(251,191,36,.25);'
                                f'display:flex;align-items:center;justify-content:center;'
                                f'font:700 14px var(--dmc-fd);color:#FBBF24">{initials}</div>'
                            )

                            # Info
                            with ui.element("div").style("flex:1;min-width:0"):
                                ui.html(
                                    f'<div style="font:600 14px var(--dmc-fd);color:var(--dmc-text);'
                                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                                    f'{t.get("nome", "")}</div>'
                                )
                                tags = []
                                if t.get("cft"):
                                    tags.append(
                                        f'<span style="background:rgba(251,191,36,.12);'
                                        f'border:1px solid rgba(251,191,36,.3);color:#FBBF24;'
                                        f'font:600 10px var(--dmc-mono);padding:1px 7px;border-radius:20px">'
                                        f'CFT {t["cft"]}</span>'
                                    )
                                if t.get("cpf"):
                                    tags.append(
                                        f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                                        f'{t["cpf"]}</span>'
                                    )
                                if t.get("telefone"):
                                    tags.append(
                                        f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                                        f'{t["telefone"]}</span>'
                                    )
                                if tags:
                                    ui.html(
                                        '<div style="display:flex;align-items:center;gap:8px;'
                                        'flex-wrap:wrap;margin-top:3px">' + " ".join(tags) + "</div>"
                                    )
                                if end_str:
                                    ui.html(
                                        f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);'
                                        f'margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
                                        f'{end_str}</div>'
                                    )

                            # Ações
                            with ui.element("div").style("display:flex;gap:6px;flex-shrink:0"):
                                cpf_ref = t.get("cpf", "")

                                def _editar(tc=t):
                                    dlg.close()
                                    _editar_tecnico_dialog(tc, on_saved=ver_tecnicos_dialog)

                                def _excluir(cpf=cpf_ref, nome=t.get("nome", "")):
                                    delete_tecnico(cpf, nome=nome,
                                                   usuario=current_user_label(), perfil=current_user_perfil())
                                    ui.notify(f"Técnico '{nome}' removido.", type="positive")
                                    _render_lista(busca.value or "")

                                ui.button(icon="edit", on_click=_editar).props("flat round dense").style(
                                    "color:var(--dmc-muted2);"
                                ).tooltip("Editar")
                                ui.button(icon="delete", on_click=_excluir).props("flat round dense").style(
                                    "color:#F87171;"
                                ).tooltip("Excluir")

            busca.on("input", lambda e: _render_lista(e.value or ""))
            _render_lista()

        # Rodapé
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;flex-shrink:0;"
        ):
            ui.button("Fechar", on_click=dlg.close).props("flat no-caps").classes("dmc-btn dmc-btn-ghost")

    dlg.open()


# ── Diálogo Editar Técnico ────────────────────────────────────────────────

def _editar_tecnico_dialog(tecnico: dict, on_saved=None) -> None:
    original_cpf = tecnico.get("cpf", "")

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(900px,98vw)!important;max-height:92vh;"
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
                'background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">edit</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Editar Técnico</div>')
                ui.html(
                    f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    f'{tecnico.get("nome", "")}</div>'
                )

        with ui.element("div").style("padding:22px 24px 8px;overflow-y:auto;flex:1"):

            ui.html(f"""
            <div class="dmc-card">
              <div class="dmc-card-hdr">
                <span class="material-icons">engineering</span> Dados do Técnico
              </div>
              <div class="dmc-card-body">
                <div style="margin-bottom:12px">
                  <label class="dmc-label">Nome Completo</label>
                  <input class="dmc-input" id="tce-nome" value="{tecnico.get('nome','')}"
                    oninput="this.value=this.value.toUpperCase()">
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px">
                  <div>
                    <label class="dmc-label">CPF</label>
                    <input class="dmc-input" id="tce-doc" value="{tecnico.get('cpf','')}"
                      inputmode="numeric" oninput="this.value=maskCPF(this.value)">
                  </div>
                  <div>
                    <label class="dmc-label">CFT</label>
                    <input class="dmc-input" id="tce-cft" value="{tecnico.get('cft','')}"
                      oninput="this.value=this.value.toUpperCase()">
                  </div>
                  <div>
                    <label class="dmc-label">Telefone</label>
                    <input class="dmc-input" id="tce-tel" value="{tecnico.get('telefone','')}"
                      oninput="this.value=maskTel(this.value)">
                  </div>
                </div>
              </div>
            </div>
            """)

            with ui.element("div").classes("dmc-card"):
                ui.html(
                    '<div class="dmc-card-hdr">'
                    '<span class="material-icons">home</span> Endereço</div>'
                )
                with ui.element("div").classes("dmc-card-body"):
                    ui.html(_tc_addr_html("e2"))

            ui.element("div").style("height:12px")

        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props("flat no-caps").classes("dmc-btn dmc-btn-ghost")

            async def salvar_edicao():
                vals = await ui.run_javascript("""({
                  nome: (document.getElementById('tce-nome')?.value||'').trim().toUpperCase(),
                  cft:  (document.getElementById('tce-cft')?.value||'').trim().toUpperCase(),
                  doc:  (document.getElementById('tce-doc')?.value||'').trim(),
                  tel:  (document.getElementById('tce-tel')?.value||'').trim(),
                  end_log:    (document.getElementById('tc-log-e2')?.value||'').trim().toUpperCase(),
                  end_num:    (document.getElementById('tc-num-e2')?.value||'').trim().toUpperCase(),
                  end_comp:   (document.getElementById('tc-comp-e2')?.value||'').trim().toUpperCase(),
                  end_bairro: (document.getElementById('tc-bairro-e2')?.value||'').trim().toUpperCase(),
                  end_cidade: (document.getElementById('tc-cidade-e2')?.value||'').trim().toUpperCase(),
                  end_uf:     (document.getElementById('tc-uf-e2')?.value||'').trim().toUpperCase(),
                  end_maps:   (document.getElementById('tc-maps-e2')?.value||'').trim(),
                })""")

                if not vals.get("nome") or not vals.get("doc"):
                    ui.notify("Preencha pelo menos Nome e CPF.", type="warning")
                    return

                updated = {
                    "nome":       vals["nome"],
                    "cft":        vals["cft"],
                    "cpf":        fmt_cpf(vals["doc"]),
                    "telefone":   fmt_tel(vals["tel"]),
                    "end_log":    vals["end_log"],
                    "end_num":    vals["end_num"],
                    "end_comp":   vals["end_comp"],
                    "end_bairro": vals["end_bairro"],
                    "end_cidade": vals["end_cidade"],
                    "end_estado": vals["end_uf"],
                    "end_maps":   vals["end_maps"],
                    "data":       tecnico.get("data", datetime.now().strftime("%d/%m/%Y %H:%M")),
                }
                update_tecnico(original_cpf, updated,
                              usuario=current_user_label(), perfil=current_user_perfil())
                ui.notify(f"✓ Técnico '{vals['nome']}' atualizado!", type="positive")
                if on_saved:
                    on_saved()
                dlg.close()

            ui.button("Salvar Alterações", icon="save", on_click=salvar_edicao).props(
                "unelevated no-caps"
            ).classes("dmc-btn dmc-btn-primary").style("padding:0 22px")

    # Preenche campos de endereço
    ui.run_javascript(f"""
    setTimeout(function() {{
      var fields = {{
        'tc-log-e2':    {repr(tecnico.get('end_log',''))},
        'tc-num-e2':    {repr(tecnico.get('end_num',''))},
        'tc-comp-e2':   {repr(tecnico.get('end_comp',''))},
        'tc-bairro-e2': {repr(tecnico.get('end_bairro',''))},
        'tc-cidade-e2': {repr(tecnico.get('end_cidade',''))},
        'tc-uf-e2':     {repr(tecnico.get('end_estado',''))},
        'tc-maps-e2':   {repr(tecnico.get('end_maps',''))},
      }};
      Object.entries(fields).forEach(function([id, val]) {{
        var el = document.getElementById(id);
        if (el) el.value = val;
      }});
      // Máscaras CPF / Tel
      var docInpE = document.getElementById('tce-doc');
      if (docInpE) docInpE.oninput = function() {{ this.value = maskCPF(this.value); }};
      var telInpE = document.getElementById('tce-tel');
      if (telInpE) telInpE.oninput = function() {{ this.value = maskTel(this.value); }};

      var ci = document.getElementById('tc-cep-e2');
      var cb = document.getElementById('tc-btn-cep-e2');
      if (ci) {{
        ci.oninput = function() {{ this.value = maskCEP(this.value); }};
        ci.onkeydown = function(e) {{ if (e.key === 'Enter') tcBuscarCep('e2'); }};
      }}
      if (cb) cb.onclick = function() {{ tcBuscarCep('e2'); }};
      var mb = document.getElementById('tc-btn-maps-e2');
      if (mb) mb.onclick = function() {{
        var v = document.getElementById('tc-maps-e2')?.value?.trim();
        if (v) window.open(v, '_blank', 'noopener,noreferrer');
      }};
    }}, 120);
    """)

    dlg.open()


# ── Injeta JS de CEP no head (chamado uma vez ao carregar) ────────────────

def inject_tecnicos_js() -> None:
    ui.add_head_html(f"<script>{_CEP_JS}</script>")
