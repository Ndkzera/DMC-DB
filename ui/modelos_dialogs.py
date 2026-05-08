"""Dialog de gerenciamento de modelos de documento .docx."""

from nicegui import ui

from config import MODELOS_DIR

_MARCADORES = [
    ("-NOME DO CLIENTE-",   "Nome completo do cliente",                          "Cliente"),
    ("-CPF/CNPJ-",          "CPF ou CNPJ com label  (ex: CPF: 000.000.000-00)", "Cliente"),
    ("-LOGRADOURO / RUA-",  "Logradouro / rua da área ou obra",                  "Endereço"),
    ("-Nº-",                "Número  (ex: Nº 123 — vazio se S/N)",               "Endereço"),
    ("-COMPLEMENTO-",       "Complemento do endereço",                           "Endereço"),
    ("-BAIRRO-",            "BAIRRO + nome  (ex: BAIRRO Centro)",                "Endereço"),
    ("-CEP-",               "CEP: 00000-000  (ou vazio se não cadastrado)",      "Endereço"),
    ("-CIDADE-",            "Cidade",                                             "Endereço"),
    ("-UF-",                "Estado — sigla  (ex: SC)",                          "Endereço"),
    ("-NOME DO TÉCNICO-",   "Nome do técnico selecionado ao gerar o documento",  "Técnico"),
    ("-NUMERO CFT-",        "Número CFT do técnico",                             "Técnico"),
    ("-MÊS-",               "Mês atual em maiúsculas  (ex: MAIO)",               "Data"),
    ("-MES-",               "Igual a -MÊS-  (variante sem acento)",              "Data"),
    ("-ANO-",               "Ano atual  (ex: 2025)",                              "Data"),
]

_CAT_STYLE = {
    "Cliente":  ("#4ADE80",  "rgba(74,222,128,.07)"),
    "Endereço": ("#60A5FA",  "rgba(96,165,250,.07)"),
    "Técnico":  ("#FBBF24",  "rgba(251,191,36,.07)"),
    "Data":     ("#C4B5FD",  "rgba(196,181,253,.07)"),
}


