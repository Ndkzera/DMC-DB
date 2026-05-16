"""Página de cadastro de clientes."""

import json
from datetime import datetime

import aiohttp
from nicegui import app as _app
from nicegui import ui

from services.auth import current_user_label, current_user_perfil
from services.clientes import add_cliente, fmt_cpf, fmt_tel
from ui.styles import BOOTSTRAP_CDN, CSS, UTILS_JS

# ── FastAPI endpoints (CEP / CPF / CNPJ) ─────────────────────────────────────

@_app.get("/api/cep/{cep_val}")
async def _api_cep(cep_val: str):
    cep = "".join(c for c in cep_val if c.isdigit())[:8]
    if len(cep) != 8:
        return {"erro": True}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://viacep.com.br/ws/{cep}/json/",
                             timeout=aiohttp.ClientTimeout(total=5)) as r:
                return await r.json()
    except Exception:
        return {"erro": True}


@_app.get("/api/cpf/{cpf_val}")
async def _api_cpf(cpf_val: str):
    cpf = "".join(c for c in cpf_val if c.isdigit())[:11]
    if len(cpf) != 11:
        return {"erro": True}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://brasilapi.com.br/api/cpf/v1/{cpf}",
                             timeout=aiohttp.ClientTimeout(total=6)) as r:
                return await r.json()
    except Exception:
        return {"erro": True}


@_app.get("/api/cnpj/{cnpj_val}")
async def _api_cnpj(cnpj_val: str):
    cnpj = "".join(c for c in cnpj_val if c.isdigit())[:14]
    if len(cnpj) != 14:
        return {"erro": True}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://receitaws.com.br/v1/cnpj/{cnpj}",
                             headers={"Accept": "application/json"},
                             timeout=aiohttp.ClientTimeout(total=8)) as r:
                return await r.json()
    except Exception:
        return {"erro": True}


# ── CSS ───────────────────────────────────────────────────────────────────────

# CSS moved to ui/styles.py (global)

# ── JavaScript ────────────────────────────────────────────────────────────────

