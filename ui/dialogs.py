"""Todos os diálogos modais da aplicação."""

import urllib.parse
from datetime import datetime

from nicegui import app as _app, ui

from config import BASE_URL
from ui.documentos_dialogs import gerar_documento_dialog
from services.clientes import (
    add_cliente,
    delete_cliente,
    update_cliente,
    fmt_cpf,
    fmt_tel,
    load_clientes,
)
from services.files import delete_item, file_url, list_dir, safe, san
from services.auth import check_login, current_user_label, current_user_name, current_user_perfil
from services.log import log_action


# ── Pasta ────────────────────────────────────────────────────────────

def create_folder_dialog(state) -> None:
    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:16px!important;padding:0;min-width:380px;color:var(--dmc-text)!important"
    ):
        with ui.element("div").style(
            "padding:16px 20px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:10px;"
        ):
            ui.html('<span class="material-icons" style="font-size:18px;color:var(--dmc-green)">create_new_folder</span>')
            ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Nova Pasta</div>')

        with ui.element("div").style("padding:20px"):
            ui.html('<label class="dmc-label" for="dlg-folder-name">Nome da pasta</label>')
            ui.html(
                '<input class="dmc-input" id="dlg-folder-name" placeholder="Ex: Projetos 2025" '
                'style="width:100%;margin-bottom:4px" autofocus>'
            )

            async def _create():
                name = san(await ui.run_javascript(
                    "(document.getElementById('dlg-folder-name')?.value||'').trim()"
                ))
                if not name:
                    ui.notify("Nome inválido.", type="warning")
                    return
                new = state.path / name
                if not safe(new):
                    ui.notify("Caminho não permitido.", type="negative")
                    return
                if new.exists():
                    ui.notify("Já existe.", type="warning")
                    return
                try:
                    new.mkdir()
                    log_action(current_user_label(), current_user_perfil(),
                               "pasta", "pasta", name, str(state.path))
                    ui.notify(f"✓ Pasta '{name}' criada!", type="positive")
                    dlg.close()
                    state.render()
                except OSError as ex:
                    ui.notify(f"Erro: {ex}", type="negative")

            ui.add_body_html("""<script>
            (function(){
              var inp = document.getElementById('dlg-folder-name');
              if(inp) inp.addEventListener('keydown', function(e){
                if(e.key==='Enter') document.getElementById('trig-create-folder')?.click();
              });
            })();
            </script>""")

        with ui.element("div").style(
            "padding:12px 20px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:8px;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')
            ui.button("Criar", on_click=_create).props(
                'unelevated no-caps id="trig-create-folder"'
            ).classes('dmc-btn dmc-btn-primary')
    dlg.open()


# ── Excluir ──────────────────────────────────────────────────────────

def delete_selected_dialog(state) -> None:
    folders_all, files_all = list_dir(state.path, "")
    all_items = (
        [{"name": f["name"], "path": f["path"], "type": "folder"} for f in folders_all]
        + [{"name": f["name"], "path": f["path"], "type": "file"} for f in files_all]
    )
    if not all_items:
        ui.notify("Pasta vazia — nada para deletar.", type="warning")
        return

    _ROW = (
        "display:flex;align-items:center;gap:10px;padding:9px 12px;"
        "border:1px solid var(--dmc-b1);border-radius:10px;margin-bottom:4px;"
        "cursor:pointer;transition:background .12s,border-color .12s;"
    )
    _ROW_SEL = (
        "display:flex;align-items:center;gap:10px;padding:9px 12px;"
        "border:1px solid rgba(248,113,113,.35);border-radius:10px;margin-bottom:4px;"
        "cursor:pointer;transition:background .12s,border-color .12s;"
        "background:rgba(248,113,113,.06);"
    )
    _CHK_OFF = (
        "width:17px;height:17px;border-radius:4px;flex-shrink:0;"
        "border:1.5px solid var(--dmc-b2);background:transparent;"
        "display:flex;align-items:center;justify-content:center;transition:all .12s;"
    )
    _CHK_ON = (
        "width:17px;height:17px;border-radius:4px;flex-shrink:0;"
        "border:1.5px solid rgba(248,113,113,.8);background:rgba(248,113,113,.85);"
        "display:flex;align-items:center;justify-content:center;transition:all .12s;"
    )
    _MARK_OFF = '<span class="material-icons" style="font-size:11px;color:white;opacity:0;line-height:1">check</span>'
    _MARK_ON  = '<span class="material-icons" style="font-size:11px;color:white;opacity:1;line-height:1">check</span>'

    selected  = [False] * len(all_items)
    chk_refs  = []   # (chk_div, chk_mark_html, row_div)

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid #7F1D1D!important;"
        "border-radius:16px!important;padding:0;"
        "width:min(480px,96vw);max-height:80vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;"
    ):
        # ── Cabeçalho ────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:16px 20px;border-bottom:1px solid rgba(127,29,29,.4);"
            "display:flex;align-items:center;gap:10px;flex-shrink:0;"
        ):
            ui.html('<span class="material-icons" style="font-size:18px;color:#F87171">delete</span>')
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:#F87171">Deletar itens</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted)">Itens movidos para "Arquivos deletados"</div>')

        # ── Barra de controle ─────────────────────────────────────────
        with ui.element("div").style(
            "padding:10px 20px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;justify-content:space-between;flex-shrink:0;"
        ):
            ui.html(
                f'<span style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                f'text-transform:uppercase;letter-spacing:.1em">{len(all_items)} itens</span>'
            )
            with ui.element("div").style("display:flex;gap:6px"):
                sel_all   = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                desel_all = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                with sel_all:   ui.html("<span>Selecionar todos</span>")
                with desel_all: ui.html("<span>Desmarcar todos</span>")

        # ── Lista rolável ─────────────────────────────────────────────
        with ui.element("div").style("overflow-y:auto;flex:1;min-height:0;padding:8px 12px"):
            for i, item in enumerate(all_items):
                icon  = "folder" if item["type"] == "folder" else "insert_drive_file"
                color = "var(--dmc-amber)" if item["type"] == "folder" else "var(--dmc-muted)"
                row = ui.element("div").style(_ROW)
                with row:
                    chk = ui.element("div").style(_CHK_OFF)
                    with chk:
                        mark = ui.html(_MARK_OFF)
                    ui.html(f'<span class="material-icons" style="font-size:18px;color:{color}">{icon}</span>')
                    ui.html(
                        f'<span style="font:13px var(--dmc-fm);color:var(--dmc-text);'
                        f'flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                        f'{item["name"]}</span>'
                    )
                chk_refs.append((chk, mark, row))

                def _toggle(idx=i):
                    selected[idx] = not selected[idx]
                    c, m, r = chk_refs[idx]
                    c.style(_CHK_ON  if selected[idx] else _CHK_OFF)
                    m.set_content(_MARK_ON if selected[idx] else _MARK_OFF)
                    r.style(_ROW_SEL if selected[idx] else _ROW)

                row.on("click", _toggle)

        def _set_all(v: bool):
            for idx in range(len(all_items)):
                selected[idx] = v
                c, m, r = chk_refs[idx]
                c.style(_CHK_ON  if v else _CHK_OFF)
                m.set_content(_MARK_ON if v else _MARK_OFF)
                r.style(_ROW_SEL if v else _ROW)

        sel_all.on("click",   lambda: _set_all(True))
        desel_all.on("click", lambda: _set_all(False))

        def do_delete():
            to_del = [all_items[i] for i, v in enumerate(selected) if v]
            if not to_del:
                ui.notify("Selecione ao menos um item.", type="warning")
                return
            ok = [item["name"] for item in to_del if delete_item(item["path"], deleted_by=current_user_label(), perfil=current_user_perfil())]
            if ok:
                nomes = ", ".join(ok[:3]) + (f" e mais {len(ok) - 3}" if len(ok) > 3 else "")
                ui.notify(f"🗑 {len(ok)} item(s) movido(s): {nomes}", type="positive")
            dlg.close()
            state.render()

        # ── Rodapé ────────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:12px 20px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:8px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')
            ui.button("Deletar selecionados", on_click=do_delete).props('unelevated no-caps').classes('dmc-btn dmc-btn-danger')
    dlg.open()


