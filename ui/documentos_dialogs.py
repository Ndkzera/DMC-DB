"""Dialog de geração de documentos a partir de modelos .docx."""

from nicegui import ui

from services.documentos import gerar_documento_bytes, listar_modelos
from services.tecnicos import load_tecnicos


def gerar_documento_dialog(cliente: dict) -> None:
    modelos = listar_modelos()
    tecnicos = load_tecnicos()

    sel = {
        "modelo": modelos[0] if len(modelos) == 1 else None,
        "tecnico": tecnicos[0] if len(tecnicos) == 1 else None,
    }

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(680px,97vw)!important;max-height:90vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        ui.button(icon="close", on_click=dlg.close).props("flat round dense").style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        # ── Cabeçalho ─────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#60A5FA">description</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Gerar Documento</div>')
                ui.html(
                    f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    f'{cliente.get("nome", "")}</div>'
                )

        # ── Corpo ──────────────────────────────────────────────────────
        with ui.element("div").style("padding:22px 24px 8px;overflow-y:auto;flex:1;min-height:0"):

            def _section_label(text: str) -> None:
                ui.html(
                    f'<div style="font:9px var(--dmc-mono);color:var(--dmc-muted2);'
                    f'letter-spacing:.18em;text-transform:uppercase;margin-bottom:10px">{text}</div>'
                )

            # ── Seletor de modelo ──────────────────────────────────────
            _section_label("Documento")
            modelo_box = ui.element("div")

            ui.element("div").style("height:18px")
            _section_label("Técnico Responsável")
            tecnico_box = ui.element("div")

            ui.element("div").style("height:12px")

        # ── Rodapé ─────────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props("flat no-caps").classes("dmc-btn dmc-btn-ghost")

            async def _gerar():
                if not sel["modelo"]:
                    ui.notify("Selecione um documento.", type="warning")
                    return
                if not sel["tecnico"]:
                    ui.notify("Selecione um técnico.", type="warning")
                    return
                try:
                    content = gerar_documento_bytes(sel["modelo"]["path"], cliente, sel["tecnico"])
                    nome_safe = cliente.get("nome", "cliente").replace(" ", "_")
                    ui.download(content, f"Memorial_{nome_safe}.docx")
                    ui.notify("Documento gerado!", type="positive")
                    dlg.close()
                except Exception as e:
                    ui.notify(f"Erro ao gerar documento: {e}", type="negative")

            ui.button("Gerar Documento", icon="download", on_click=_gerar).props(
                "unelevated no-caps"
            ).classes("dmc-btn dmc-btn-primary").style("padding:0 20px")

    # ── Renderização dos cards ─────────────────────────────────────────

    def _render_modelos():
        modelo_box.clear()
        with modelo_box:
            if not modelos:
                ui.html(
                    '<div style="font:13px var(--dmc-fm);color:var(--dmc-muted2);'
                    'padding:12px 0">Nenhum modelo encontrado na pasta <code>modelos/</code>.</div>'
                )
                return
            for m in modelos:
                active = sel["modelo"] and sel["modelo"]["path"] == m["path"]
                border = "1.5px solid var(--dmc-green)" if active else "1px solid var(--dmc-b1)"
                bg = "rgba(74,222,128,.05)" if active else "var(--dmc-bg3)"
                card = ui.element("div").style(
                    f"background:{bg};border:{border};border-radius:12px;"
                    "padding:13px 16px;margin-bottom:8px;cursor:pointer;"
                    "display:flex;align-items:center;gap:12px;transition:border .15s;"
                )
                with card:
                    ui.html(
                        '<span class="material-icons" '
                        'style="font-size:22px;color:var(--dmc-amber);flex-shrink:0">description</span>'
                    )
                    ui.html(
                        f'<span style="font:500 13px var(--dmc-fm);color:var(--dmc-text)">{m["nome"]}</span>'
                    )
                    if active:
                        ui.html(
                            '<span class="material-icons" '
                            'style="color:var(--dmc-green);margin-left:auto;font-size:20px">check_circle</span>'
                        )
                card.on("click", lambda mm=m: [sel.update({"modelo": mm}), _render_modelos()])

    def _render_tecnicos():
        tecnico_box.clear()
        with tecnico_box:
            if not tecnicos:
                ui.html(
                    '<div style="font:13px var(--dmc-fm);color:var(--dmc-muted2);padding:12px 0">'
                    'Nenhum técnico cadastrado. Cadastre em <b>Administrativo → Técnicos Cadastrados</b>.</div>'
                )
                return
            for t in tecnicos:
                active = sel["tecnico"] and sel["tecnico"].get("cpf") == t.get("cpf")
                border = "1.5px solid var(--dmc-green)" if active else "1px solid var(--dmc-b1)"
                bg = "rgba(74,222,128,.05)" if active else "var(--dmc-bg3)"
                initials = "".join(p[0] for p in t.get("nome", "?").split()[:2]).upper()
                card = ui.element("div").style(
                    f"background:{bg};border:{border};border-radius:12px;"
                    "padding:13px 16px;margin-bottom:8px;cursor:pointer;"
                    "display:flex;align-items:center;gap:12px;transition:border .15s;"
                )
                with card:
                    ui.html(
                        f'<div style="width:38px;height:38px;border-radius:9px;flex-shrink:0;'
                        f'background:rgba(251,191,36,.10);border:1px solid rgba(251,191,36,.25);'
                        f'display:flex;align-items:center;justify-content:center;'
                        f'font:700 13px var(--dmc-fd);color:#FBBF24">{initials}</div>'
                    )
                    with ui.element("div").style("min-width:0"):
                        ui.html(
                            f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text)">'
                            f'{t.get("nome","")}</div>'
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
                        if tags:
                            ui.html(
                                '<div style="display:flex;gap:7px;align-items:center;margin-top:3px">'
                                + " ".join(tags) + "</div>"
                            )
                    if active:
                        ui.html(
                            '<span class="material-icons" '
                            'style="color:var(--dmc-green);margin-left:auto;font-size:20px">check_circle</span>'
                        )
                card.on("click", lambda tt=t: [sel.update({"tecnico": tt}), _render_tecnicos()])

    _render_modelos()
    _render_tecnicos()
    dlg.open()