_FORM_JS = """
<script>
var dmcTipo = 'PF';

function maskCPF(v){
  v=v.replace(/\D/g,'').slice(0,11);
  if(v.length>9) v=v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6,9)+'-'+v.slice(9);
  else if(v.length>6) v=v.slice(0,3)+'.'+v.slice(3,6)+'.'+v.slice(6);
  else if(v.length>3) v=v.slice(0,3)+'.'+v.slice(3);
  return v;
}
function maskCNPJ(v){
  v=v.replace(/\D/g,'').slice(0,14);
  if(v.length>12) v=v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5,8)+'/'+v.slice(8,12)+'-'+v.slice(12);
  else if(v.length>8) v=v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5,8)+'/'+v.slice(8);
  else if(v.length>5) v=v.slice(0,2)+'.'+v.slice(2,5)+'.'+v.slice(5);
  else if(v.length>2) v=v.slice(0,2)+'.'+v.slice(2);
  return v;
}
function maskTel(v){
  v=v.replace(/\D/g,'').slice(0,11);
  if(v.length>10) v='('+v.slice(0,2)+') '+v.slice(2,7)+'-'+v.slice(7);
  else if(v.length>6) v='('+v.slice(0,2)+') '+v.slice(2,6)+'-'+v.slice(6);
  else if(v.length>2) v='('+v.slice(0,2)+') '+v.slice(2);
  else if(v.length>0) v='('+v;
  return v;
}
function maskCEP(v){
  v=v.replace(/\D/g,'').slice(0,8);
  if(v.length>5) v=v.slice(0,5)+'-'+v.slice(5);
  return v;
}
function tcase(s){
  return (s||'').toLowerCase().replace(/\b\w/g,function(c){return c.toUpperCase();});
}

function setTipo(tipo){
  dmcTipo=tipo;
  document.querySelectorAll('.dmc-tipo-btn').forEach(function(b){
    b.classList.toggle('active',b.dataset.tipo===tipo);
  });
  var lbl=document.getElementById('doc-label');
  var nomeLbl=document.getElementById('nome-label');
  var inp=document.getElementById('f-doc');
  if(lbl) lbl.textContent=tipo==='PF'?'CPF':'CNPJ';
  if(nomeLbl) nomeLbl.textContent=tipo==='PF'?'Nome Completo':'Razão Social';
  if(inp){
    inp.placeholder=tipo==='PF'?'000.000.000-00':'00.000.000/0000-00';
    inp.inputMode=tipo==='PF'?'numeric':'text';
    inp.value='';
    inp.oninput=function(){this.value=tipo==='PF'?maskCPF(this.value):maskCNPJ(this.value);};
  }
  setDocStatus('','transparent');
}

function setCepStatus(prefix,msg,color){
  var el=document.getElementById('cep-status-'+prefix);
  if(el){el.textContent=msg;el.style.color=color;}
}
function setDocStatus(msg,color){
  var el=document.getElementById('doc-status');
  if(el){el.textContent=msg;el.style.color=color||'transparent';}
}
function toggleObra(checked){
  var w=document.getElementById('obra-fields-wrap');
  if(!w) return;
  var _fields=['cep','log','num','comp','bairro','cidade','uf','maps'];
  if(checked){
    _fields.forEach(function(f){
      var src=document.getElementById('f-'+f+'-end');
      var dst=document.getElementById('f-'+f+'-obra');
      if(src&&dst) dst.value=src.value;
    });
    var ss=document.getElementById('cep-status-end');
    var sd=document.getElementById('cep-status-obra');
    if(ss&&sd){sd.textContent=ss.textContent;sd.style.color=ss.style.color;}
    w.querySelectorAll('input,textarea,button').forEach(function(el){el.disabled=true;});
    w.style.opacity='0.45';
  }else{
    w.querySelectorAll('input,textarea,button').forEach(function(el){el.disabled=false;});
    w.style.opacity='1';
  }
}

async function buscarCep(prefix){
  var el=document.getElementById('f-cep-'+prefix);
  if(!el) return;
  var cep=el.value.replace(/\D/g,'');
  if(cep.length!==8){setCepStatus(prefix,'CEP inválido','#F87171');return;}
  setCepStatus(prefix,'Buscando...','#6B8F6B');
  try{
    var r=await fetch('/api/cep/'+cep);
    var d=await r.json();
    if(d.erro){setCepStatus(prefix,'CEP não encontrado','#F87171');return;}
    document.getElementById('f-log-'+prefix).value=tcase(d.logradouro);
    document.getElementById('f-bairro-'+prefix).value=tcase(d.bairro);
    document.getElementById('f-cidade-'+prefix).value=tcase(d.localidade);
    document.getElementById('f-uf-'+prefix).value=(d.uf||'').toUpperCase();
    setCepStatus(prefix,'✓ Endereço encontrado','#4ADE80');
  }catch(e){setCepStatus(prefix,'Erro ao buscar CEP','#F87171');}
}

async function buscarDoc(){
  var raw=(document.getElementById('f-doc')?.value||'').replace(/\D/g,'');
  if(dmcTipo==='PF'){
    if(raw.length!==11){setDocStatus('CPF inválido (11 dígitos)','#F87171');return;}
    setDocStatus('Consultando CPF...','#6B8F6B');
    try{
      var r=await fetch('/api/cpf/'+raw);
      var d=await r.json();
      var nome=tcase(d.nome||d.name||'');
      if(nome){
        document.getElementById('f-nome').value=nome;
        setDocStatus('✓ '+nome,'#4ADE80');
      }else{setDocStatus('CPF válido — preencha o nome manualmente','#FBBF24');}
    }catch(e){setDocStatus('CPF válido — consulta indisponível','#FBBF24');}
  }else{
    if(raw.length!==14){setDocStatus('CNPJ inválido (14 dígitos)','#F87171');return;}
    setDocStatus('Consultando Receita Federal...','#6B8F6B');
    try{
      var r=await fetch('/api/cnpj/'+raw);
      var d=await r.json();
      if(d.status==='ERROR'){setDocStatus('CNPJ não encontrado','#F87171');return;}
      var nome=tcase(d.nome||d.fantasia||'');
      document.getElementById('f-nome').value=nome;
      var tel=document.getElementById('f-tel');
      if(tel) tel.value=(d.telefone||'').split('/')[0].trim();
      if(d.logradouro) document.getElementById('f-log-end').value=tcase(d.logradouro);
      if(d.numero)     document.getElementById('f-num-end').value=d.numero;
      if(d.complemento) document.getElementById('f-comp-end').value=d.complemento;
      if(d.bairro)     document.getElementById('f-bairro-end').value=tcase(d.bairro);
      if(d.municipio)  document.getElementById('f-cidade-end').value=tcase(d.municipio);
      if(d.uf)         document.getElementById('f-uf-end').value=d.uf.toUpperCase();
      var cepR=(d.cep||'').replace(/\D/g,'');
      if(cepR.length===8) document.getElementById('f-cep-end').value=cepR.slice(0,5)+'-'+cepR.slice(5);
      setDocStatus('✓ '+nome,'#4ADE80');
    }catch(e){setDocStatus('Erro na consulta','#F87171');}
  }
}
</script>
"""