# ── Compartilhar ──────────────────────────────────────────────────────

def share_selected_dialog(state) -> None:
    _, files_all = list_dir(state.path, "")
    if not files_all:
        ui.notify("Nenhum arquivo nesta pasta para compartilhar.", type="warning")
        return

    items  = [{"name": f["name"], "path": f["path"], "type": "file"} for f in files_all]
    checks = []

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:16px!important;padding:0;width:min(680px,96vw)!important;max-height:85vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;"
    ):
        with ui.element("div").style(
            "padding:16px 20px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:10px;flex-shrink:0;"
        ):
            ui.html('<span class="material-icons" style="font-size:18px;color:var(--dmc-green)">share</span>')
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Compartilhar arquivos</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted)">Selecione e clique em Gerar links</div>')

        with ui.element("div").style("padding:12px 20px;overflow-y:auto;flex:1"):
            for item in items:
                with ui.element("div").style(
                    "display:flex;align-items:center;gap:10px;padding:8px 10px;"
                    "border:1px solid var(--dmc-b1);border-radius:8px;margin-bottom:4px;"
                ):
                    cb = ui.checkbox("").style("flex-shrink:0")
                    ui.html('<span class="material-icons" style="font-size:16px;color:var(--dmc-muted)">insert_drive_file</span>')
                    ui.html(
                        f'<span style="font:13px var(--dmc-fm);color:var(--dmc-text);'
                        f'flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                        f'{item["name"]}</span>'
                    )
                    checks.append((cb, item))

        result_area = ui.element("div").style("padding:0 20px")

        def do_share():
            sel = [item for cb, item in checks if cb.value]
            if not sel:
                ui.notify("Selecione ao menos um arquivo.", type="warning")
                return

            result_area.clear()
            with result_area:
                ui.element("div").style("height:1px;background:var(--dmc-b1);margin:4px 0 10px")
                for item in sel:
                    url          = file_url(item["path"])
                    link         = f"{BASE_URL}{url}"
                    link_decoded = urllib.parse.unquote(link)
                    msg_raw = (
                        f"📁 *DMC Topografia*\n"
                        f"━━━━━━━━━━━━━━━━━━\n"
                        f"📄 *{item['name']}*\n\n"
                        f"🔗 Link para download:\n{link_decoded}\n\n"
                        f"_Enviado pelo sistema DMC Drive_"
                    )
                    wa_url = f"https://wa.me/?text={urllib.parse.quote(msg_raw)}"
                    cid    = f"cp{abs(hash(item['name']))}"

                    with ui.element("div").style(
                        "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);border-radius:10px;"
                        "padding:10px 12px;margin-bottom:8px;"
                        "display:flex;align-items:center;gap:8px;"
                    ):
                        ui.html('<span class="material-icons" style="font-size:16px;color:var(--dmc-muted2);flex-shrink:0">insert_drive_file</span>')
                        ui.label(item["name"]).style(
                            "flex:1;font:500 13px var(--dmc-fm);color:var(--dmc-text);"
                            "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                        )

                        cp_btn = (
                            ui.element("button")
                            .classes("dmc-btn-icon")
                            .props(f'id="{cid}" title="Copiar link"')
                        )
                        with cp_btn:
                            ui.html('<span class="material-icons" style="font-size:14px">content_copy</span>')
                        cp_btn.on("click", lambda lnk=link, c=cid: ui.run_javascript(
                            "navigator.clipboard.writeText(" + repr(lnk) + ")"
                            ".then(function(){"
                            "  var b=document.getElementById('" + c + "');"
                            "  if(b){b.style.color='#4ADE80';b.style.borderColor='#4ADE80';"
                            "  b.innerHTML='<span class=\\'material-icons\\' style=\\'font-size:14px\\'>check</span>';}"
                            "  setTimeout(function(){"
                            "    if(b){b.style.color='';b.style.borderColor='';"
                            "    b.innerHTML='<span class=\\'material-icons\\' style=\\'font-size:14px\\'>content_copy</span>';}"
                            "  },2000);"
                            "}).catch(function(){"
                            "  var t=document.createElement('textarea');"
                            "  t.value=" + repr(lnk) + ";document.body.appendChild(t);"
                            "  t.select();document.execCommand('copy');document.body.removeChild(t);"
                            "});"
                        ))

                        wa_btn = ui.element("button").style(
                            "display:inline-flex;align-items:center;justify-content:center;"
                            "width:32px;height:32px;border-radius:6px;"
                            "background:rgba(37,211,102,.12);border:1px solid rgba(37,211,102,.3);"
                            "color:#25D366;cursor:pointer;flex-shrink:0;transition:all .2s;"
                        ).props('title="Enviar via WhatsApp"')
                        with wa_btn:
                            ui.html('<span class="material-icons" style="font-size:16px">send</span>')
                        wa_btn.on("click", lambda wu=wa_url: ui.run_javascript(
                            "window.open(" + repr(wu) + ",'_blank','noopener,noreferrer');"
                        ))

        with ui.element("div").style(
            "padding:12px 20px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:8px;flex-shrink:0;"
        ):
            ui.button("Fechar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')
            ui.button("Gerar links", on_click=do_share).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary')
    dlg.open()


# ── Clientes: busca e ficha ───────────────────────────────────────────

def ver_ficha_dialog(c: dict) -> None:
    tipo_cor = "#14532D" if c["tipo"] == "PF" else "#1E3A5F"
    tipo_txt = "Pessoa Física" if c["tipo"] == "PF" else "Pessoa Jurídica"

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:16px!important;padding:0;width:min(680px,96vw)!important;"
        "max-height:85vh;overflow-y:auto;color:var(--dmc-text)!important;"
    ):
        with ui.element("div").style(
            f"background:{tipo_cor};padding:18px 24px;"
            "display:flex;align-items:center;gap:12px;"
        ):
            tipo_icon = "person" if c["tipo"] == "PF" else "business"
            ui.html(f'<span class="material-icons" style="font-size:28px;color:var(--dmc-green)">{tipo_icon}</span>')
            with ui.element("div"):
                ui.html(f'<div style="font:700 16px var(--dmc-fd);color:#fff">{c.get("nome", "")}</div>')
                ui.html(f'<div style="font:400 12px var(--dmc-fm);color:rgba(255,255,255,.65)">{tipo_txt}</div>')

        with ui.element("div").style("padding:20px 24px"):
            def row(label: str, value: str, color: str = "var(--dmc-text)"):
                if not value:
                    return
                with ui.element("div").style(
                    "display:flex;gap:8px;padding:8px 0;border-bottom:1px solid var(--dmc-b1);"
                ):
                    ui.html(
                        f'<span style="font:500 11px var(--dmc-mono);color:var(--dmc-muted2);'
                        f'width:110px;flex-shrink:0;padding-top:1px;text-transform:uppercase;'
                        f'letter-spacing:.06em">{label}</span>'
                    )
                    ui.html(f'<span style="font:13px var(--dmc-fm);color:{color};word-break:break-all">{value}</span>')

            doc_lbl = "CPF" if c["tipo"] == "PF" else "CNPJ"
            row("Nome", c.get("nome", ""))
            row(doc_lbl, c.get("cpf", ""), "var(--dmc-green)")
            row("Telefone", c.get("telefone", ""), "var(--dmc-amber)")
            row("Cadastrado", c.get("data", ""))

            def _end_section(titulo: str, prefix: str):
                if titulo:
                    ui.html(
                        f'<div style="font:600 11px var(--dmc-mono);color:var(--dmc-muted2);'
                        f'text-transform:uppercase;letter-spacing:.1em;margin:16px 0 8px">{titulo}</div>'
                    )
                log = f"{c.get(f'{prefix}_log', '')} {c.get(f'{prefix}_num', '')}"
                if c.get(f"{prefix}_comp"):
                    log += f", {c[f'{prefix}_comp']}"
                log += f"\n{c.get(f'{prefix}_bairro', '')} — {c.get(f'{prefix}_cidade', '')} / {c.get(f'{prefix}_estado', '')}"
                row("Logradouro", log)
                maps_url = c.get(f"{prefix}_maps", "")
                if maps_url:
                    with ui.element("div").style(
                        "display:flex;gap:8px;padding:8px 0;border-bottom:1px solid var(--dmc-b1)"
                    ):
                        ui.html(
                            '<span style="font:500 11px var(--dmc-mono);color:var(--dmc-muted2);width:110px;'
                            'flex-shrink:0;text-transform:uppercase;letter-spacing:.06em">Maps</span>'
                        )
                        maps_a = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                        with maps_a:
                            ui.html('<span class="material-icons">map</span>')
                            ui.html("<span>Abrir localização</span>")
                        maps_a.on("click", lambda u=maps_url: ui.run_javascript(
                            f"window.open({repr(u)},'_blank','noopener,noreferrer');"
                        ))

            _end_section("Endereço Pessoal / Comercial", "end")
            ui.html(
                '<div style="font:600 11px var(--dmc-mono);color:var(--dmc-muted2);'
                'text-transform:uppercase;letter-spacing:.1em;margin:16px 0 8px">Endereço da Obra</div>'
            )
            if c.get("obra_mesmo"):
                ui.html('<div style="font:13px var(--dmc-fm);color:var(--dmc-muted2)">Mesmo endereço acima</div>')
            else:
                _end_section("", "obra")

        with ui.element("div").style(
            "padding:12px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:space-between;align-items:center;"
        ):
            ui.button("Fechar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')
            with ui.element("div").style("display:flex;gap:8px"):
                # Excluir — apenas DESENVOLVEDOR e ADMINISTRADOR
                if current_user_perfil() in ("DESENVOLVEDOR", "ADMINISTRADOR"):
                    def _pedir_senha_delete():
                        with ui.dialog().props("persistent") as pw_dlg:
                            pw_dlg.open()
                            with ui.card().style(
                                "width:360px;max-width:94vw;padding:0;"
                                "background:var(--dmc-bg2)!important;"
                                "border:1px solid rgba(248,113,113,.35)!important;"
                                "border-radius:12px!important;"
                            ):
                                with ui.element("div").style(
                                    "padding:16px 20px;border-bottom:1px solid var(--dmc-b1);"
                                ):
                                    ui.html(
                                        f'<div style="font:600 13px var(--dmc-fd);color:var(--dmc-text)">'
                                        f'Excluir &ldquo;{c.get("nome", "")}&rdquo;?</div>'
                                        '<div style="font:11px var(--dmc-fm);color:#F87171;margin-top:4px">'
                                        'Esta ação é irreversível.</div>'
                                    )
                                with ui.element("div").style(
                                    "padding:16px 20px;display:flex;flex-direction:column;gap:10px"
                                ):
                                    pw = (
                                        ui.input("Senha", password=True, password_toggle_button=True)
                                        .props('outlined dense color="red"')
                                        .style("font-family:var(--dmc-fm);font-size:12px")
                                    )
                                    err_lbl = ui.html("").style(
                                        "font:11px var(--dmc-fm);color:#F87171;min-height:14px"
                                    )
                                    with ui.element("div").style(
                                        "display:flex;gap:8px;justify-content:flex-end"
                                    ):
                                        cx = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                                        with cx:
                                            ui.html("<span>Cancelar</span>")
                                        cx.on("click", pw_dlg.close)

                                        cf = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
                                        with cf:
                                            ui.html(
                                                '<span class="material-icons" style="font-size:15px">delete_forever</span>'
                                                "<span>Excluir</span>"
                                            )

                                        def _confirmar(pw_dlg=pw_dlg, pw=pw, err_lbl=err_lbl):
                                            email = _app.storage.user.get("dmc_user_email", "")
                                            if not check_login(email, pw.value):
                                                err_lbl.set_content(
                                                    '<span style="color:#F87171">Senha incorreta.</span>'
                                                )
                                                return
                                            pw_dlg.close()
                                            dlg.close()
                                            delete_cliente(c.get("cpf", ""), c.get("nome", ""),
                                                           usuario=current_user_label(), perfil=current_user_perfil())
                                            ui.notify(f"Cliente '{c.get('nome', '')}' excluído.", type="positive")

                                        cf.on("click", _confirmar)
                                        pw.on("keydown.enter", _confirmar)

                    del_btn = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
                    with del_btn:
                        ui.html('<span class="material-icons" style="font-size:15px">delete_forever</span>')
                        ui.html("<span>Excluir</span>")
                    del_btn.on("click", _pedir_senha_delete)

                ui.button("Gerar Documento", icon="description", on_click=lambda: gerar_documento_dialog(c)).props(
                    'unelevated no-caps'
                ).classes('dmc-btn dmc-btn-secondary').style("padding:0 16px")
                ui.button("Editar", icon="edit", on_click=lambda: [dlg.close(), editar_cliente_dialog(c)]).props(
                    'unelevated no-caps'
                ).classes('dmc-btn dmc-btn-primary').style("padding:0 18px")

    dlg.open()


# ── Editar cliente ────────────────────────────────────────────────────

def editar_cliente_dialog(c: dict) -> None:
    import json as _json

    original_cpf = c.get("cpf", "")

    _FORM_IDS = [
        "f-nome", "f-doc", "f-tel",
        "f-cep-end", "f-log-end", "f-num-end", "f-comp-end",
        "f-bairro-end", "f-cidade-end", "f-uf-end", "f-maps-end",
        "f-cep-obra", "f-log-obra", "f-num-obra", "f-comp-obra",
        "f-bairro-obra", "f-cidade-obra", "f-uf-obra", "f-maps-obra",
    ]

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(1100px,98vw)!important;max-width:98vw!important;max-height:92vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        # ── Botão fechar ──────────────────────────────────────────────
        ui.button(icon="close", on_click=dlg.close).props('flat round dense').style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        # ── Cabeçalho ─────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(96,165,250,.1);border:1px solid rgba(96,165,250,.3);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#60A5FA">edit</span></div>'
            )
            with ui.element("div"):
                ui.html(f'<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Editar Cliente</div>')
                ui.html(f'<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">{c.get("nome","")}</div>')

        # ── Corpo (scrollável) ─────────────────────────────────────────
        with ui.element("div").style("padding:22px 24px 8px;overflow-y:auto;flex:1"):

            ui.html("""
            <div style="margin-bottom:22px">
              <div class="dmc-label" style="margin-bottom:10px">Tipo de Cliente</div>
              <div style="display:flex;gap:10px;max-width:360px">
                <button class="dmc-tipo-btn" data-tipo="PF">
                  <span class="material-icons" style="font-size:16px">person</span>
                  <span>Pessoa Física</span>
                </button>
                <button class="dmc-tipo-btn" data-tipo="PJ">
                  <span class="material-icons" style="font-size:16px">business</span>
                  <span>Pessoa Jurídica</span>
                </button>
              </div>
            </div>
            """)

            ui.html("""
            <div class="dmc-card">
              <div class="dmc-card-hdr">
                <span class="material-icons">person</span> Dados do Cliente
              </div>
              <div class="dmc-card-body">
                <div style="margin-bottom:12px">
                  <label class="dmc-label" id="nome-label" for="f-nome">Nome Completo</label>
                  <input class="dmc-input" id="f-nome" placeholder="NOME COMPLETO"
                    oninput="this.value=this.value.toUpperCase()">
                </div>
                <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:flex-end">
                  <div style="min-width:0">
                    <label class="dmc-label" id="doc-label">CPF</label>
                    <input class="dmc-input" id="f-doc" placeholder="000.000.000-00"
                      inputmode="numeric">
                  </div>
                  <button type="button" class="dmc-btn" id="btn-consultar">
                    <span class="material-icons">manage_search</span> Consultar
                  </button>
                  <div style="min-width:0">
                    <label class="dmc-label">Telefone</label>
                    <input class="dmc-input" id="f-tel" placeholder="(00) 00000-0000">
                  </div>
                </div>
                <div id="doc-status" class="dmc-status" style="color:transparent">_</div>
              </div>
            </div>
            """)

            with ui.element("div").classes("dmc-cols-2"):
                with ui.element("div").classes("dmc-card").style("margin-bottom:0"):
                    ui.html(
                        '<div class="dmc-card-hdr">'
                        '<span class="material-icons">home</span>'
                        ' Endereço Pessoal / Comercial</div>'
                    )
                    with ui.element("div").classes("dmc-card-body"):
                        ui.html(_addr_block_html("end"))

                with ui.element("div").classes("dmc-card").style("margin-bottom:0"):
                    ui.html(
                        '<div class="dmc-card-hdr" style="justify-content:space-between">'
                        '<span style="display:flex;align-items:center;gap:8px">'
                        '<span class="material-icons">construction</span>'
                        ' Endereço da Obra'
                        '</span>'
                        '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;margin:0">'
                        '<input type="checkbox" id="obra-mesmo" onchange="toggleObra(this.checked)" '
                        'style="width:14px;height:14px;accent-color:var(--dmc-green);cursor:pointer;flex-shrink:0">'
                        '<span style="font:500 10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.08em;text-transform:uppercase;white-space:nowrap">'
                        'Mesmo endereço</span>'
                        '</label>'
                        '</div>'
                    )
                    with ui.element("div").classes("dmc-card-body"):
                        with ui.element("div").props('id="obra-fields-wrap"'):
                            ui.html(_addr_block_html("obra"))

            ui.element("div").style("height:12px")

        # ── Rodapé ────────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def salvar_edicao():
                vals = await ui.run_javascript("""({
                  tipo: window.dmcTipo||'PF',
                  nome: (document.getElementById('f-nome')?.value||'').trim().toUpperCase(),
                  doc:  (document.getElementById('f-doc')?.value||'').trim(),
                  tel:  (document.getElementById('f-tel')?.value||'').trim(),
                  obra_mesmo: document.getElementById('obra-mesmo')?.checked||false,
                  end_log:    (document.getElementById('f-log-end')?.value||'').trim().toUpperCase(),
                  end_num:    (document.getElementById('f-num-end')?.value||'').trim().toUpperCase(),
                  end_comp:   (document.getElementById('f-comp-end')?.value||'').trim().toUpperCase(),
                  end_bairro: (document.getElementById('f-bairro-end')?.value||'').trim().toUpperCase(),
                  end_cidade: (document.getElementById('f-cidade-end')?.value||'').trim().toUpperCase(),
                  end_uf:     (document.getElementById('f-uf-end')?.value||'').trim().toUpperCase(),
                  end_cep:    (document.getElementById('f-cep-end')?.value||'').trim(),
                  end_maps:   (document.getElementById('f-maps-end')?.value||'').trim(),
                  obra_log:    (document.getElementById('f-log-obra')?.value||'').trim().toUpperCase(),
                  obra_num:    (document.getElementById('f-num-obra')?.value||'').trim().toUpperCase(),
                  obra_comp:   (document.getElementById('f-comp-obra')?.value||'').trim().toUpperCase(),
                  obra_bairro: (document.getElementById('f-bairro-obra')?.value||'').trim().toUpperCase(),
                  obra_cidade: (document.getElementById('f-cidade-obra')?.value||'').trim().toUpperCase(),
                  obra_uf:     (document.getElementById('f-uf-obra')?.value||'').trim().toUpperCase(),
                  obra_cep:    (document.getElementById('f-cep-obra')?.value||'').trim(),
                  obra_maps:   (document.getElementById('f-maps-obra')?.value||'').trim(),
                })""")

                if not vals.get("nome") or not vals.get("doc") or not vals.get("tel"):
                    ui.notify("Preencha Nome, CPF/CNPJ e Telefone.", type="warning")
                    return

                tipo = vals.get("tipo", "PF")
                obra_mesmo = vals.get("obra_mesmo", False)
                doc_fmt = fmt_cpf(vals["doc"]) if tipo == "PF" else vals["doc"]

                updated = {
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
                    "end_cep":     vals["end_cep"],
                    "end_maps":    vals["end_maps"],
                    "obra_mesmo":  obra_mesmo,
                    "obra_log":    vals["end_log"]    if obra_mesmo else vals["obra_log"],
                    "obra_num":    vals["end_num"]    if obra_mesmo else vals["obra_num"],
                    "obra_comp":   vals["end_comp"]   if obra_mesmo else vals["obra_comp"],
                    "obra_bairro": vals["end_bairro"] if obra_mesmo else vals["obra_bairro"],
                    "obra_cidade": vals["end_cidade"] if obra_mesmo else vals["obra_cidade"],
                    "obra_estado": vals["end_uf"]     if obra_mesmo else vals["obra_uf"],
                    "obra_cep":    vals["end_cep"]    if obra_mesmo else vals["obra_cep"],
                    "obra_maps":   vals["end_maps"]   if obra_mesmo else vals["obra_maps"],
                    "data":        c.get("data", datetime.now().strftime("%d/%m/%Y %H:%M")),
                    "data_edicao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                update_cliente(original_cpf, updated,
                              usuario=current_user_label(), perfil=current_user_perfil())
                ui.notify(f"✓ Cliente '{vals['nome']}' atualizado!", type="positive")
                dlg.close()

            ui.button("Salvar Alterações", icon="save", on_click=salvar_edicao).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style("padding:0 22px")

    # ── Pré-preencher com dados existentes via JS ──────────────────────
    obra_mesmo_js = "true" if c.get("obra_mesmo") else "false"
    ui.run_javascript(f"""
    setTimeout(function(){{
      document.querySelectorAll('.dmc-tipo-btn').forEach(function(b){{
        b.onclick=function(){{setTipo(b.dataset.tipo);}};
      }});
      var oc=document.getElementById('obra-mesmo');
      if(oc){{
        oc.onchange=function(){{toggleObra(this.checked);}};
      }}

      var tipo={_json.dumps(c.get("tipo","PF"))};
      window.dmcTipo=tipo;
      setTipo(tipo);

      var docInpE=document.getElementById('f-doc');
      if(docInpE){{
        docInpE.onkeydown=function(e){{if(e.key==='Enter')buscarDoc();}};
      }}
      var consultarBtnE=document.getElementById('btn-consultar');
      if(consultarBtnE) consultarBtnE.onclick=function(){{buscarDoc();}};

      var telInp=document.getElementById('f-tel');
      if(telInp) telInp.oninput=function(){{this.value=maskTel(this.value);}};

      ['end','obra'].forEach(function(p){{
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
          var mapsInp=document.getElementById('f-maps-'+p);
          if(mapsInp&&q) mapsInp.value=url;
          window.open(url,'_blank','noopener,noreferrer');
        }};
      }});

      var prefill={{
        'f-nome':       {_json.dumps(c.get("nome",""))},
        'f-doc':        {_json.dumps(c.get("cpf",""))},
        'f-tel':        {_json.dumps(c.get("telefone",""))},
        'f-log-end':    {_json.dumps(c.get("end_log",""))},
        'f-num-end':    {_json.dumps(c.get("end_num",""))},
        'f-comp-end':   {_json.dumps(c.get("end_comp",""))},
        'f-bairro-end': {_json.dumps(c.get("end_bairro",""))},
        'f-cidade-end': {_json.dumps(c.get("end_cidade",""))},
        'f-uf-end':     {_json.dumps(c.get("end_estado",""))},
        'f-cep-end':    {_json.dumps(c.get("end_cep",""))},
        'f-maps-end':   {_json.dumps(c.get("end_maps",""))},
        'f-log-obra':    {_json.dumps(c.get("obra_log",""))},
        'f-num-obra':    {_json.dumps(c.get("obra_num",""))},
        'f-comp-obra':   {_json.dumps(c.get("obra_comp",""))},
        'f-bairro-obra': {_json.dumps(c.get("obra_bairro",""))},
        'f-cidade-obra': {_json.dumps(c.get("obra_cidade",""))},
        'f-uf-obra':     {_json.dumps(c.get("obra_estado",""))},
        'f-cep-obra':    {_json.dumps(c.get("obra_cep",""))},
        'f-maps-obra':   {_json.dumps(c.get("obra_maps",""))}
      }};
      Object.keys(prefill).forEach(function(id){{
        var el=document.getElementById(id);
        if(el) el.value=prefill[id];
      }});

      if({obra_mesmo_js}){{
        var oc2=document.getElementById('obra-mesmo');
        if(oc2){{oc2.checked=true; toggleObra(true);}}
      }}
    }},120);
    """)
    dlg.open()


# ── Buscar cliente ────────────────────────────────────────────────────

def buscar_cliente_dialog(campo: str) -> None:
    _CFG = {
        "nome": {
            "titulo":     "Buscar Cliente",
            "subtitulo":  "por Nome",
            "icon":       "person_search",
            "color":      "#60A5FA",
            "bg":         "rgba(96,165,250,.08)",
            "br":         "rgba(96,165,250,.25)",
            "placeholder":"Ex: João Silva",
            "hint":       None,
            "mask_js":    "",
            "mono":       False,
        },
        "telefone": {
            "titulo":     "Buscar Cliente",
            "subtitulo":  "por Telefone",
            "icon":       "phone",
            "color":      "#FBBF24",
            "bg":         "rgba(251,191,36,.08)",
            "br":         "rgba(251,191,36,.25)",
            "placeholder":"(48) 9 9999-9999",
            "hint":       None,
            "mask_js":    "inp.oninput=function(){this.value=maskTel(this.value);};",
            "mono":       True,
        },
        "cpf": {
            "titulo":     "Buscar Cliente",
            "subtitulo":  "por CPF / CNPJ",
            "icon":       "badge",
            "color":      "#C4B5FD",
            "bg":         "rgba(196,181,253,.08)",
            "br":         "rgba(196,181,253,.25)",
            "placeholder":"000.000.000-00 ou 00.000.000/0000-00",
            "hint":       "CPF &nbsp;·&nbsp; 000.000.000-00 &nbsp;&nbsp;|&nbsp;&nbsp; CNPJ &nbsp;·&nbsp; 00.000.000/0000-00",
            "mask_js":    "inp.oninput=function(){var d=this.value.replace(/\\D/g,'');this.value=d.length>11?maskCNPJ(this.value):maskCPF(this.value);};",
            "mono":       True,
        },
    }
    cfg     = _CFG.get(campo, _CFG["nome"])
    inp_id  = f"dlg-search-{campo}"
    trig_id = f"trig-buscar-{campo}"
    mono_s  = "font-family:'DM Mono',monospace;letter-spacing:.04em;" if cfg["mono"] else ""
    color, bg, br = cfg["color"], cfg["bg"], cfg["br"]

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:20px!important;padding:0;"
        "width:min(700px,96vw)!important;max-height:90vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;"
        "box-shadow:0 32px 80px rgba(0,0,0,.9)!important;"
    ):
        # ── Cabeçalho ────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:20px 24px 18px;"
            "display:flex;align-items:center;gap:16px;flex-shrink:0;"
        ):
            ui.html(
                f'<div style="width:44px;height:44px;border-radius:12px;flex-shrink:0;'
                f'background:{bg};border:1px solid {br};'
                f'display:flex;align-items:center;justify-content:center;">'
                f'<span class="material-icons" style="font-size:22px;color:{color}">{cfg["icon"]}</span></div>'
            )
            with ui.element("div").style("flex:1;min-width:0"):
                ui.html(
                    f'<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text);line-height:1.15">'
                    f'{cfg["titulo"]}</div>'
                )
                ui.html(
                    f'<div style="font:11px var(--dmc-mono);color:{color};'
                    f'letter-spacing:.1em;text-transform:uppercase;margin-top:2px">'
                    f'{cfg["subtitulo"]}</div>'
                )
            ui.button(icon="close", on_click=dlg.close).props('flat round dense').style(
                "color:var(--dmc-muted);flex-shrink:0;"
            )

        # ── Campo de busca ────────────────────────────────────────────
        with ui.element("div").style("padding:0 24px 20px;flex-shrink:0"):
            ui.html(
                f'<div style="position:relative;width:100%">'
                f'<span class="material-icons" style="position:absolute;left:14px;top:50%;'
                f'transform:translateY(-50%);font-size:19px;color:{color};'
                f'pointer-events:none;user-select:none">{cfg["icon"]}</span>'
                f'<input id="{inp_id}" autocomplete="off" placeholder="{cfg["placeholder"]}" autofocus'
                f' class="dmc-input" style="padding-left:46px;font-size:15px;{mono_s}"'
                f' onfocus="this.style.borderColor=\'{color}\'"'
                f' onblur="this.style.borderColor=\'var(--dmc-b1)\'">'
                f'</div>'
            )
            if cfg["hint"]:
                ui.html(
                    f'<div style="margin-top:8px;padding:7px 12px;'
                    f'background:{bg};border:1px solid {br};border-radius:8px;'
                    f'font:10px \'DM Mono\',monospace;color:{color};letter-spacing:.04em">'
                    f'{cfg["hint"]}</div>'
                )
            ui.html(
                '<div style="margin-top:10px;display:flex;align-items:center;gap:6px;'
                'font:11px var(--dmc-fm);color:var(--dmc-muted2)">'
                '<span class="material-icons" style="font-size:13px">keyboard_return</span>'
                'Pressione Enter para buscar</div>'
            )

        # ── Área de resultados ────────────────────────────────────────
        result_area = ui.element("div").style(
            "padding:0 24px 8px;overflow-y:auto;max-height:50vh;"
        )

        async def buscar():
            q = await ui.run_javascript(
                f"(document.getElementById('{inp_id}')?.value||'').trim().toLowerCase()"
            )
            if not q:
                ui.notify("Digite algo para buscar.", type="warning")
                return
            if campo == "cpf":
                q_raw = "".join(ch for ch in q if ch.isdigit())
                encontrados = [
                    c for c in load_clientes()
                    if q_raw and q_raw in "".join(x for x in c.get("cpf", "") if x.isdigit())
                ]
            else:
                encontrados = [
                    c for c in load_clientes()
                    if q in c.get(campo, "").lower()
                    or (campo == "nome" and q in c.get("nome", "").lower())
                ]
            result_area.clear()
            with result_area:
                ui.html('<div style="height:1px;background:#182418;margin-bottom:16px"></div>')
                if not encontrados:
                    with ui.element("div").style(
                        "text-align:center;padding:28px 0 20px;"
                    ):
                        ui.html(
                            f'<div style="width:52px;height:52px;border-radius:14px;'
                            f'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                            f'display:flex;align-items:center;justify-content:center;margin:0 auto 12px">'
                            f'<span class="material-icons" style="font-size:26px;color:var(--dmc-b2)">search_off</span></div>'
                        )
                        ui.html('<div style="font:600 13px var(--dmc-fm);color:var(--dmc-muted2)">Nenhum cliente encontrado</div>')
                    return

                ui.html(
                    f'<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                    f'letter-spacing:.12em;text-transform:uppercase;margin-bottom:12px">'
                    f'{len(encontrados)} resultado{"s" if len(encontrados)!=1 else ""}</div>'
                )
                for c in encontrados:
                    is_pf    = c["tipo"] == "PF"
                    t_icon   = "person" if is_pf else "business"
                    t_color  = "#4ADE80" if is_pf else "#60A5FA"
                    t_bg     = "rgba(74,222,128,.07)" if is_pf else "rgba(96,165,250,.07)"
                    t_br     = "rgba(74,222,128,.2)" if is_pf else "rgba(96,165,250,.2)"
                    initials = "".join(p[0].upper() for p in c.get("nome","?").split()[:2])
                    end_str  = ", ".join(filter(None, [
                        f"{c.get('end_log','')} {c.get('end_num','')}".strip(),
                        c.get("end_bairro",""),
                        f"{c.get('end_cidade','')} / {c.get('end_estado','')}".strip("/ "),
                    ]))

                    with ui.element("div").style(
                        "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);border-radius:14px;"
                        "padding:14px 16px;margin-bottom:8px;"
                        "display:flex;align-items:center;gap:14px;"
                        "transition:border-color .15s;"
                    ):
                        ui.html(
                            f'<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                            f'background:{t_bg};border:1px solid {t_br};'
                            f'display:flex;align-items:center;justify-content:center;'
                            f'font:700 13px \'DM Mono\',monospace;color:{t_color}">'
                            f'{initials}</div>'
                        )
                        with ui.element("div").style("flex:1;min-width:0"):
                            ui.html(
                                f'<div style="font:600 14px var(--dmc-fm);color:var(--dmc-text);'
                                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-bottom:3px">'
                                f'{c.get("nome","")}</div>'
                            )
                            with ui.element("div").style("display:flex;align-items:center;gap:10px;flex-wrap:wrap"):
                                if c.get("cpf"):
                                    ui.html(
                                        f'<span style="font:11px \'DM Mono\',monospace;color:#527A52">'
                                        f'{c["cpf"]}</span>'
                                    )
                                if c.get("telefone"):
                                    ui.html(
                                        f'<span style="font:11px \'DM Mono\',monospace;color:#FBBF24">'
                                        f'{c["telefone"]}</span>'
                                    )
                            if end_str.strip("/ ,"):
                                ui.html(
                                    f'<div style="display:flex;align-items:center;gap:4px;'
                                    f'font:11px \'Inter\',sans-serif;color:#527A52;margin-top:3px">'
                                    f'<span class="material-icons" style="font-size:12px;flex-shrink:0">location_on</span>'
                                    f'<span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                                    f'{end_str}</span></div>'
                                )

                        ver_btn = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm").style(
                            f"color:{t_color}!important;border-color:{t_br}!important;background:{t_bg}!important;"
                        )
                        with ver_btn:
                            ui.html('<span class="material-icons">open_in_new</span>')
                            ui.html("<span>Ver ficha</span>")
                        ver_btn.on("click", lambda cc=c: ver_ficha_dialog(cc))

        async def _attach_js(mid=inp_id, tid=trig_id, mjs=cfg["mask_js"]):
            await ui.run_javascript(f"""
                var inp=document.getElementById('{mid}');
                if(inp){{
                    inp.addEventListener('keydown',function(e){{
                        if(e.key==='Enter') document.getElementById('{tid}')?.click();
                    }});
                    {mjs}
                    inp.focus();
                }}
            """)
        ui.timer(0.12, _attach_js, once=True)

        # ── Rodapé ───────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Fechar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')
            buscar_btn = ui.element("button").classes("dmc-btn dmc-btn-primary").props(f'id="{trig_id}"')
            with buscar_btn:
                ui.html('<span class="material-icons" style="font-size:16px">search</span><span>Buscar</span>')
            buscar_btn.on("click", buscar)
    dlg.open()


