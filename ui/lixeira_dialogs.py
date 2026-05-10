"""Diálogo de Lixeira — visualizar, baixar e excluir permanentemente."""

import re
import shutil
from pathlib import Path

from nicegui import app as _app, ui

from services.files import cat, fmt_size

_TS_RE    = re.compile(r"__\d{8}_\d{6}$")
_TS_PARSE = re.compile(r"__(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})")


def _orig_name(p: Path) -> str:
    base = p.stem if p.suffix else p.name
    return _TS_RE.sub("", base) + p.suffix


def _del_date(p: Path) -> str:
    m = _TS_PARSE.search(p.name)
    if m:
        return f"{m.group(3)}/{m.group(2)}/{m.group(1)} {m.group(4)}:{m.group(5)}"
    return "—"


def lixeira_dialog() -> None:
    from config import TRASH_DIR
    from services.auth import check_login

    def _items() -> list[Path]:
        try:
            return sorted(TRASH_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        except OSError:
            return []

    def _pedir_senha(titulo: str, on_confirm) -> None:
        with ui.dialog().props("persistent") as pw_dlg:
            pw_dlg.open()
            with ui.card().style(
                "width:360px;max-width:94vw;padding:0;"
                "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
            ):
                with ui.element("div").style(
                    "padding:16px 20px;border-bottom:1px solid var(--dmc-b1);"
                ):
                    ui.html(
                        f'<div style="font:600 13px var(--dmc-fd);color:var(--dmc-text)">{titulo}</div>'
                        '<div style="font:11px var(--dmc-fm);color:#F87171;margin-top:4px">'
                        "Esta ação é irreversível.</div>"
                    )
                with ui.element("div").style(
                    "padding:16px 20px;display:flex;flex-direction:column;gap:10px"
                ):
                    ui.html('<label class="dmc-label" style="margin-bottom:5px">Senha</label>')
                    with ui.element('div').style('position:relative;width:100%'):
                        ui.html(
                            '<input type="password" id="lx-pw-conf" class="dmc-input"'
                            ' placeholder="••••••••" autocomplete="current-password"'
                            ' style="padding-right:44px;height:40px;width:100%;box-sizing:border-box">'
                        )
                        with ui.element('button').style(
                            'position:absolute;right:0;top:0;height:40px;width:40px;'
                            'background:transparent;border:none;cursor:pointer;'
                            'display:flex;align-items:center;justify-content:center;padding:0;'
                        ).props('type=button tabindex=-1') as _lx_tog:
                            _lx_icon = ui.html(
                                '<span class="material-icons" '
                                'style="font-size:18px;color:var(--dmc-muted)">visibility_off</span>'
                            )

                        async def _lx_pw_toggle():
                            state = await ui.run_javascript(
                                "var i=document.getElementById('lx-pw-conf');"
                                "if(!i) return 'x';"
                                "if(i.type==='password'){i.type='text';return 'text';}"
                                "i.type='password';return 'password';"
                            )
                            _lx_icon.set_content(
                                '<span class="material-icons" style="font-size:18px;color:var(--dmc-muted)">'
                                + ('visibility' if state == 'text' else 'visibility_off') + '</span>'
                            )
                        _lx_tog.on('click', _lx_pw_toggle)
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

                        async def _do_confirm(pw_dlg=pw_dlg, err_lbl=err_lbl):
                            senha = await ui.run_javascript(
                                "document.getElementById('lx-pw-conf')?.value || ''"
                            )
                            email = _app.storage.user.get("dmc_user_email", "")
                            if not check_login(email, senha):
                                err_lbl.set_content(
                                    '<span style="color:#F87171">Senha incorreta.</span>'
                                )
                                return
                            pw_dlg.close()
                            on_confirm()

                        cf.on("click", _do_confirm)

    with ui.dialog().props("persistent") as dlg:
        dlg.open()
        with ui.card().style(
            "width:720px;max-width:96vw;max-height:88vh;padding:0;"
            "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
            "display:flex;flex-direction:column;overflow:hidden;"
        ):
            with ui.element("div").style(
                "display:flex;align-items:center;gap:10px;padding:16px 20px;"
                "border-bottom:1px solid var(--dmc-b1);flex-shrink:0;"
            ):
                ui.html(
                    '<span class="material-icons" style="color:#F87171;font-size:22px">delete</span>'
                    '<span style="font:700 15px var(--dmc-fd);color:var(--dmc-text)">Lixeira</span>'
                )
                ui.element("div").style("flex:1")
                cb = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
                with cb:
                    ui.html('<span class="material-icons" style="font-size:17px">close</span>')
                cb.on("click", dlg.close)

            list_area = ui.element("div").style(
                "flex:1;overflow-y:auto;padding:14px 20px;min-height:0;"
            )
            footer_area = ui.element("div").style(
                "flex-shrink:0;border-top:1px solid var(--dmc-b1);"
                "padding:12px 20px;display:flex;align-items:center;gap:8px;"
            )

    def _render():
        list_area.clear()
        footer_area.clear()
        items = _items()

        with list_area:
            if not items:
                with ui.element("div").style(
                    "display:flex;flex-direction:column;align-items:center;"
                    "padding:60px 20px;gap:12px;color:var(--dmc-muted2);"
                ):
                    ui.html(
                        '<span class="material-icons" style="font-size:52px;opacity:.2">'
                        "delete_outline</span>"
                        '<div style="font:12px var(--dmc-fm)">Lixeira vazia</div>'
                    )
            else:
                total_b = 0
                for p in items:
                    try:
                        total_b += (
                            sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                            if p.is_dir()
                            else p.stat().st_size
                        )
                    except OSError:
                        pass

                ui.html(
                    f'<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);margin-bottom:10px">'
                    f'{len(items)} {"item" if len(items) == 1 else "itens"} · {fmt_size(total_b)}</div>'
                )

                for p in items:
                    is_dir = p.is_dir()
                    orig   = _orig_name(p)
                    ddate  = _del_date(p)

                    if is_dir:
                        ic, co, lb = "folder", "#FBBF24", "PASTA"
                        try:
                            sz_b = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                        except OSError:
                            sz_b = 0
                    else:
                        c = cat(p.suffix.lower())
                        ic, co, lb = c["icon"], c["color"], c["label"]
                        try:
                            sz_b = p.stat().st_size
                        except OSError:
                            sz_b = 0

                    with ui.element("div").style(
                        "display:flex;align-items:center;gap:10px;padding:10px 12px;"
                        "border-radius:8px;background:var(--dmc-bg3);"
                        "border:1px solid var(--dmc-b1);margin-bottom:6px;"
                    ):
                        ui.html(
                            f'<span class="material-icons" style="font-size:22px;color:{co};'
                            f'flex-shrink:0">{ic}</span>'
                        )
                        with ui.element("div").style("flex:1;min-width:0"):
                            ui.html(
                                f'<div style="font:500 12px var(--dmc-fm);color:var(--dmc-text);'
                                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{orig}</div>'
                                f'<div style="font:10px var(--dmc-mono);color:var(--dmc-muted2);margin-top:3px">'
                                f'<span style="background:{co}20;color:{co};padding:1px 5px;'
                                f'border-radius:3px;font-size:9px;margin-right:6px">{lb}</span>'
                                f'{fmt_size(sz_b)} · Excluído: {ddate}</div>'
                            )
                        with ui.element("div").style("display:flex;gap:6px;flex-shrink:0"):
                            if not is_dir:
                                dl = ui.element("button").classes(
                                    "dmc-btn dmc-btn-secondary dmc-btn-sm"
                                )
                                with dl:
                                    ui.html(
                                        '<span class="material-icons" style="font-size:14px">download</span>'
                                        "<span>Download</span>"
                                    )
                                dl.on(
                                    "click",
                                    lambda fname=p.name: ui.run_javascript(
                                        f"window.location.href='/api/trash/{fname}'"
                                    ),
                                )

                            dx = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
                            with dx:
                                ui.html(
                                    '<span class="material-icons" style="font-size:14px">delete_forever</span>'
                                    "<span>Excluir</span>"
                                )

                            def _del_one(path=p):
                                def _do():
                                    try:
                                        if path.is_dir():
                                            shutil.rmtree(path)
                                        else:
                                            path.unlink()
                                        ui.notify(
                                            f"'{_orig_name(path)}' excluído permanentemente.",
                                            type="positive",
                                        )
                                    except Exception as ex:
                                        ui.notify(f"Erro: {ex}", type="negative")
                                    _render()

                                _pedir_senha(
                                    f'Excluir "{_orig_name(path)}" permanentemente?',
                                    _do,
                                )

                            dx.on("click", _del_one)

        with footer_area:
            ui.element("div").style("flex:1")
            if items:
                ez = ui.element("button").classes("dmc-btn dmc-btn-danger dmc-btn-sm")
                with ez:
                    ui.html(
                        '<span class="material-icons" style="font-size:15px">delete_sweep</span>'
                        "<span>Esvaziar Lixeira</span>"
                    )

                def _esvaziar():
                    def _do():
                        erros = 0
                        for path in _items():
                            try:
                                if path.is_dir():
                                    shutil.rmtree(path)
                                else:
                                    path.unlink()
                            except Exception:
                                erros += 1
                        if erros:
                            ui.notify(
                                f"Lixeira esvaziada com {erros} erro(s).", type="warning"
                            )
                        else:
                            ui.notify("Lixeira esvaziada.", type="positive")
                        _render()

                    _pedir_senha("Esvaziar lixeira permanentemente?", _do)

                ez.on("click", _esvaziar)

    _render()