# ── Address block HTML ────────────────────────────────────────────────────────

def _end_html(prefix: str) -> str:
    return f"""
<div class="dmc-flex-end" style="margin-bottom:4px">
  <div style="flex:1;min-width:0">
    <label class="dmc-label">CEP</label>
    <input class="dmc-input" id="f-cep-{prefix}" placeholder="00000-000" maxlength="9"
      oninput="this.value=maskCEP(this.value)"
      onkeydown="if(event.key==='Enter')buscarCep('{prefix}')">
  </div>
  <button type="button" class="dmc-btn" onclick="buscarCep('{prefix}')">
    <span class="material-icons">search</span> Buscar CEP
  </button>
</div>
<div id="cep-status-{prefix}" class="dmc-status" style="margin-bottom:8px;color:transparent">_</div>
<div style="display:grid;grid-template-columns:1fr 72px;gap:8px;margin-bottom:8px">
  <div>
    <label class="dmc-label">Logradouro / Rua</label>
    <input class="dmc-input" id="f-log-{prefix}" placeholder="Rua, Av., Rod...">
  </div>
  <div>
    <label class="dmc-label">Nº</label>
    <input class="dmc-input" id="f-num-{prefix}" placeholder="000">
  </div>
</div>
<div style="margin-bottom:8px">
  <label class="dmc-label">Complemento</label>
  <input class="dmc-input" id="f-comp-{prefix}" placeholder="Apto, Bloco, Sala...">
</div>
<div style="display:grid;grid-template-columns:1fr 1fr 52px;gap:8px;margin-bottom:8px">
  <div>
    <label class="dmc-label">Bairro</label>
    <input class="dmc-input" id="f-bairro-{prefix}" placeholder="Bairro">
  </div>
  <div>
    <label class="dmc-label">Cidade</label>
    <input class="dmc-input" id="f-cidade-{prefix}" placeholder="Cidade">
  </div>
  <div>
    <label class="dmc-label">UF</label>
    <input class="dmc-input" id="f-uf-{prefix}" placeholder="SC" maxlength="2">
  </div>
</div>
<div class="dmc-flex-end">
  <div style="flex:1;min-width:0">
    <label class="dmc-label">Link Google Maps</label>
    <input class="dmc-input" id="f-maps-{prefix}" placeholder="Cole o link aqui...">
  </div>
  <button type="button" class="dmc-btn"
    onclick="window.open('https://maps.google.com','_blank','noopener,noreferrer')">
    <span class="material-icons">map</span> Maps
  </button>
</div>
"""


# ── Page ──────────────────────────────────────────────────────────────────────