# ── Cadastrar cliente (inline) ────────────────────────────────────────

def _addr_block_html(prefix: str) -> str:
    return f"""
<div class="dmc-flex-end" style="margin-bottom:4px">
  <div style="flex:1;min-width:0">
    <label class="dmc-label">CEP</label>
    <input class="dmc-input" id="f-cep-{prefix}" placeholder="00000-000" maxlength="9"
      inputmode="numeric">
  </div>
  <button type="button" class="dmc-btn" id="btn-cep-{prefix}">
    <span class="material-icons">search</span> Buscar CEP
  </button>
</div>
<div id="cep-status-{prefix}" class="dmc-status" style="margin-bottom:8px;color:transparent">_</div>
<div style="display:grid;grid-template-columns:1fr 72px;gap:8px;margin-bottom:8px">
  <div>
    <label class="dmc-label">Logradouro / Rua</label>
    <input class="dmc-input" id="f-log-{prefix}" placeholder="RUA, AV., ROD..."
      oninput="this.value=this.value.toUpperCase()">
  </div>
  <div>
    <label class="dmc-label">Nº</label>
    <input class="dmc-input" id="f-num-{prefix}" placeholder="000"
      oninput="this.value=this.value.toUpperCase()">
  </div>
</div>
<div style="margin-bottom:8px">
  <label class="dmc-label">Complemento</label>
  <input class="dmc-input" id="f-comp-{prefix}" placeholder="APTO, BLOCO, SALA..."
    oninput="this.value=this.value.toUpperCase()">
</div>
<div style="display:grid;grid-template-columns:1fr 1fr 52px;gap:8px;margin-bottom:8px">
  <div>
    <label class="dmc-label">Bairro</label>
    <input class="dmc-input" id="f-bairro-{prefix}" placeholder="BAIRRO"
      oninput="this.value=this.value.toUpperCase()">
  </div>
  <div>
    <label class="dmc-label">Cidade</label>
    <input class="dmc-input" id="f-cidade-{prefix}" placeholder="CIDADE"
      oninput="this.value=this.value.toUpperCase()">
  </div>
  <div>
    <label class="dmc-label">UF</label>
    <input class="dmc-input" id="f-uf-{prefix}" placeholder="SC" maxlength="2"
      oninput="this.value=this.value.toUpperCase()">
  </div>
</div>
<div class="dmc-flex-end">
  <div style="flex:1;min-width:0">
    <label class="dmc-label">Link Google Maps</label>
    <input class="dmc-input" id="f-maps-{prefix}" placeholder="Cole o link aqui...">
  </div>
  <button type="button" class="dmc-btn" id="btn-maps-{prefix}">
    <span class="material-icons">map</span> Maps
  </button>
</div>
"""


