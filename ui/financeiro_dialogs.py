"""Dialogs do módulo Financeiro / NFS-e."""

import base64
import json
from datetime import datetime, date
from pathlib import Path

from nicegui import ui

from services.nfse import (
    load_config, save_config, emit_nfse, save_nfse,
    cert_info, cancel_nfse, list_nfse, _DEPS_OK, _DEPS_MSG,
)


# ── Helpers de layout ──────────────────────────────────────────────────

def _section(label: str):
    ui.html(
        f'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
        f'letter-spacing:.14em;text-transform:uppercase;'
        f'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-bottom:10px">'
        f'{label}</div>'
    )


def _label(txt: str):
    ui.html(f'<label class="dmc-label">{txt}</label>')


def _row2(fn):
    with ui.element('div').style('display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:12px'):
        fn()


# ── Configuração ───────────────────────────────────────────────────────

def config_nfse_dialog(on_save=None) -> None:
    cfg = load_config()
    _st = dict(cfg)

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(680px,97vw)!important;max-height:94vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#4ADE80">settings</span></div>'
            )
            with ui.element('div'):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Configuração NFS-e</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">Dados do prestador e certificado digital</div>')

        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1;min-height:0'):

            ui.html('<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">Prestador</div>')

            def _inp(label, key, placeholder='', mono=False):
                _label(label)
                font = 'var(--dmc-mono)' if mono else 'var(--dmc-fm)'
                inp = ui.input(value=_st.get(key, ''), placeholder=placeholder).props(
                    'borderless dense outlined'
                ).style(
                    f'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                    f'border-radius:8px;padding:0 12px;margin-bottom:12px;font:{font}'
                )
                inp.on('change', lambda e, k=key: _st.update({k: e.value or ''}))
                return inp

            with ui.element('div').style('display:grid;grid-template-columns:1fr 1fr;gap:14px'):
                with ui.element('div'):
                    _inp('CNPJ', 'cnpj', '00.000.000/0000-00', mono=True)
                with ui.element('div'):
                    _inp('Inscrição Municipal', 'im', 'Nº municipal', mono=True)

            _inp('Razão Social', 'razao_social', 'Nome da empresa')

            with ui.element('div').style('display:grid;grid-template-columns:2fr 1fr;gap:14px'):
                with ui.element('div'):
                    _inp('Código IBGE do Município', 'cod_municipio', 'Ex: 4205407', mono=True)
                with ui.element('div'):
                    _inp('Série DPS', 'serie', '1', mono=True)

            _inp('Alíquota ISS (%)', 'aliquota_iss', '5.00', mono=True)

            _section('Ambiente')
            ui.html(
                '<div style="display:flex;gap:10px;margin-bottom:14px">'
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b2);border-radius:8px;'
                'padding:8px 16px;font:13px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="radio" name="cfg-amb" value="homologacao" style="accent-color:#FBBF24"'
                + (' checked' if _st.get('ambiente') == 'homologacao' else '') +
                '> Homologação (testes)</label>'
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b2);border-radius:8px;'
                'padding:8px 16px;font:13px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="radio" name="cfg-amb" value="producao" style="accent-color:#4ADE80"'
                + (' checked' if _st.get('ambiente') == 'producao' else '') +
                '> Produção</label>'
                '</div>'
            )

            _section('Certificado Digital (.pfx / .p12)')

            _label('Caminho do arquivo (.pfx ou .p12)')
            cert_inp = ui.input(value=_st.get('cert_path', ''), placeholder='/caminho/para/cert.pfx').props(
                'borderless dense outlined'
            ).style(
                'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                'border-radius:8px;padding:0 12px;margin-bottom:12px;font:var(--dmc-mono)'
            )
            cert_inp.on('change', lambda e: _st.update({'cert_path': e.value or ''}))

            _label('Senha do certificado')
            _cert_pw_val = _st.get('cert_senha', '')
            with ui.element('div').style('position:relative;margin-bottom:12px;width:100%'):
                ui.html(
                    f'<input type="password" id="fin-cert-pw" class="dmc-input"'
                    f' value="{_cert_pw_val}" placeholder="••••••••" autocomplete="off"'
                    ' style="padding-right:44px;height:40px;width:100%;box-sizing:border-box">'
                )
                with ui.element('button').style(
                    'position:absolute;right:0;top:0;height:40px;width:40px;'
                    'background:transparent;border:none;cursor:pointer;'
                    'display:flex;align-items:center;justify-content:center;padding:0;'
                ).props('type=button tabindex=-1') as _pw_tog:
                    _pw_icon = ui.html(
                        '<span class="material-icons" '
                        'style="font-size:18px;color:var(--dmc-muted)">visibility_off</span>'
                    )

                async def _pw_toggle():
                    state = await ui.run_javascript(
                        "var i=document.getElementById('fin-cert-pw');"
                        "if(!i) return 'x';"
                        "if(i.type==='password'){i.type='text';return 'text';}"
                        "i.type='password';return 'password';"
                    )
                    _pw_icon.set_content(
                        '<span class="material-icons" style="font-size:18px;color:var(--dmc-muted)">'
                        + ('visibility' if state == 'text' else 'visibility_off') + '</span>'
                    )
                _pw_tog.on('click', _pw_toggle)

            cert_status = ui.html('<div style="min-height:18px"></div>')

            async def _test_cert():
                path  = _st.get('cert_path', '')
                senha = await ui.run_javascript(
                    "document.getElementById('fin-cert-pw')?.value || ''"
                )
                _st['cert_senha'] = senha
                if not path or not Path(path).exists():
                    cert_status.set_content('<div style="font:11px var(--dmc-mono);color:#F87171">Arquivo não encontrado.</div>')
                    return
                try:
                    info = cert_info(path, senha)
                    cert_status.set_content(
                        f'<div style="font:11px var(--dmc-mono);color:#4ADE80">'
                        f'✓ {info["cn"]} · Válido até {info["validade"]}</div>'
                    )
                except Exception as ex:
                    cert_status.set_content(f'<div style="font:11px var(--dmc-mono);color:#F87171">Erro: {ex}</div>')

            ui.button('Testar certificado', icon='verified', on_click=_test_cert).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-secondary').style('margin-bottom:4px')

        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0'
        ):
            ui.button('Cancelar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _salvar():
                amb = await ui.run_javascript(
                    "document.querySelector('input[name=\"cfg-amb\"]:checked')?.value || 'homologacao'"
                )
                _st['ambiente'] = amb
                _st['cert_senha'] = await ui.run_javascript(
                    "document.getElementById('fin-cert-pw')?.value || ''"
                )
                try:
                    save_config(_st)
                    ui.notify('Configuração salva.', type='positive')
                    if on_save:
                        on_save()
                    dlg.close()
                except Exception as ex:
                    ui.notify(f'Erro ao salvar: {ex}', type='negative')

            ui.button('Salvar', icon='save', on_click=_salvar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary')

    dlg.open()


# ── Emissão NFS-e ──────────────────────────────────────────────────────

def emitir_nfse_dialog(on_success=None) -> None:
    cfg = load_config()

    if not cfg.get('cnpj'):
        ui.notify('Configure o CNPJ do prestador antes de emitir.', type='warning')
        config_nfse_dialog(on_save=lambda: emitir_nfse_dialog(on_success))
        return

    _st: dict = {
        'toma_tipo':   'CNPJ',
        'toma_doc':    '',
        'toma_nome':   '',
        'toma_cep':    '',
        'toma_end':    '',
        'toma_num':    '',
        'toma_bairro': '',
        'toma_cidade': '',
        'toma_uf':     '',
        'toma_cod_mun': '',
        'descricao':   '',
        'cod_tributacao': '010101',
        'cod_nbs':     '',
        'valor':       '',
        'iss_retido':  False,
    }

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(760px,97vw)!important;height:94vh;max-height:94vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#4ADE80">receipt_long</span></div>'
            )
            with ui.element('div'):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Emitir NFS-e</div>')
                amb = cfg.get('ambiente', 'homologacao')
                amb_col = '#FBBF24' if amb == 'homologacao' else '#4ADE80'
                amb_lbl = 'HOMOLOGAÇÃO' if amb == 'homologacao' else 'PRODUÇÃO'
                ui.html(
                    f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    f'Prestador: {cfg.get("razao_social") or cfg.get("cnpj")} · '
                    f'<span style="color:{amb_col};font-weight:600">{amb_lbl}</span></div>'
                )

        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1;min-height:0'):

            # ── Tomador ────────────────────────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">Tomador</div>'
            )

            ui.html(
                '<div style="display:flex;gap:10px;margin-bottom:12px">'
                '<label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;'
                'font:13px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="radio" name="toma-tipo" value="CNPJ" checked style="accent-color:#4ADE80"> '
                'CNPJ</label>'
                '<label style="display:inline-flex;align-items:center;gap:6px;cursor:pointer;'
                'font:13px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="radio" name="toma-tipo" value="CPF" style="accent-color:#4ADE80"> '
                'CPF (Pessoa Física)</label>'
                '</div>'
            )

            def _f(label, key, placeholder='', mono=False, grid_span=False):
                font = 'var(--dmc-mono)' if mono else 'var(--dmc-fm)'
                _label(label)
                inp = ui.input(placeholder=placeholder).props('borderless dense outlined').style(
                    f'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                    f'border-radius:8px;padding:0 12px;margin-bottom:12px;font:{font}'
                )
                inp.on('change', lambda e, k=key: _st.update({k: e.value or ''}))
                return inp

            with ui.element('div').style('display:grid;grid-template-columns:1fr 2fr;gap:14px'):
                with ui.element('div'):
                    _f('CPF / CNPJ', 'toma_doc', '', mono=True)
                with ui.element('div'):
                    _f('Razão Social / Nome', 'toma_nome', 'Nome do tomador')

            with ui.element('div').style('display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px'):
                with ui.element('div').style('grid-column:span 2'):
                    _f('Logradouro', 'toma_end', 'Rua/Avenida')
                with ui.element('div'):
                    _f('Número', 'toma_num', 'S/N')
                with ui.element('div'):
                    _f('CEP', 'toma_cep', '00000-000', mono=True)

            with ui.element('div').style('display:grid;grid-template-columns:2fr 2fr 1fr;gap:14px'):
                with ui.element('div'):
                    _f('Bairro', 'toma_bairro', '')
                with ui.element('div'):
                    _f('Cidade', 'toma_cidade', '')
                with ui.element('div'):
                    _f('UF', 'toma_uf', 'SC')

            with ui.element('div').style('display:grid;grid-template-columns:1fr 1fr;gap:14px'):
                with ui.element('div'):
                    _f('Código IBGE do Tomador', 'toma_cod_mun', cfg.get('cod_municipio', ''), mono=True)

            # ── Serviço ────────────────────────────────────────────────
            _section('Serviço')

            _label('Descrição do serviço prestado')
            desc_inp = ui.textarea(placeholder='Descreva o serviço prestado...').props(
                'borderless dense outlined rows=3'
            ).style(
                'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                'border-radius:8px;padding:8px 12px;margin-bottom:12px;'
                'font:13px var(--dmc-fm);resize:vertical'
            )
            desc_inp.on('change', lambda e: _st.update({'descricao': e.value or ''}))

            with ui.element('div').style('display:grid;grid-template-columns:1fr 1fr;gap:14px'):
                with ui.element('div'):
                    _label('Código Tributação Nacional (cTribNac)')
                    cod_trib = ui.input(value='010101', placeholder='010101').props(
                        'borderless dense outlined'
                    ).style(
                        'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                        'border-radius:8px;padding:0 12px;margin-bottom:12px;font:var(--dmc-mono)'
                    )
                    cod_trib.on('change', lambda e: _st.update({'cod_tributacao': e.value or '010101'}))
                with ui.element('div'):
                    _label('Código NBS (cNBS — obrigatório 2026+)')
                    cod_nbs = ui.input(placeholder='Ex: 1.0301.00.00').props(
                        'borderless dense outlined'
                    ).style(
                        'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                        'border-radius:8px;padding:0 12px;margin-bottom:12px;font:var(--dmc-mono)'
                    )
                    cod_nbs.on('change', lambda e: _st.update({'cod_nbs': e.value or ''}))

            # Código NBS info
            ui.html(
                '<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                'background:rgba(96,165,250,.06);border:1px solid rgba(96,165,250,.15);'
                'border-radius:6px;padding:6px 10px;margin-bottom:14px">'
                'Consulte o código NBS em: '
                '<span style="color:#60A5FA">nfse.gov.br → Nomenclatura Brasileira de Serviços</span>'
                '</div>'
            )

            # ── Valores ────────────────────────────────────────────────
            _section('Valores')

            aliq = cfg.get('aliquota_iss', '5.00')
            valor_display = ui.html('<div style="min-height:18px"></div>')

            with ui.element('div').style('display:grid;grid-template-columns:1fr 1fr;gap:14px'):
                with ui.element('div'):
                    _label('Valor do serviço (R$)')
                    valor_inp = ui.input(placeholder='0,00').props(
                        'borderless dense outlined'
                    ).style(
                        'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                        'border-radius:8px;padding:0 12px;margin-bottom:8px;font:var(--dmc-mono)'
                    )
                    def _on_valor(e):
                        v = (e.value or '').replace(',', '.')
                        try:
                            vf = float(v)
                            iss = round(vf * float(aliq) / 100, 2)
                            valor_display.set_content(
                                f'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                                f'ISS ({aliq}%): <span style="color:#FBBF24">R$ {iss:.2f}</span>'
                                f' · Líquido: <span style="color:#4ADE80">R$ {vf-iss:.2f}</span></div>'
                            )
                        except ValueError:
                            valor_display.set_content('<div style="min-height:18px"></div>')
                        _st['valor'] = v
                    valor_inp.on('input', _on_valor)

                with ui.element('div'):
                    _label(f'Alíquota ISS configurada')
                    ui.html(
                        f'<div style="background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                        f'border-radius:8px;padding:0 12px;height:40px;'
                        f'display:flex;align-items:center;margin-bottom:8px">'
                        f'<span style="font:600 15px var(--dmc-mono);color:#FBBF24">{aliq}%</span>'
                        f'<span style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-left:8px">'
                        f'(configurável em ⚙ Configurar)</span>'
                        f'</div>'
                    )

            ui.html(
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:13px var(--dmc-fm);color:var(--dmc-text);margin-bottom:14px">'
                '<input type="checkbox" id="nfse-iss-retido" style="accent-color:#4ADE80;'
                'width:16px;height:16px"> ISS Retido pelo Tomador</label>'
            )

            status_box = ui.element('div')

        # ── Rodapé ─────────────────────────────────────────────────────
        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0'
        ):
            ui.button('Cancelar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            btn_emitir = ui.button('Emitir NFS-e', icon='send').props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary')

            async def _emitir():
                if not _DEPS_OK:
                    ui.notify(_DEPS_MSG, type='negative', multi_line=True)
                    return

                # Coleta dados do JS
                tipo = await ui.run_javascript(
                    "document.querySelector('input[name=\"toma-tipo\"]:checked')?.value || 'CNPJ'"
                )
                iss_ret = await ui.run_javascript(
                    "document.getElementById('nfse-iss-retido')?.checked || false"
                )
                _st['toma_tipo']  = tipo
                _st['iss_retido'] = bool(iss_ret)

                # Validações básicas
                erros = []
                if not _st.get('toma_doc'):
                    erros.append('CPF/CNPJ do tomador é obrigatório.')
                if not _st.get('toma_nome'):
                    erros.append('Nome do tomador é obrigatório.')
                if not _st.get('descricao'):
                    erros.append('Descrição do serviço é obrigatória.')
                if not _st.get('valor'):
                    erros.append('Valor do serviço é obrigatório.')
                try:
                    float(str(_st.get('valor', '')).replace(',', '.'))
                except ValueError:
                    erros.append('Valor inválido.')

                if erros:
                    status_box.clear()
                    with status_box:
                        ui.html(
                            '<div style="margin:0 0 8px;padding:10px 14px;'
                            'background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);'
                            'border-radius:8px;font:12px var(--dmc-fm);color:#F87171">'
                            + '<br>'.join(erros) + '</div>'
                        )
                    return

                _st['valor'] = float(str(_st['valor']).replace(',', '.'))
                cfg_atual = load_config()
                cfg_atual['proximo_num'] = cfg_atual.get('proximo_num', 1)

                btn_emitir.disable()
                status_box.clear()
                with status_box:
                    ui.html(
                        '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);'
                        'padding:8px 0">⏳ Enviando para a API NFS-e Nacional...</div>'
                    )

                try:
                    result = emit_nfse(_st, cfg_atual)
                    save_nfse(result)

                    if result['sucesso']:
                        cfg_atual['proximo_num'] = cfg_atual.get('proximo_num', 1) + 1
                        save_config(cfg_atual)
                        ui.notify(
                            f'NFS-e emitida com sucesso! Nº {result["numero"]}',
                            type='positive',
                        )
                        if on_success:
                            on_success()
                        dlg.close()
                    else:
                        erros_api = result.get('erros', ['Erro desconhecido.'])
                        status_box.clear()
                        with status_box:
                            ui.html(
                                '<div style="margin:8px 0;padding:10px 14px;'
                                'background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);'
                                'border-radius:8px;font:12px var(--dmc-mono);color:#F87171">'
                                '<b>Erros da API:</b><br>'
                                + '<br>'.join(erros_api) + '</div>'
                            )
                        save_nfse(result)
                        if on_success:
                            on_success()
                except Exception as ex:
                    status_box.clear()
                    with status_box:
                        ui.html(
                            f'<div style="margin:8px 0;padding:10px 14px;'
                            f'background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);'
                            f'border-radius:8px;font:12px var(--dmc-mono);color:#F87171">'
                            f'<b>Exceção:</b> {ex}</div>'
                        )
                finally:
                    btn_emitir.enable()

            btn_emitir.on('click', _emitir)

    dlg.open()