def _build_cadastro_form():

    # ── Header ───────────────────────────────────────────────────────
    with ui.element("div").style(
        "position:sticky;top:0;z-index:1000;background:rgba(6,10,6,.97);"
        "backdrop-filter:blur(12px);border-bottom:1px solid #182418;"
        "display:flex;align-items:center;padding:0 32px;height:60px;gap:16px;"
    ):
        ui.button("Voltar", icon="arrow_back", on_click=lambda: ui.navigate.to("/")).props(
            "flat dense no-caps"
        ).style("color:#6B8F6B;font-family:'DM Mono',monospace")
        ui.element("div").style("width:1px;height:24px;background:#1E301E")
        ui.html('<span class="material-icons" style="font-size:20px;color:#4ADE80">person_add</span>')
        ui.html('<div style="font:700 16px Syne,sans-serif;color:#DCE8DC">Cadastrar Cliente</div>')
        ui.element("div").style("flex:1")
        ui.html('<div style="font:10px DM Mono,monospace;color:#374F37">DMC Topografia · Database</div>')

    # ── Conteúdo ──────────────────────────────────────────────────────
    with ui.element("div").style("padding:28px 32px 80px"):

        # Tipo toggle
        ui.html("""
        <div style="margin-bottom:24px">
          <div class="dmc-label" style="margin-bottom:12px">Tipo de Cliente</div>
          <div style="display:flex;gap:10px;max-width:380px">
            <button class="dmc-tipo-btn active" data-tipo="PF" onclick="setTipo('PF')">
              <span class="material-icons" style="font-size:16px">person</span>
              <span>Pessoa Física</span>
            </button>
            <button class="dmc-tipo-btn" data-tipo="PJ" onclick="setTipo('PJ')">
              <span class="material-icons" style="font-size:16px">business</span>
              <span>Pessoa Jurídica</span>
            </button>
          </div>
        </div>
        """)

        # Dados do cliente
        ui.html(f"""
        <div class="dmc-card">
          <div class="dmc-card-hdr">
            <span class="material-icons">person</span> Dados do Cliente
          </div>
          <div class="dmc-card-body">
            <div style="margin-bottom:12px">
              <label class="dmc-label" id="nome-label" for="f-nome">Nome Completo</label>
              <input class="dmc-input" id="f-nome" placeholder="Digite o nome completo">
            </div>
            <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:flex-end">
              <div style="min-width:0">
                <label class="dmc-label" id="doc-label">CPF</label>
                <input class="dmc-input" id="f-doc" placeholder="000.000.000-00"
                  inputmode="numeric"
                  oninput="if(/[a-zA-Z]/.test(this.value)&&dmcTipo==='PF'){{setTipo('PJ');this.value=maskCNPJ(this.value);}}else{{this.value=dmcTipo==='PF'?maskCPF(this.value):maskCNPJ(this.value);}}"
                  onkeydown="if(event.key==='Enter')buscarDoc()">
              </div>
              <button type="button" class="dmc-btn" onclick="buscarDoc()">
                <span class="material-icons">manage_search</span> Consultar
              </button>
              <div style="min-width:0">
                <label class="dmc-label">Telefone</label>
                <input class="dmc-input" id="f-tel" placeholder="(00) 00000-0000"
                  oninput="this.value=maskTel(this.value)">
              </div>
            </div>
            <div id="doc-status" class="dmc-status" style="color:transparent">_</div>
          </div>
        </div>
        """)

        # Endereços
        with ui.element("div").classes("dmc-cols-2"):

            # Pessoal
            with ui.element("div").classes("dmc-card").style("margin-bottom:0"):
                ui.html(
                    '<div class="dmc-card-hdr">'
                    '<span class="material-icons">home</span>'
                    ' Endereço Pessoal / Comercial</div>'
                )
                with ui.element("div").classes("dmc-card-body"):
                    ui.html(_end_html("end"))

            # Obra
            with ui.element("div").classes("dmc-card").style("margin-bottom:0"):
                ui.html(
                    '<div class="dmc-card-hdr">'
                    '<span class="material-icons">construction</span>'
                    ' Endereço da Obra</div>'
                )
                with ui.element("div").classes("dmc-card-body"):
                    ui.html("""
                    <label class="dmc-check-row">
                      <input type="checkbox" id="obra-mesmo" onchange="toggleObra(this.checked)">
                      <span>Mesmo endereço do cliente</span>
                    </label>
                    """)
                    with ui.element("div").props('id="obra-fields-wrap"'):
                        ui.html(_end_html("obra"))

        # Barra salvar
        with ui.element("div").style(
            "display:flex;justify-content:flex-end;gap:10px;margin-top:28px;"
            "padding-top:20px;border-top:1px solid #182418;"
        ):
            ui.button("Cancelar", on_click=lambda: ui.navigate.to("/")).props(
                "flat dense no-caps"
            ).style("color:#6B8F6B;font-family:'DM Mono',monospace")

            async def salvar():
                vals = await ui.run_javascript("""({
                  tipo: window.dmcTipo||'PF',
                  nome: (document.getElementById('f-nome')?.value||'').trim(),
                  doc:  (document.getElementById('f-doc')?.value||'').trim(),
                  tel:  (document.getElementById('f-tel')?.value||'').trim(),
                  obra_mesmo: document.getElementById('obra-mesmo')?.checked||false,
                  end_log:    (document.getElementById('f-log-end')?.value||'').trim(),
                  end_num:    (document.getElementById('f-num-end')?.value||'').trim(),
                  end_comp:   (document.getElementById('f-comp-end')?.value||'').trim(),
                  end_bairro: (document.getElementById('f-bairro-end')?.value||'').trim(),
                  end_cidade: (document.getElementById('f-cidade-end')?.value||'').trim(),
                  end_uf:     (document.getElementById('f-uf-end')?.value||'').trim().toUpperCase(),
                  end_maps:   (document.getElementById('f-maps-end')?.value||'').trim(),
                  obra_log:    (document.getElementById('f-log-obra')?.value||'').trim(),
                  obra_num:    (document.getElementById('f-num-obra')?.value||'').trim(),
                  obra_comp:   (document.getElementById('f-comp-obra')?.value||'').trim(),
                  obra_bairro: (document.getElementById('f-bairro-obra')?.value||'').trim(),
                  obra_cidade: (document.getElementById('f-cidade-obra')?.value||'').trim(),
                  obra_uf:     (document.getElementById('f-uf-obra')?.value||'').trim().toUpperCase(),
                  obra_maps:   (document.getElementById('f-maps-obra')?.value||'').trim(),
                })""")

                if not vals.get("nome") or not vals.get("doc") or not vals.get("tel"):
                    ui.notify("Preencha Nome, CPF/CNPJ e Telefone.", type="warning")
                    return

                tipo = vals.get("tipo", "PF")
                obra_mesmo = vals.get("obra_mesmo", False)
                doc_fmt = fmt_cpf(vals["doc"]) if tipo == "PF" else vals["doc"]

                cliente = {
                    "tipo":        tipo,
                    "nome":        vals["nome"],
                    "cpf":         doc_fmt,
                    "telefone":    fmt_tel(vals["tel"]),
                    "end_log":     vals["end_log"],
                    "end_num":     vals["end_num"],
                    "end_comp":    vals["end_comp"],
                    "end_bairro":  vals["end_bairro"],
                    "end_cidade":  vals["end_cidade"],
                    "end_estado":  vals["end_uf"],
                    "end_maps":    vals["end_maps"],
                    "obra_mesmo":  obra_mesmo,
                    "obra_log":    vals["obra_log"]    if not obra_mesmo else "",
                    "obra_num":    vals["obra_num"]    if not obra_mesmo else "",
                    "obra_comp":   vals["obra_comp"]   if not obra_mesmo else "",
                    "obra_bairro": vals["obra_bairro"] if not obra_mesmo else "",
                    "obra_cidade": vals["obra_cidade"] if not obra_mesmo else "",
                    "obra_estado": vals["obra_uf"]     if not obra_mesmo else "",
                    "obra_maps":   vals["obra_maps"]   if not obra_mesmo else "",
                    "data":        datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                try:
                    add_cliente(cliente, usuario=current_user_label(), perfil=current_user_perfil())
                except ValueError as _dup:
                    ui.notify(str(_dup), type="warning")
                    return
                ui.notify(f"✓ Cliente '{vals['nome']}' cadastrado!", type="positive")
                ui.navigate.to("/")

            ui.button("Salvar Cliente", on_click=salvar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style("padding:0 20px")


@ui.page("/cliente/cadastrar")
def page_cadastrar_cliente():
    from services.auth import is_authenticated
    if not is_authenticated():
        ui.navigate.to("/login")
        return
    ui.dark_mode().enable()
    ui.add_head_html(BOOTSTRAP_CDN)
    ui.add_head_html(f"<style>{CSS}</style>")
    ui.add_head_html(UTILS_JS)
    ui.add_head_html(_FORM_JS)
    _build_cadastro_form()