def cadastrar_cliente_dialog() -> None:
    _FORM_IDS = [
        "f-nome", "f-doc", "f-tel",
        "f-cep-end", "f-log-end", "f-num-end", "f-comp-end",
        "f-bairro-end", "f-cidade-end", "f-uf-end", "f-maps-end",
        "f-cep-obra", "f-log-obra", "f-num-obra", "f-comp-obra",
        "f-bairro-obra", "f-cidade-obra", "f-uf-obra", "f-maps-obra",
    ]

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(1100px,98vw)!important;max-width:98vw!important;max-height:92vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;"
    ):
        # ── Botão fechar (canto superior direito) ─────────────────────
        ui.button(icon="close", on_click=dlg.close).props(
            'flat round dense'
        ).style(
            "color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;"
        )

        # ── Cabeçalho ────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid var(--dmc-gd);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:var(--dmc-green)">person_add</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Cadastrar Cliente</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">Preencha os dados e clique em Salvar Cliente</div>')

        # ── Corpo (scrollável) ────────────────────────────────────────
        with ui.element("div").style("padding:22px 24px 8px;overflow-y:auto;flex:1"):

            # Tipo de cliente
            ui.html("""
            <div style="margin-bottom:22px">
              <div class="dmc-label" style="margin-bottom:10px">Tipo de Cliente</div>
              <div style="display:flex;gap:10px;max-width:360px">
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
            ui.html("""
            <div class="dmc-card">
              <div class="dmc-card-hdr">
                <span class="material-icons">person</span> Dados do Cliente
              </div>
              <div class="dmc-card-body">
                <div style="margin-bottom:12px">
                  <label class="dmc-label" id="nome-label" for="f-nome">Nome Completo</label>
                  <input class="dmc-input" id="f-nome" placeholder="NOME COMPLETO"
                    oninput="this.value=this.value.toUpperCase()">
                </div>
                <div style="display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:flex-end">
                  <div style="min-width:0">
                    <label class="dmc-label" id="doc-label">CPF</label>
                    <input class="dmc-input" id="f-doc" placeholder="000.000.000-00"
                      inputmode="numeric">
                  </div>
                  <button type="button" class="dmc-btn" id="btn-consultar">
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

            # Endereços — 2 colunas
            with ui.element("div").classes("dmc-cols-2"):
                with ui.element("div").classes("dmc-card").style("margin-bottom:0"):
                    ui.html(
                        '<div class="dmc-card-hdr">'
                        '<span class="material-icons">home</span>'
                        ' Endereço Pessoal / Comercial</div>'
                    )
                    with ui.element("div").classes("dmc-card-body"):
                        ui.html(_addr_block_html("end"))

                with ui.element("div").classes("dmc-card").style("margin-bottom:0"):
                    ui.html(
                        '<div class="dmc-card-hdr" style="justify-content:space-between">'
                        '<span style="display:flex;align-items:center;gap:8px">'
                        '<span class="material-icons">construction</span>'
                        ' Endereço da Obra'
                        '</span>'
                        '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;margin:0">'
                        '<input type="checkbox" id="obra-mesmo" onchange="toggleObra(this.checked)" '
                        'style="width:14px;height:14px;accent-color:var(--dmc-green);cursor:pointer;flex-shrink:0">'
                        '<span style="font:500 10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.08em;text-transform:uppercase;white-space:nowrap">'
                        'Mesmo endereço</span>'
                        '</label>'
                        '</div>'
                    )
                    with ui.element("div").classes("dmc-card-body"):
                        with ui.element("div").props('id="obra-fields-wrap"'):
                            ui.html(_addr_block_html("obra"))

            ui.element("div").style("height:12px")

        # ── Rodapé ───────────────────────────────────────────────────
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def salvar():
                vals = await ui.run_javascript("""({
                  tipo: window.dmcTipo||'PF',
                  nome: (document.getElementById('f-nome')?.value||'').trim().toUpperCase(),
                  doc:  (document.getElementById('f-doc')?.value||'').trim(),
                  tel:  (document.getElementById('f-tel')?.value||'').trim(),
                  obra_mesmo: document.getElementById('obra-mesmo')?.checked||false,
                  end_log:    (document.getElementById('f-log-end')?.value||'').trim().toUpperCase(),
                  end_num:    (document.getElementById('f-num-end')?.value||'').trim().toUpperCase(),
                  end_comp:   (document.getElementById('f-comp-end')?.value||'').trim().toUpperCase(),
                  end_bairro: (document.getElementById('f-bairro-end')?.value||'').trim().toUpperCase(),
                  end_cidade: (document.getElementById('f-cidade-end')?.value||'').trim().toUpperCase(),
                  end_uf:     (document.getElementById('f-uf-end')?.value||'').trim().toUpperCase(),
                  end_cep:    (document.getElementById('f-cep-end')?.value||'').trim(),
                  end_maps:   (document.getElementById('f-maps-end')?.value||'').trim(),
                  obra_log:    (document.getElementById('f-log-obra')?.value||'').trim().toUpperCase(),
                  obra_num:    (document.getElementById('f-num-obra')?.value||'').trim().toUpperCase(),
                  obra_comp:   (document.getElementById('f-comp-obra')?.value||'').trim().toUpperCase(),
                  obra_bairro: (document.getElementById('f-bairro-obra')?.value||'').trim().toUpperCase(),
                  obra_cidade: (document.getElementById('f-cidade-obra')?.value||'').trim().toUpperCase(),
                  obra_uf:     (document.getElementById('f-uf-obra')?.value||'').trim().toUpperCase(),
                  obra_cep:    (document.getElementById('f-cep-obra')?.value||'').trim(),
                  obra_maps:   (document.getElementById('f-maps-obra')?.value||'').trim(),
                })""")

                if not vals.get("nome") or not vals.get("doc") or not vals.get("tel"):
                    ui.notify("Preencha Nome, CPF/CNPJ e Telefone.", type="warning")
                    return

                tipo      = vals.get("tipo", "PF")
                obra_mesmo = vals.get("obra_mesmo", False)
                doc_fmt   = fmt_cpf(vals["doc"]) if tipo == "PF" else vals["doc"]

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
                    "end_cep":     vals["end_cep"],
                    "end_maps":    vals["end_maps"],
                    "obra_mesmo":  obra_mesmo,
                    "obra_log":    vals["end_log"]    if obra_mesmo else vals["obra_log"],
                    "obra_num":    vals["end_num"]    if obra_mesmo else vals["obra_num"],
                    "obra_comp":   vals["end_comp"]   if obra_mesmo else vals["obra_comp"],
                    "obra_bairro": vals["end_bairro"] if obra_mesmo else vals["obra_bairro"],
                    "obra_cidade": vals["end_cidade"] if obra_mesmo else vals["obra_cidade"],
                    "obra_estado": vals["end_uf"]     if obra_mesmo else vals["obra_uf"],
                    "obra_cep":    vals["end_cep"]    if obra_mesmo else vals["obra_cep"],
                    "obra_maps":   vals["end_maps"]   if obra_mesmo else vals["obra_maps"],
                    "data":        datetime.now().strftime("%d/%m/%Y %H:%M"),
                }
                add_cliente(cliente, usuario=current_user_label(), perfil=current_user_perfil())
                ui.notify(f"✓ Cliente '{vals['nome']}' cadastrado com sucesso!", type="positive")
                dlg.close()

            ui.button("Salvar Cliente", on_click=salvar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style("padding:0 22px")

    # Reseta o formulário e abre
    ids_js = ",".join(f"'{i}'" for i in _FORM_IDS)
    ui.run_javascript(f"""
    setTimeout(function(){{
      // ── Tipo PF/PJ: attach onclick via JS (inline onclick não é confiável no NiceGUI) ──
      document.querySelectorAll('.dmc-tipo-btn').forEach(function(b){{
        b.onclick=function(){{setTipo(b.dataset.tipo);}};
      }});

      // ── Reset estado ──────────────────────────────────────────────
      window.dmcTipo='PF';
      document.querySelectorAll('.dmc-tipo-btn').forEach(function(b){{
        b.classList.toggle('active',b.dataset.tipo==='PF');
      }});
      var docLbl=document.getElementById('doc-label');
      var nomeLbl=document.getElementById('nome-label');
      var docInp=document.getElementById('f-doc');
      var telInp=document.getElementById('f-tel');
      if(docLbl) docLbl.textContent='CPF';
      if(nomeLbl) nomeLbl.textContent='Nome Completo';
      if(docInp){{
        docInp.placeholder='000.000.000-00';
        docInp.inputMode='numeric';
        docInp.oninput=function(){{this.value=maskCPF(this.value);}};
        docInp.onkeydown=function(e){{if(e.key==='Enter')buscarDoc();}};
      }}
      var consultarBtn=document.getElementById('btn-consultar');
      if(consultarBtn) consultarBtn.onclick=function(){{buscarDoc();}};
      if(telInp) telInp.oninput=function(){{this.value=maskTel(this.value);}};
      ['end','obra'].forEach(function(p){{
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
          var mapsInp=document.getElementById('f-maps-'+p);
          if(mapsInp&&q) mapsInp.value=url;
          window.open(url,'_blank','noopener,noreferrer');
        }};
      }});
      var ds=document.getElementById('doc-status');
      if(ds) ds.style.color='transparent';
      var ow=document.getElementById('obra-fields-wrap');
      if(ow){{
        ow.style.opacity='1';
        ow.querySelectorAll('input,textarea,button').forEach(function(el){{el.disabled=false;}});
      }}
      var oc=document.getElementById('obra-mesmo');
      if(oc){{
        oc.checked=false;
        oc.onchange=function(){{toggleObra(this.checked);}};
      }}
      [{ids_js}].forEach(function(id){{
        var el=document.getElementById(id); if(el) el.value='';
      }});
      ['cep-status-end','cep-status-obra'].forEach(function(id){{
        var el=document.getElementById(id);
        if(el){{el.textContent='_';el.style.color='transparent';}}
      }});
    }},120);
    """)
    dlg.open()