def modelos_dialog() -> None:
    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(820px,97vw)!important;max-height:94vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        # ── Cabeçalho ────────────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#60A5FA">folder_special</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Modelos de Documento</div>')
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    'Gerencie os modelos .docx — campos com realce amarelo são preenchidos automaticamente</div>'
                )

        # ── Corpo ─────────────────────────────────────────────────────────────
        with ui.element("div").style("padding:20px 24px;overflow-y:auto;flex:1;min-height:0"):

            def _sec(text: str, border_top: bool = False) -> None:
                bt = "border-top:1px solid var(--dmc-b1);padding-top:14px;" if border_top else ""
                ui.html(
                    f'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                    f'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px;{bt}">'
                    f'{text}</div>'
                )

            # ── Modelos disponíveis ───────────────────────────────────────────
            _sec("Modelos Disponíveis")
            list_area = ui.element("div")

            def _render_list():
                list_area.clear()
                with list_area:
                    files = sorted(MODELOS_DIR.glob("*.docx"))
                    if not files:
                        ui.html(
                            '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);'
                            'padding:16px;background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                            'border-radius:10px;text-align:center;margin-bottom:14px">'
                            'Nenhum modelo encontrado — faça o upload do primeiro modelo abaixo.</div>'
                        )
                        return
                    for f in files:
                        sz = f.stat().st_size
                        sz_str = f"{sz/1024:.1f} KB" if sz >= 1024 else f"{sz} B"
                        with ui.element("div").style(
                            "display:flex;align-items:center;gap:12px;"
                            "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);"
                            "border-radius:10px;padding:11px 14px;margin-bottom:8px;"
                        ):
                            ui.html(
                                '<span class="material-icons" '
                                'style="font-size:22px;color:var(--dmc-amber);flex-shrink:0">description</span>'
                            )
                            ui.html(
                                f'<span style="font:500 13px var(--dmc-fm);color:var(--dmc-text);flex:1">'
                                f'{f.stem.upper()}</span>'
                                f'<span style="font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                                f'margin-right:4px">{f.name}</span>'
                            )
                            ui.html(
                                f'<span style="font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                                f'flex-shrink:0;margin-right:8px">{sz_str}</span>'
                            )
                            del_btn = ui.element("button").style(
                                "background:none;border:none;cursor:pointer;padding:4px 6px;"
                                "color:var(--dmc-muted2);display:flex;align-items:center;flex-shrink:0;"
                                "border-radius:6px;transition:color .15s;"
                            )
                            with del_btn:
                                ui.html('<span class="material-icons" style="font-size:17px">delete_outline</span>')

                            def _del(path=f):
                                try:
                                    path.unlink()
                                    ui.notify(f"{path.name} removido.", type="positive")
                                    _render_list()
                                except Exception as ex:
                                    ui.notify(f"Erro: {ex}", type="negative")

                            del_btn.on("click", _del)

            _render_list()

            # ── Upload ────────────────────────────────────────────────────────
            _sec("Adicionar Novo Modelo", border_top=True)

            ui.html('<input type="file" id="mdl-file-input" accept=".docx" style="display:none">')

            with ui.element("div").style("display:flex;align-items:center;gap:14px;margin-bottom:6px"):
                with ui.element("button").style(
                    "display:flex;align-items:center;gap:9px;"
                    "background:rgba(96,165,250,.08);border:1.5px dashed rgba(96,165,250,.35);"
                    "border-radius:10px;padding:12px 22px;cursor:pointer;"
                    "font:500 13px var(--dmc-fm);color:#60A5FA;transition:all .15s;"
                ).props('id="mdl-upload-lbl"'):
                    ui.html(
                        '<span class="material-icons" style="font-size:18px">cloud_upload</span>'
                        '<span>Selecionar arquivo .docx</span>'
                    )

                upload_status = ui.element("div")

            ui.html(
                '<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:16px">'
                'Somente arquivos <b>.docx</b> são aceitos. '
                'O arquivo é salvo em <code>modelos/</code> e aparece na lista acima automaticamente.</div>'
            )

            def _on_uploaded(_e):
                _render_list()
                upload_status.clear()
                with upload_status:
                    ui.html(
                        '<div style="font:12px var(--dmc-fm);color:var(--dmc-green);padding:3px 0">'
                        '✓ Modelo adicionado!</div>'
                    )

            ui.on("mdl_uploaded", _on_uploaded)

            # ── Marcadores disponíveis ────────────────────────────────────────
            _sec("Marcadores Disponíveis", border_top=True)
            ui.html(
                '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:14px">'
                'No Word, escreva o marcador <b>exatamente</b> como mostrado e aplique '
                '<b style="background:#FBBF24;color:#111;padding:1px 6px;border-radius:3px">'
                'realce amarelo</b> no texto — ele será substituído automaticamente ao gerar.</div>'
            )

            cats: dict = {}
            for marker, desc, cat in _MARCADORES:
                cats.setdefault(cat, []).append((marker, desc))

            for cat, items in cats.items():
                color, bg = _CAT_STYLE.get(cat, ("#94A3B8", "rgba(148,163,184,.07)"))
                ui.html(
                    f'<div style="font:9px var(--dmc-mono);color:{color};letter-spacing:.15em;'
                    f'text-transform:uppercase;margin:10px 0 6px">{cat}</div>'
                )
                with ui.element("div").style(
                    f"background:{bg};border:1px solid rgba(255,255,255,.06);"
                    f"border-radius:10px;overflow:hidden;margin-bottom:4px;"
                ):
                    for i, (marker, desc) in enumerate(items):
                        sep = "border-top:1px solid rgba(255,255,255,.04);" if i > 0 else ""
                        ui.html(
                            f'<div style="display:flex;align-items:center;gap:14px;padding:9px 14px;{sep}">'
                            f'<code style="font:600 12px var(--dmc-mono);color:{color};'
                            f'background:rgba(255,255,255,.06);padding:2px 9px;'
                            f'border-radius:5px;flex-shrink:0;white-space:nowrap">{marker}</code>'
                            f'<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">{desc}</span>'
                            f'</div>'
                        )

        # ── Rodapé ────────────────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;flex-shrink:0;"
        ):
            ui.button("Fechar", on_click=dlg.close).props("flat no-caps").classes("dmc-btn dmc-btn-ghost")

        # JS: conecta o botão ao input oculto e faz o XHR para /upload-modelo
        ui.timer(0.05, lambda: ui.run_javascript(r"""
            (function(){
                var lbl = document.getElementById('mdl-upload-lbl');
                var inp = document.getElementById('mdl-file-input');
                if (!lbl || !inp) return;
                lbl.addEventListener('click', function(){ inp.click(); });
                inp.addEventListener('change', function(){
                    var f = inp.files[0];
                    if (!f) return;
                    if (!f.name.toLowerCase().endsWith('.docx')) {
                        alert('Somente arquivos .docx são aceitos.');
                        inp.value = '';
                        return;
                    }
                    var fd = new FormData();
                    fd.append('file', f);
                    var xhr = new XMLHttpRequest();
                    xhr.addEventListener('loadend', function(){
                        inp.value = '';
                        emitEvent('mdl_uploaded', {name: f.name});
                    });
                    xhr.open('POST', '/upload-modelo');
                    xhr.send(fd);
                });
            })();
        """), once=True)

    dlg.open()