# ── Visualização NFS-e ─────────────────────────────────────────────────

def ver_nfse_dialog(entry: dict) -> None:
    sucesso = entry.get('sucesso', False)
    num     = entry.get('numero', '—')
    toma    = entry.get('tomador', '—')
    val     = entry.get('valor', 0)
    amb     = entry.get('ambiente', 'homologacao')
    emitido = (entry.get('emitido_em', '') or '')[:16].replace('T', ' ')
    chave   = entry.get('chave_acesso', '—')
    erros   = entry.get('erros', [])
    dados   = entry.get('dados', {})

    amb_col = '#FBBF24' if amb == 'homologacao' else '#4ADE80'
    amb_lbl = 'HOMOLOGAÇÃO' if amb == 'homologacao' else 'PRODUÇÃO'
    val_fmt = f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(680px,97vw)!important;max-height:94vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        status_color = '#4ADE80' if sucesso else '#F87171'
        status_icon  = 'check_circle' if sucesso else 'error'

        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                f'<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                f'background:{status_color}14;border:1px solid {status_color}33;'
                f'display:flex;align-items:center;justify-content:center;">'
                f'<span class="material-icons" style="font-size:20px;color:{status_color}">{status_icon}</span></div>'
            )
            with ui.element('div'):
                ui.html(f'<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">NFS-e #{num}</div>')
                ui.html(
                    f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    f'<span style="color:{amb_col};font-weight:600">{amb_lbl}</span>'
                    f' · Emitida em {emitido}</div>'
                )

        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1;min-height:0'):

            def _row(lbl, val, color='var(--dmc-text)'):
                ui.html(
                    f'<div style="display:flex;justify-content:space-between;'
                    f'padding:8px 0;border-bottom:1px solid var(--dmc-b1)">'
                    f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                    f'text-transform:uppercase;letter-spacing:.06em">{lbl}</span>'
                    f'<span style="font:13px var(--dmc-mono);color:{color}">{val}</span>'
                    f'</div>'
                )

            _row('Número', f'#{num}', '#4ADE80')
            _row('Tomador', toma)
            _row('Valor', val_fmt, '#FBBF24')
            _row('Ambiente', amb_lbl, amb_col)
            _row('Emitido em', emitido)
            if chave and chave != '—':
                _row('Chave de acesso', chave[:20] + '...' if len(chave) > 20 else chave)
            if dados.get('descricao'):
                _row('Serviço', dados['descricao'][:80] + ('...' if len(dados.get('descricao', '')) > 80 else ''))
            if dados.get('cod_nbs'):
                _row('Código NBS', dados['cod_nbs'])

            if erros:
                ui.html(
                    '<div style="margin-top:14px;padding:10px 14px;'
                    'background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);'
                    'border-radius:8px">'
                    '<div style="font:600 10px var(--dmc-mono);color:#F87171;'
                    'letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px">Erros</div>'
                    + ''.join(f'<div style="font:12px var(--dmc-mono);color:#FCA5A5">{e}</div>' for e in erros)
                    + '</div>'
                )

        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0'
        ):
            if entry.get('nfse_xml'):
                async def _dl_xml():
                    xml_b64 = base64.b64encode(entry['nfse_xml'].encode()).decode()
                    fname   = f'NFSe_{num}.xml'
                    await ui.run_javascript(f'''
                        const a = document.createElement('a');
                        a.href = 'data:application/xml;base64,{xml_b64}';
                        a.download = '{fname}';
                        document.body.appendChild(a); a.click();
                        document.body.removeChild(a);
                    ''')
                ui.button('Download XML', icon='download', on_click=_dl_xml).props(
                    'unelevated no-caps'
                ).classes('dmc-btn dmc-btn-secondary')

            ui.button('Fechar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

    dlg.open()


# ── Relatório Financeiro ───────────────────────────────────────────────

def _fmt_brl(v: float) -> str:
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _filter_entries(entries: list, periodo: str, de: str, ate: str,
                    inc_emitida: bool, inc_homo: bool, inc_erro: bool) -> list:
    hoje = date.today()

    if periodo == 'mes_atual':
        ini = hoje.replace(day=1).isoformat()
        fim = hoje.isoformat()
    elif periodo == 'mes_anterior':
        if hoje.month == 1:
            ini = date(hoje.year - 1, 12, 1).isoformat()
            fim = date(hoje.year - 1, 12, 31).isoformat()
        else:
            import calendar
            last = calendar.monthrange(hoje.year, hoje.month - 1)[1]
            ini = date(hoje.year, hoje.month - 1, 1).isoformat()
            fim = date(hoje.year, hoje.month - 1, last).isoformat()
    elif periodo == '3meses':
        from dateutil.relativedelta import relativedelta  # type: ignore
        ini = (hoje - relativedelta(months=3)).isoformat()
        fim = hoje.isoformat()
    elif periodo == 'ano_atual':
        ini = hoje.replace(month=1, day=1).isoformat()
        fim = hoje.isoformat()
    else:
        ini = de or '2000-01-01'
        fim = ate or hoje.isoformat()

    out = []
    for e in entries:
        dt = (e.get('emitido_em', '') or '')[:10]
        if dt and not (ini <= dt <= fim):
            continue
        sucesso = e.get('sucesso', False)
        amb = e.get('ambiente', 'homologacao')
        if sucesso and amb == 'producao' and not inc_emitida:
            continue
        if sucesso and amb == 'homologacao' and not inc_homo:
            continue
        if not sucesso and not inc_erro:
            continue
        out.append(e)
    return out


def _build_report_html(entries: list, cfg: dict, periodo_label: str) -> str:
    empresa   = cfg.get('razao_social') or 'Empresa'
    cnpj_raw  = cfg.get('cnpj') or ''
    cnpj_fmt  = (
        f'{cnpj_raw[:2]}.{cnpj_raw[2:5]}.{cnpj_raw[5:8]}/{cnpj_raw[8:12]}-{cnpj_raw[12:]}'
        if len(cnpj_raw) == 14 else cnpj_raw
    )
    now_str   = datetime.now().strftime('%d/%m/%Y %H:%M')
    aliq      = float(cfg.get('aliquota_iss', '5.00') or '5.00')

    total     = sum(float(e.get('valor', 0) or 0) for e in entries)
    total_iss = round(total * aliq / 100, 2)
    total_liq = round(total - total_iss, 2)
    n_emit    = sum(1 for e in entries if e.get('sucesso') and e.get('ambiente') == 'producao')
    n_homo    = sum(1 for e in entries if e.get('sucesso') and e.get('ambiente') == 'homologacao')
    n_erro    = sum(1 for e in entries if not e.get('sucesso'))

    rows_html = ''
    for e in entries:
        sucesso = e.get('sucesso', False)
        amb     = e.get('ambiente', 'homologacao')
        if not sucesso:
            s_lbl, s_cls = 'ERRO',        'err'
        elif amb == 'homologacao':
            s_lbl, s_cls = 'HOMOLOGAÇÃO', 'hom'
        else:
            s_lbl, s_cls = 'EMITIDA',     'ok'

        val     = float(e.get('valor', 0) or 0)
        iss_v   = round(val * aliq / 100, 2)
        emitido = (e.get('emitido_em', '') or '')[:10]
        desc    = (e.get('descricao', '') or '')[:55]
        if len(e.get('descricao', '') or '') > 55:
            desc += '…'

        rows_html += (
            f'<tr>'
            f'<td class="tc num-col">#{e.get("numero", "—")}</td>'
            f'<td>{e.get("tomador", "—")}<div class="desc">{desc}</div></td>'
            f'<td class="tr mono">{_fmt_brl(val)}</td>'
            f'<td class="tr mono muted">{_fmt_brl(iss_v)}</td>'
            f'<td class="tc"><span class="badge {s_cls}">{s_lbl}</span></td>'
            f'<td class="tc mono muted">{emitido}</td>'
            f'</tr>'
        )

    if not rows_html:
        rows_html = '<tr><td colspan="6" class="tc muted" style="padding:32px">Nenhuma NFS-e no período.</td></tr>'

    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Relatório NFS-e — {empresa}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px; color: #1a1a1a; background: #f8f8f8;
  }}
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 32px 24px; }}

  /* ── Header ── */
  .rpt-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    border-bottom: 3px solid #15803d; padding-bottom: 18px; margin-bottom: 24px;
  }}
  .rpt-empresa {{ font-size: 20px; font-weight: 700; color: #15803d; }}
  .rpt-cnpj    {{ font-size: 11px; color: #555; margin-top: 3px; font-family: monospace; }}
  .rpt-meta    {{ text-align: right; font-size: 11px; color: #555; line-height: 1.8; }}
  .rpt-periodo {{ font-weight: 600; color: #1a1a1a; font-size: 13px; }}

  /* ── Summary cards ── */
  .summary {{
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px; margin-bottom: 24px;
  }}
  .s-card {{
    background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
    padding: 14px 16px;
  }}
  .s-card .lbl {{
    font-size: 9px; font-weight: 600; letter-spacing: .1em;
    text-transform: uppercase; color: #6b7280; margin-bottom: 6px;
  }}
  .s-card .val {{ font-size: 18px; font-weight: 700; }}
  .s-card .sub {{ font-size: 10px; color: #9ca3af; margin-top: 2px; }}
  .c-green  {{ color: #15803d; }}
  .c-blue   {{ color: #1d4ed8; }}
  .c-amber  {{ color: #b45309; }}
  .c-red    {{ color: #dc2626; }}
  .c-slate  {{ color: #475569; }}

  /* ── Table ── */
  .rpt-card {{
    background: #fff; border: 1px solid #e5e7eb;
    border-radius: 12px; overflow: hidden; margin-bottom: 20px;
  }}
  .rpt-card-hdr {{
    padding: 12px 18px; border-bottom: 1px solid #e5e7eb;
    font-size: 11px; font-weight: 600; letter-spacing: .08em;
    text-transform: uppercase; color: #374151;
    display: flex; justify-content: space-between; align-items: center;
  }}
  table {{ width: 100%; border-collapse: collapse; }}
  thead th {{
    padding: 10px 14px; text-align: left;
    font-size: 10px; font-weight: 600; letter-spacing: .07em;
    text-transform: uppercase; color: #6b7280;
    background: #f9fafb; border-bottom: 1px solid #e5e7eb;
  }}
  tbody tr {{ border-bottom: 1px solid #f3f4f6; }}
  tbody tr:last-child {{ border-bottom: none; }}
  tbody tr:hover {{ background: #fafafa; }}
  tbody td {{ padding: 9px 14px; vertical-align: middle; }}
  .desc  {{ font-size: 11px; color: #6b7280; margin-top: 2px; }}
  .mono  {{ font-family: 'DM Mono', 'Courier New', monospace; }}
  .muted {{ color: #6b7280; }}
  .tc    {{ text-align: center; }}
  .tr    {{ text-align: right; }}
  .num-col {{ font-weight: 600; color: #15803d; font-family: monospace; }}

  /* ── Badges ── */
  .badge {{
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 9px; font-weight: 700; letter-spacing: .08em;
    border: 1px solid;
  }}
  .badge.ok  {{ color: #15803d; background: #f0fdf4; border-color: #bbf7d0; }}
  .badge.hom {{ color: #b45309; background: #fffbeb; border-color: #fde68a; }}
  .badge.err {{ color: #dc2626; background: #fef2f2; border-color: #fecaca; }}

  /* ── Totals row ── */
  .totals-row td {{
    padding: 10px 14px; font-weight: 700;
    background: #f9fafb; border-top: 2px solid #e5e7eb;
  }}

  /* ── Footer ── */
  .rpt-footer {{
    font-size: 10px; color: #9ca3af; text-align: center;
    border-top: 1px solid #e5e7eb; padding-top: 14px; margin-top: 8px;
  }}

  /* ── Print button (hidden on print) ── */
  .print-bar {{
    position: fixed; top: 0; left: 0; right: 0;
    background: #15803d; color: #fff; padding: 10px 24px;
    display: flex; align-items: center; gap: 16px;
    font-size: 13px; font-weight: 500; z-index: 99;
    box-shadow: 0 2px 8px rgba(0,0,0,.15);
  }}
  .print-bar button {{
    background: #fff; color: #15803d; border: none;
    border-radius: 6px; padding: 6px 18px;
    font-size: 12px; font-weight: 700; cursor: pointer;
  }}
  .print-bar button:hover {{ background: #f0fdf4; }}
  .print-bar .close-btn {{
    background: rgba(255,255,255,.15); color: #fff;
    margin-left: auto;
  }}
  @media print {{
    .print-bar {{ display: none !important; }}
    body {{ background: #fff; }}
    .wrap {{ padding: 0; }}
    .rpt-card {{ box-shadow: none; }}
  }}
  @media (max-width: 700px) {{
    .summary {{ grid-template-columns: repeat(2, 1fr); }}
    .hide-sm {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="print-bar">
  <span>📄 Relatório NFS-e — {empresa}</span>
  <button onclick="window.print()">🖨 Imprimir / Salvar PDF</button>
  <button class="close-btn" onclick="window.close()">✕ Fechar</button>
</div>

<div class="wrap" style="margin-top:52px">

  <div class="rpt-header">
    <div>
      <div class="rpt-empresa">{empresa}</div>
      <div class="rpt-cnpj">CNPJ: {cnpj_fmt}</div>
    </div>
    <div class="rpt-meta">
      <div class="rpt-periodo">{periodo_label}</div>
      <div>Gerado em {now_str}</div>
      <div>{len(entries)} nota(s) no período</div>
    </div>
  </div>

  <div class="summary">
    <div class="s-card">
      <div class="lbl">Total bruto</div>
      <div class="val c-green">{_fmt_brl(total)}</div>
      <div class="sub">{len(entries)} nota(s)</div>
    </div>
    <div class="s-card">
      <div class="lbl">ISS ({aliq:.2f}%)</div>
      <div class="val c-amber">{_fmt_brl(total_iss)}</div>
      <div class="sub">Total retido</div>
    </div>
    <div class="s-card">
      <div class="lbl">Valor líquido</div>
      <div class="val c-blue">{_fmt_brl(total_liq)}</div>
      <div class="sub">Bruto − ISS</div>
    </div>
    <div class="s-card">
      <div class="lbl">Emitidas</div>
      <div class="val c-green">{n_emit}</div>
      <div class="sub">Produção</div>
    </div>
    <div class="s-card">
      <div class="lbl">Homologação</div>
      <div class="val c-amber">{n_homo}</div>
      <div class="sub">{"+ " + str(n_erro) + " erro(s)" if n_erro else "sem erros"}</div>
    </div>
  </div>

  <div class="rpt-card">
    <div class="rpt-card-hdr">
      <span>Notas Fiscais de Serviço — NFS-e</span>
      <span style="font-weight:400;color:#9ca3af">{periodo_label}</span>
    </div>
    <table>
      <thead>
        <tr>
          <th style="width:60px">Nº</th>
          <th>Tomador / Descrição</th>
          <th style="width:130px;text-align:right">Valor</th>
          <th style="width:110px;text-align:right">ISS</th>
          <th style="width:100px;text-align:center">Status</th>
          <th style="width:100px;text-align:center">Emitida em</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
        <tr class="totals-row">
          <td colspan="2" class="muted" style="font-size:11px">
            Total — {len(entries)} nota(s)
          </td>
          <td class="tr mono c-green">{_fmt_brl(total)}</td>
          <td class="tr mono c-amber">{_fmt_brl(total_iss)}</td>
          <td colspan="2"></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="rpt-footer">
    DMC Topografia · Sistema de Gestão · Relatório gerado automaticamente em {now_str}
  </div>

</div>
</body>
</html>'''


def relatorio_financeiro_dialog() -> None:
    cfg = load_config()
    _st = {
        'periodo':    'mes_atual',
        'de':         '',
        'ate':        '',
        'inc_emitida': True,
        'inc_homo':    True,
        'inc_erro':    True,
    }

    _PERIODOS = [
        ('mes_atual',    'Mês atual'),
        ('mes_anterior', 'Mês anterior'),
        ('3meses',       'Últimos 3 meses'),
        ('ano_atual',    'Ano atual'),
        ('personalizado','Período personalizado'),
    ]

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(560px,97vw)!important;max-height:94vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#60A5FA">bar_chart</span></div>'
            )
            with ui.element('div'):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Relatório Financeiro</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">NFS-e emitidas — exporta como PDF / impressão</div>')

        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1;min-height:0'):

            # Período
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">Período</div>'
            )
            periodo_sel = ui.select(
                options={k: v for k, v in _PERIODOS},
                value='mes_atual',
            ).props('outlined dense options-dense').style(
                'width:100%;background:var(--dmc-bg3);border-radius:8px;margin-bottom:12px'
            )
            periodo_sel.on('update:model-value', lambda e: _st.update({'periodo': e.value}))

            custom_box = ui.element('div').style(
                'display:none;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:12px'
            )
            with custom_box:
                with ui.element('div'):
                    ui.html('<label class="dmc-label">De</label>')
                    de_inp = ui.input(placeholder='AAAA-MM-DD').props('borderless dense outlined').style(
                        'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                        'border-radius:8px;padding:0 12px;font:var(--dmc-mono)'
                    )
                    de_inp.on('change', lambda e: _st.update({'de': e.value or ''}))
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Até</label>')
                    ate_inp = ui.input(placeholder='AAAA-MM-DD').props('borderless dense outlined').style(
                        'width:100%;background:var(--dmc-bg3);border:1px solid var(--dmc-b2);'
                        'border-radius:8px;padding:0 12px;font:var(--dmc-mono)'
                    )
                    ate_inp.on('change', lambda e: _st.update({'ate': e.value or ''}))

            def _on_periodo(e):
                _st['periodo'] = e.value
                custom_box.style(
                    'display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:12px'
                    if e.value == 'personalizado' else 'display:none'
                )
            periodo_sel.on('update:model-value', _on_periodo)

            # Filtro de status
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-top:4px;margin-bottom:10px">'
                'Incluir status</div>'
            )
            ui.html(
                '<div style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px">'
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:13px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="checkbox" id="rfi-emit" checked style="accent-color:#4ADE80;width:15px;height:15px">'
                ' <span style="color:#4ADE80;font:600 10px var(--dmc-mono)">EMITIDA</span>'
                ' <span style="color:var(--dmc-muted2);font-size:12px">— produção</span></label>'
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:13px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="checkbox" id="rfi-homo" checked style="accent-color:#FBBF24;width:15px;height:15px">'
                ' <span style="color:#FBBF24;font:600 10px var(--dmc-mono)">HOMOLOGAÇÃO</span>'
                ' <span style="color:var(--dmc-muted2);font-size:12px">— testes</span></label>'
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:13px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="checkbox" id="rfi-erro" checked style="accent-color:#F87171;width:15px;height:15px">'
                ' <span style="color:#F87171;font:600 10px var(--dmc-mono)">ERRO</span>'
                ' <span style="color:var(--dmc-muted2);font-size:12px">— falhas de emissão</span></label>'
                '</div>'
            )

        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0'
        ):
            ui.button('Cancelar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _gerar():
                _st['inc_emitida'] = await ui.run_javascript(
                    "document.getElementById('rfi-emit')?.checked ?? true"
                )
                _st['inc_homo'] = await ui.run_javascript(
                    "document.getElementById('rfi-homo')?.checked ?? true"
                )
                _st['inc_erro'] = await ui.run_javascript(
                    "document.getElementById('rfi-erro')?.checked ?? true"
                )

                entries = _filter_entries(
                    list_nfse(),
                    _st['periodo'], _st['de'], _st['ate'],
                    bool(_st['inc_emitida']),
                    bool(_st['inc_homo']),
                    bool(_st['inc_erro']),
                )

                periodo_label = dict(_PERIODOS).get(_st['periodo'], _st['periodo'])
                if _st['periodo'] == 'personalizado' and (_st['de'] or _st['ate']):
                    periodo_label = f'{_st["de"] or "?"} → {_st["ate"] or "?"}'

                html = _build_report_html(entries, cfg, periodo_label)
                html_b64 = base64.b64encode(html.encode('utf-8')).decode()
                await ui.run_javascript(f'''
                    const w = window.open('', '_blank', 'width=1000,height=720,noopener,noreferrer');
                    const html = atob('{html_b64}');
                    w.document.open();
                    w.document.write(html);
                    w.document.close();
                ''')

            ui.button('Gerar Relatório', icon='bar_chart', on_click=_gerar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary')

    dlg.open()
