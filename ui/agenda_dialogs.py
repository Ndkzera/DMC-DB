"""Diálogos da integração com Google Calendar."""

import asyncio
import calendar as _cal_mod
from datetime import date, datetime, timedelta

from nicegui import ui

from services.auth import _load as _load_users
from services.obras import load_obras

from services.agenda import (
    start_auth_flow,
    finish_auth_flow,
    create_event,
    delete_event,
    disconnect,
    fmt_event,
    get_events,
    get_events_for_month,
    is_connected,
    CREDENTIALS_FILE,
)


# ── Paleta de cores para eventos ──────────────────────────────────────

_COLOR_MAP = {
    "1":  "#a4bdfc",  # Lavender
    "2":  "#7ae7bf",  # Sage
    "3":  "#dbadff",  # Grape
    "4":  "#ff887c",  # Flamingo
    "5":  "#fbd75b",  # Banana
    "6":  "#ffb878",  # Tangerine
    "7":  "#46d6db",  # Peacock
    "8":  "#e1e1e1",  # Graphite
    "9":  "#5484ed",  # Blueberry
    "10": "#51b749",  # Basil
    "11": "#dc2127",  # Tomato
}
_DEFAULT_COLOR = "#4ADE80"


# ── Conectar Google ───────────────────────────────────────────────────

def conectar_agenda_dialog() -> None:
    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;width:min(700px,97vw)!important;"
        "color:var(--dmc-text)!important;"
    ):
        # Cabeçalho
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">calendar_month</span></div>'
            )
            with ui.element("div"):
                ui.html('<div style="font:700 15px var(--dmc-fd);color:var(--dmc-text)">Conectar Google Agenda</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">Autorizção OAuth 2.0</div>')

        # Instruções
        with ui.element("div").style("padding:20px 24px"):
            ui.html(
                '<div style="font:600 11px var(--dmc-mono);color:var(--dmc-muted2);'
                'text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px">Passo a passo</div>'
            )

            steps = [
                ("cloud", "#60A5FA",
                 "Acesse o Google Cloud Console",
                 "console.cloud.google.com → Crie um projeto → Ative a Google Calendar API"),
                ("key", "#FBBF24",
                 "Crie credenciais OAuth 2.0",
                 'Credenciais → Criar → "App de computador" → Baixe o JSON'),
                ("folder_open", "#4ADE80",
                 f"Salve como credentials.json",
                 f"Destino: {CREDENTIALS_FILE}"),
                ("login", "#C4B5FD",
                 "Clique em Conectar abaixo",
                 "Um navegador abrirá para você autorizar o acesso"),
            ]

            for i, (icon, color, title, desc) in enumerate(steps, 1):
                with ui.element("div").style(
                    "display:flex;gap:12px;margin-bottom:14px;align-items:flex-start;"
                ):
                    ui.html(
                        f'<div style="width:28px;height:28px;border-radius:7px;flex-shrink:0;'
                        f'background:rgba(255,255,255,.04);border:1px solid var(--dmc-b2);'
                        f'display:flex;align-items:center;justify-content:center;">'
                        f'<span class="material-icons" style="font-size:14px;color:{color}">{icon}</span></div>'
                    )
                    with ui.element("div"):
                        ui.html(f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text)">{title}</div>')
                        ui.html(f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:2px">{desc}</div>')

            # Status de conexão (label reativo)
            status_lbl = ui.label("Aguardando conexão...").style(
                "display:block;margin-top:8px;padding:10px 14px;border-radius:9px;"
                "background:rgba(74,222,128,.05);border:1px solid var(--dmc-b1);"
                "font:12px var(--dmc-fm);color:var(--dmc-muted2);min-height:38px;"
            )

        # Rodapé
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:8px;"
        ):
            ui.button("Fechar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            auth_url_box = ui.html('').style('display:none')

            async def _conectar():
                btn_conectar.disable()
                status_lbl.set_text("Gerando link de autorização…")
                status_lbl.style("color:#FBBF24")
                try:
                    url = await asyncio.to_thread(start_auth_flow)
                    auth_url_box.set_content(
                        f'<div style="margin-top:10px;padding:12px 14px;'
                        f'background:rgba(96,165,250,.07);border:1px solid rgba(96,165,250,.25);'
                        f'border-radius:9px">'
                        f'<div style="font:600 11px var(--dmc-mono);color:#60A5FA;'
                        f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:6px">'
                        f'Abra este link no seu navegador</div>'
                        f'<a href="{url}" target="_blank" style="font:11px var(--dmc-mono);'
                        f'color:#93C5FD;word-break:break-all;text-decoration:none">{url}</a>'
                        f'<div style="font:10px var(--dmc-fm);color:var(--dmc-muted2);margin-top:8px">'
                        f'&#9432; Se estiver acessando via t&uacute;nel, abra '
                        f'<b>http://localhost:8080</b> primeiro para que o retorno OAuth funcione.</div>'
                        f'</div>'
                    )
                    auth_url_box.style('display:block')
                    status_lbl.set_text("Aguardando autorização no navegador…")
                    status_lbl.style("color:#FBBF24")
                    await asyncio.to_thread(finish_auth_flow)
                    auth_url_box.style('display:none')
                    status_lbl.set_text("✓ Conectado com sucesso!")
                    status_lbl.style("color:#4ADE80")
                    ui.notify("Google Agenda conectado!", type="positive")
                except FileNotFoundError as exc:
                    status_lbl.set_text(str(exc))
                    status_lbl.style("color:#F87171")
                except Exception as exc:
                    status_lbl.set_text(f"Erro: {exc}")
                    status_lbl.style("color:#F87171")
                finally:
                    btn_conectar.enable()

            btn_conectar = ui.button("Conectar", on_click=_conectar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style("padding:0 20px")
    dlg.open()


# ── Ver Agenda (visão mensal) ─────────────────────────────────────────

_CAL       = _cal_mod.Calendar(firstweekday=6)   # semana começa no domingo
_DOW_LABELS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
_MONTH_NAMES = [
    "Janeiro","Fevereiro","Março","Abril","Maio","Junho",
    "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro",
]


def ver_agenda_dialog() -> None:
    if not is_connected():
        conectar_agenda_dialog()
        return

    today = date.today()
    state = {"year": today.year, "month": today.month, "events": {}}

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:20px!important;padding:0!important;"
        "width:min(920px,97vw)!important;max-width:97vw!important;height:90vh!important;"
        "display:grid!important;grid-template-rows:auto auto 1fr auto!important;"
        "overflow:hidden!important;color:var(--dmc-text)!important;"
        "box-shadow:0 30px 80px rgba(0,0,0,.6)!important;"
    ):
        # ── Cabeçalho (grid row 1 — auto) ────────────────────────────
        with ui.element("div").style(
            "padding:14px 20px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:12px;"
            "background:rgba(0,0,0,.15);"
        ):
            ui.html(
                '<div style="width:38px;height:38px;border-radius:10px;flex-shrink:0;'
                'background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.3);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">calendar_month</span></div>'
            )
            with ui.element("div").style("display:flex;align-items:center;gap:2px"):
                prev_btn = ui.button(icon="chevron_left").props('flat round dense').style(
                    "color:var(--dmc-muted);width:32px;height:32px;"
                )
                month_lbl = ui.label("").style(
                    "font:700 16px var(--dmc-fd);color:var(--dmc-text);"
                    "min-width:188px;text-align:center;letter-spacing:.02em;"
                )
                next_btn = ui.button(icon="chevron_right").props('flat round dense').style(
                    "color:var(--dmc-muted);width:32px;height:32px;"
                )
            today_btn = ui.button("Hoje").props('flat no-caps').classes("dmc-btn dmc-btn-secondary dmc-btn-sm").style("margin-left:6px")
            ui.element("div").style("flex:1")
            with ui.element("div").style("display:flex;align-items:center;gap:4px"):
                ui.button(icon="add", on_click=lambda: [dlg.close(), novo_evento_dialog()]).props(
                    'flat round dense'
                ).style("color:var(--dmc-green)")
                ui.button(icon="close", on_click=dlg.close).props(
                    'flat round dense'
                ).style("color:var(--dmc-muted)")

        # ── Dias da semana (grid row 2 — auto) — HTML único garante grid correto ──
        _dow_cells = "".join(
            f'<div style="text-align:center;padding:10px 0;'
            f'font:600 12px \'DM Mono\',monospace;letter-spacing:.14em;'
            f'color:{"#60A5FA" if d in ("DOM","SÁB") else "#52657A"}">{d}</div>'
            for d in ["DOM", "SEG", "TER", "QUA", "QUI", "SEX", "SÁB"]
        )
        ui.html(
            f'<div style="display:grid;grid-template-columns:repeat(7,1fr);'
            f'padding:0 12px;border-bottom:1px solid var(--dmc-b1);'
            f'background:rgba(0,0,0,.2);">{_dow_cells}</div>'
        )

        # ── Grid do calendário (grid row 3 — 1fr) ────────────────────
        # Altura fixada via JS após render (único método confiável com Quasar)
        grid_wrap = ui.element("div").style(
            "overflow:hidden;padding:8px 12px 10px;"
        ).props('id=dmc-cal-wrap')
        with grid_wrap:
            grid = ui.element("div").style(
                "display:grid;grid-template-columns:repeat(7,1fr);"
                "grid-auto-rows:1fr;gap:5px;"
            ).props('id=dmc-cal-grid')

        # ── Rodapé (grid row 4 — auto) ────────────────────────────────
        with ui.element("div").style(
            "padding:10px 20px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:space-between;align-items:center;"
            "background:rgba(0,0,0,.15);"
        ):
            desl_btn = ui.element("button").classes("dmc-btn dmc-btn-secondary dmc-btn-sm")
            with desl_btn:
                ui.html('<span class="material-icons">link_off</span>')
                ui.html("<span>Desconectar Google</span>")
            desl_btn.on("click", lambda: [disconnect(),
                                          ui.notify("Conta Google desconectada.", type="info"),
                                          dlg.close()])
            ui.button("+ Novo Evento", on_click=lambda: [dlg.close(), novo_evento_dialog()]).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary')

        # ── Lógica de renderização ────────────────────────────────────

        def _render_grid():
            year, month   = state["year"], state["month"]
            events_by_day = state["events"]
            weeks         = _CAL.monthdayscalendar(year, month)

            month_lbl.set_text(f"{_MONTH_NAMES[month - 1]}  {year}")
            grid.clear()
            with grid:
                for week in weeks:
                    for day_num in week:
                        if day_num == 0:
                            ui.element("div").style(
                                "border-radius:8px;min-height:0;min-width:0;"
                                "background:rgba(0,0,0,.2);border:1px solid rgba(255,255,255,.03);"
                            )
                            continue

                        d          = date(year, month, day_num)
                        d_str      = d.isoformat()
                        is_today   = d == today
                        is_weekend = d.weekday() in (5, 6)
                        day_evts   = events_by_day.get(d_str, [])

                        if is_today:
                            bg, bdr, bdr_w = "rgba(74,222,128,.09)", "rgba(74,222,128,.55)", "1.5px"
                        elif is_weekend:
                            bg, bdr, bdr_w = "rgba(96,165,250,.04)", "rgba(96,165,250,.12)", "1px"
                        else:
                            bg, bdr, bdr_w = "rgba(255,255,255,.028)", "rgba(255,255,255,.07)", "1px"

                        cell = ui.element("div").style(
                            f"border-radius:8px;padding:6px 7px;min-height:0;min-width:0;"
                            f"border:{bdr_w} solid {bdr};background:{bg};"
                            "cursor:pointer;transition:border-color .15s,background .15s;"
                            "display:flex;flex-direction:column;gap:2px;overflow:hidden;"
                        )
                        with cell:
                            if is_today:
                                ui.html(
                                    f'<div style="display:flex;justify-content:flex-end;margin-bottom:2px">'
                                    f'<span style="width:24px;height:24px;border-radius:50%;'
                                    f'background:var(--dmc-green);color:#080f08;'
                                    f'font:700 12px var(--dmc-mono);flex-shrink:0;'
                                    f'display:flex;align-items:center;justify-content:center;">'
                                    f'{day_num}</span></div>'
                                )
                            else:
                                nc = "#60A5FA" if is_weekend else (
                                    "var(--dmc-text)" if day_evts else "#4A5E6A"
                                )
                                ui.html(
                                    f'<div style="text-align:right;font:600 12px var(--dmc-mono);'
                                    f'color:{nc};margin-bottom:2px;line-height:24px;">{day_num}</div>'
                                )

                            for ev in day_evts[:3]:
                                dot = _COLOR_MAP.get(ev["color"], _DEFAULT_COLOR)
                                if ev["all_day"]:
                                    pre = f'<span style="color:{dot};font-size:7px;flex-shrink:0;">●</span>'
                                else:
                                    t = ev["time_str"][:5]
                                    pre = f'<span style="color:rgba(255,255,255,.38);font-size:8px;flex-shrink:0;white-space:nowrap;">{t}</span>'
                                ui.html(
                                    f'<div style="background:{dot}18;border-left:2px solid {dot};'
                                    f'border-radius:3px;padding:1px 5px;'
                                    f'font:500 10px var(--dmc-fm);color:var(--dmc-text);'
                                    f'display:flex;align-items:center;gap:3px;'
                                    f'overflow:hidden;white-space:nowrap;">'
                                    f'{pre}'
                                    f'<span style="overflow:hidden;text-overflow:ellipsis;">{ev["title"]}</span>'
                                    f'</div>'
                                )
                            if len(day_evts) > 3:
                                ui.html(
                                    f'<div style="font:10px var(--dmc-fm);color:#4A5E6A;'
                                    f'padding-left:4px">+{len(day_evts) - 3} mais</div>'
                                )

                        cell.on("click", lambda d=d_str, evts=day_evts: _open_day(d, evts))

        def _open_day(d_str: str, day_evts: list):
            if day_evts:
                _day_detail_dialog(d_str, day_evts, dlg)
            else:
                dlg.close()
                novo_evento_dialog(d_str)

        async def _load():
            year, month = state["year"], state["month"]
            month_lbl.set_text(f"{_MONTH_NAMES[month - 1]}  {year}")
            n_weeks = len(_cal_mod.Calendar(firstweekday=6).monthdayscalendar(year, month))
            grid.clear()
            with grid:
                for _ in range(n_weeks * 7):
                    ui.element("div").style(
                        "border-radius:8px;min-height:0;min-width:0;"
                        "background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);"
                    )
            try:
                raw = await asyncio.to_thread(get_events_for_month, year, month)
                by_day: dict[str, list] = {}
                for evt in raw:
                    fe = fmt_event(evt)
                    by_day.setdefault(fe["date_key"], []).append(fe)
                state["events"] = by_day
            except RuntimeError:
                ui.notify("Sessão expirada — reconecte sua conta.", type="warning")
                state["events"] = {}
            except Exception as exc:
                ui.notify(f"Erro ao carregar agenda: {exc}", type="negative")
                state["events"] = {}
            _render_grid()

        async def _prev():
            if state["month"] == 1:
                state["year"] -= 1; state["month"] = 12
            else:
                state["month"] -= 1
            await _load()

        async def _next():
            if state["month"] == 12:
                state["year"] += 1; state["month"] = 1
            else:
                state["month"] += 1
            await _load()

        async def _go_today():
            state["year"] = today.year; state["month"] = today.month
            await _load()

        prev_btn.on("click", _prev)
        next_btn.on("click", _next)
        today_btn.on("click", _go_today)

    dlg.open()

    async def _fix_height():
        await ui.run_javascript("""
            (function() {
                const gw = document.getElementById('dmc-cal-wrap');
                if (!gw) return;
                const card = gw.closest('.q-card');
                if (!card) return;
                let used = 0;
                for (const c of card.children) { if (c !== gw) used += c.offsetHeight; }
                const avail = Math.max(card.offsetHeight - used, 100);
                gw.style.height = avail + 'px';
                const g = document.getElementById('dmc-cal-grid');
                if (g) g.style.height = (avail - 18) + 'px';
            })();
        """)

    ui.timer(0.05, _load, once=True)
    ui.timer(0.2, _fix_height, once=True)


def _day_detail_dialog(d_str: str, day_evts: list, parent_dlg) -> None:
    """Dialog com os eventos de um dia específico."""
    try:
        d_obj  = date.fromisoformat(d_str)
        _DIAS  = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]
        _MESES_FULL = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                       "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
        title  = f"{_DIAS[d_obj.weekday()]}, {d_obj.day} de {_MESES_FULL[d_obj.month-1]}"
    except Exception:
        title = d_str

    with ui.dialog() as dlg2, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:16px!important;padding:0;width:min(640px,97vw)!important;max-height:80vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;"
    ):
        with ui.element("div").style(
            "padding:16px 20px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:12px;flex-shrink:0;"
        ):
            ui.html(
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">today</span>'
            )
            with ui.element("div").style("flex:1"):
                ui.html(f'<div style="font:700 14px var(--dmc-fd);color:var(--dmc-text)">{title}</div>')
                ui.html(
                    f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2)">'
                    f'{len(day_evts)} evento(s)</div>'
                )
            ui.button(icon="close", on_click=dlg2.close).props('flat round dense').style(
                "color:var(--dmc-muted)"
            )

        with ui.element("div").style("padding:14px 18px;overflow-y:auto;flex:1"):
            for ev in day_evts:
                dot = _COLOR_MAP.get(ev["color"], _DEFAULT_COLOR)
                _render_event_card(ev, dot, lambda: None)

        with ui.element("div").style(
            "padding:12px 20px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:8px;flex-shrink:0;"
        ):
            ui.button("Fechar", on_click=dlg2.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')
            ui.button("Novo evento neste dia",
                      on_click=lambda: [dlg2.close(), parent_dlg.close(), novo_evento_dialog(d_str)]
                      ).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary').style(
                "font-family:'DM Mono',monospace;font-size:12px"
            )
    dlg2.open()


def _render_event_card(ev: dict, dot_color: str, on_reload) -> None:
    with ui.element("div").style(
        "background:var(--dmc-bg3);border:1px solid var(--dmc-b1);border-radius:11px;"
        "padding:12px 14px;margin-bottom:6px;"
        "display:flex;align-items:flex-start;gap:12px;transition:border-color .15s;"
    ):
        # Barra colorida à esquerda
        ui.element("div").style(
            f"width:3px;border-radius:2px;background:{dot_color};"
            "align-self:stretch;flex-shrink:0;min-height:20px;"
        )

        with ui.element("div").style("flex:1;min-width:0"):
            # Título
            ui.html(
                f'<div style="font:500 13px var(--dmc-fm);color:var(--dmc-text);'
                f'margin-bottom:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                f'{ev["title"]}</div>'
            )
            # Horário
            time_color = "var(--dmc-muted2)" if not ev["all_day"] else "#FBBF24"
            ui.html(
                f'<div style="display:flex;align-items:center;gap:5px;'
                f'font:11px var(--dmc-mono);color:{time_color}">'
                f'<span class="material-icons" style="font-size:12px">'
                f'{"schedule" if not ev["all_day"] else "today"}</span>'
                f'{ev["time_str"]}</div>'
            )
            # Local
            if ev["location"]:
                ui.html(
                    f'<div style="display:flex;align-items:center;gap:5px;'
                    f'font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-top:3px;'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'
                    f'<span class="material-icons" style="font-size:12px;flex-shrink:0">location_on</span>'
                    f'{ev["location"]}</div>'
                )
            # Descrição
            if ev["description"]:
                desc = ev["description"][:80] + ("…" if len(ev["description"]) > 80 else "")
                ui.html(
                    f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);'
                    f'margin-top:4px;line-height:1.45">{desc}</div>'
                )

        # Botões de ação
        with ui.element("div").style("display:flex;flex-direction:column;gap:4px;flex-shrink:0"):
            if ev["html_link"]:
                open_btn = ui.element("button").classes("dmc-btn dmc-btn-icon").props(
                    'title="Abrir no Google Calendar"'
                )
                with open_btn:
                    ui.html('<span class="material-icons" style="font-size:13px">open_in_new</span>')
                open_btn.on("click", lambda u=ev["html_link"]: ui.run_javascript(
                    f"window.open({repr(u)},'_blank','noopener,noreferrer');"
                ))

            del_btn = ui.element("button").classes("dmc-btn dmc-btn-icon").style(
                "color:#F87171;border-color:rgba(127,29,29,.3)"
            ).props('title="Excluir evento"')
            with del_btn:
                ui.html('<span class="material-icons" style="font-size:13px">delete_outline</span>')

            async def _del(eid=ev["id"]):
                try:
                    await asyncio.to_thread(delete_event, eid)
                    ui.notify("Evento excluído.", type="positive")
                    await on_reload()
                except Exception as exc:
                    ui.notify(f"Erro ao excluir: {exc}", type="negative")

            del_btn.on("click", _del)


# ── Novo Evento ───────────────────────────────────────────────────────

def novo_evento_dialog(prefill_date: str = "") -> None:
    if not is_connected():
        conectar_agenda_dialog()
        return

    hoje     = prefill_date or datetime.now().strftime("%Y-%m-%d")
    hora_ini = datetime.now().replace(minute=0, second=0).strftime("%H:%M")
    hora_fim = (datetime.now().replace(minute=0, second=0) + timedelta(hours=1)).strftime("%H:%M")

    _usuarios = [u.get("nome", "") for u in _load_users() if u.get("nome")]
    _obras    = load_obras()

    # HTML dos checkboxes da equipe
    _resp_html = "".join(
        f'<label style="display:flex;align-items:center;gap:8px;padding:6px 12px;'
        f'cursor:pointer;transition:background .12s;font:12px var(--dmc-fm);color:var(--dmc-text)">'
        f'<input type="checkbox" class="ne-resp-cb" value="{n}" '
        f'style="accent-color:#4ADE80;width:14px;height:14px;flex-shrink:0"'
        f' onchange="neUpdateEquipe()"> {n}</label>'
        for n in _usuarios
    )

    # Opções de obras para o select
    _obras_opts = "".join(
        f'<option value="{o.get("id","")}">'
        f'{o.get("cliente_nome","?")} — {o.get("obra_log","")}, {o.get("obra_cidade","")}'
        f'</option>'
        for o in _obras
    )

    with ui.dialog() as dlg, ui.card().style(
        "background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;"
        "border-radius:18px!important;padding:0;"
        "width:min(720px,97vw)!important;max-height:92vh;"
        "display:flex;flex-direction:column;color:var(--dmc-text)!important;"
    ):
        # Cabeçalho
        with ui.element("div").style(
            "padding:18px 24px;border-bottom:1px solid var(--dmc-b1);"
            "display:flex;align-items:center;gap:14px;"
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid var(--dmc-gd);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:var(--dmc-green)">add_circle</span></div>'
            )
            with ui.element("div").style("flex:1"):
                ui.html('<div style="font:700 15px var(--dmc-fd);color:var(--dmc-text)">Novo Evento</div>')
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Criar evento no Google Agenda</div>')
            ui.button(icon="close", on_click=dlg.close).props('flat round dense').style("color:var(--dmc-muted)")

        # Formulário
        with ui.element("div").style("padding:22px 24px;overflow-y:auto;flex:1;min-height:0"):

            # ── Título ────────────────────────────────────────────────
            ui.html('<label class="dmc-label">Título</label>')
            ui.html(
                '<input class="dmc-input" id="ne-titulo" placeholder="Ex: Levantamento topográfico" '
                'style="margin-bottom:16px" autofocus>'
            )

            # ── Dia inteiro ───────────────────────────────────────────
            ui.html("""
            <label class="dmc-check-row" style="margin-bottom:14px">
              <input type="checkbox" id="ne-allday"
                onchange="var h=document.getElementById('ne-hora-wrap');
                          if(h) h.style.display=this.checked?'none':'grid';">
              <span>Dia inteiro</span>
            </label>
            """)

            # ── Datas e horas ─────────────────────────────────────────
            ui.html(f"""
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:4px">
              <div><label class="dmc-label">Data início</label>
                   <input class="dmc-input" type="date" id="ne-data-ini" value="{hoje}"></div>
              <div><label class="dmc-label">Data fim</label>
                   <input class="dmc-input" type="date" id="ne-data-fim" value="{hoje}"></div>
            </div>
            <div id="ne-hora-wrap" style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px">
              <div><label class="dmc-label">Hora início</label>
                   <input class="dmc-input" type="time" id="ne-hora-ini" value="{hora_ini}"></div>
              <div><label class="dmc-label">Hora fim</label>
                   <input class="dmc-input" type="time" id="ne-hora-fim" value="{hora_fim}"></div>
            </div>
            """)

            # ── Modificadores ─────────────────────────────────────────
            ui.html(
                '<label class="dmc-label" style="margin-bottom:8px">Modificador</label>'
                '<input type="hidden" id="ne-modificador" value="">'
                '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:16px">'

                '  <button type="button" id="ne-mod-diaria"'
                '    style="display:flex;align-items:center;gap:8px;background:var(--dmc-bg3);'
                '           border:1px solid var(--dmc-b1);border-radius:10px;padding:11px 12px;'
                '           cursor:pointer;transition:border-color .15s,background .15s;text-align:left">'
                '    <span class="material-icons" style="font-size:18px;color:#60A5FA;flex-shrink:0">wb_sunny</span>'
                '    <span style="font:600 12px var(--dmc-fm);color:var(--dmc-text)">Diária</span>'
                '  </button>'

                '  <button type="button" id="ne-mod-meia"'
                '    style="display:flex;align-items:center;gap:8px;background:var(--dmc-bg3);'
                '           border:1px solid var(--dmc-b1);border-radius:10px;padding:11px 12px;'
                '           cursor:pointer;transition:border-color .15s,background .15s;text-align:left">'
                '    <span class="material-icons" style="font-size:18px;color:#FBBF24;flex-shrink:0">brightness_5</span>'
                '    <span style="font:600 12px var(--dmc-fm);color:var(--dmc-text)">Meia Diária</span>'
                '  </button>'

                '  <button type="button" id="ne-mod-lev"'
                '    style="display:flex;align-items:center;gap:8px;background:var(--dmc-bg3);'
                '           border:1px solid var(--dmc-b1);border-radius:10px;padding:11px 12px;'
                '           cursor:pointer;transition:border-color .15s,background .15s;text-align:left">'
                '    <span class="material-icons" style="font-size:18px;color:#34D399;flex-shrink:0">terrain</span>'
                '    <span style="font:600 12px var(--dmc-fm);color:var(--dmc-text)">Levantamento</span>'
                '  </button>'

                '</div>'
            )

            # ── Descrição ─────────────────────────────────────────────
            ui.html('<label class="dmc-label">Descrição (opcional)</label>')
            ui.html(
                '<textarea class="dmc-input" id="ne-desc" placeholder="Detalhes do evento..." '
                'rows="3" style="height:auto;padding-top:10px;padding-bottom:10px;'
                'resize:vertical;margin-bottom:12px"></textarea>'
            )

            # ── Local ─────────────────────────────────────────────────
            ui.html('<label class="dmc-label">Local (opcional)</label>')
            ui.html(
                '<input class="dmc-input" id="ne-local" placeholder="Endereço ou link de videoconferência"'
                ' style="margin-bottom:16px">'
            )

            # ── Obra relacionada ──────────────────────────────────────
            ui.html('<label class="dmc-label">Obra relacionada</label>')
            if _obras:
                ui.html(
                    '<select id="ne-obra" class="dmc-input" style="margin-bottom:16px">'
                    '<option value="">— Nenhuma —</option>'
                    f'{_obras_opts}'
                    '</select>'
                )
            else:
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);'
                    'padding:6px 0;margin-bottom:16px">Nenhuma obra cadastrada.</div>'
                )

            # ── Equipe destacada (collapsible) ────────────────────────
            ui.html(
                '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">'
                '  <label class="dmc-label" style="margin:0">Equipe destacada para a medição</label>'
                '  <button type="button" id="ne-equipe-btn" '
                '    style="display:flex;align-items:center;gap:5px;background:var(--dmc-bg3);'
                '           border:1px solid var(--dmc-b1);border-radius:8px;padding:4px 10px;'
                '           cursor:pointer;font:500 11px var(--dmc-mono);color:var(--dmc-muted2);'
                '           transition:border-color .15s">'
                '    <span id="ne-equipe-badge" style="display:none;background:#4ADE8030;'
                '      border:1px solid #4ADE8060;color:#4ADE80;border-radius:20px;'
                '      padding:0 6px;font:700 10px var(--dmc-mono)">0</span>'
                '    <span id="ne-equipe-btn-txt">Selecionar</span>'
                '    <span class="material-icons" id="ne-equipe-arrow" '
                '      style="font-size:14px;transition:transform .2s">expand_more</span>'
                '  </button>'
                '</div>'
            )
            if _resp_html:
                ui.html(
                    f'<div id="ne-resp-wrap" style="display:none;overflow:hidden;'
                    f'border:1px solid var(--dmc-b1);border-radius:10px;padding:4px 2px;'
                    f'margin-bottom:6px;max-height:180px;overflow-y:auto">'
                    f'{_resp_html}'
                    f'</div>'
                )
            else:
                ui.html('<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);'
                        'padding:4px 0;margin-bottom:6px">Nenhum usuário cadastrado.</div>')

        # Rodapé
        with ui.element("div").style(
            "padding:14px 24px;border-top:1px solid var(--dmc-b1);"
            "display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;"
        ):
            ui.button("Cancelar", on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _criar():
                vals = await ui.run_javascript("""({
                  titulo:   (document.getElementById('ne-titulo')?.value||'').trim(),
                  desc:     (document.getElementById('ne-desc')?.value||'').trim(),
                  local:    (document.getElementById('ne-local')?.value||'').trim(),
                  equipe:   Array.from(document.querySelectorAll('.ne-resp-cb:checked')).map(e=>e.value).join(', '),
                  allday:   document.getElementById('ne-allday')?.checked||false,
                  dataIni:  document.getElementById('ne-data-ini')?.value||'',
                  dataFim:  document.getElementById('ne-data-fim')?.value||'',
                  horaIni:  document.getElementById('ne-hora-ini')?.value||'00:00',
                  horaFim:  document.getElementById('ne-hora-fim')?.value||'01:00',
                  modificador: (document.getElementById('ne-modificador')?.value||'').trim(),
                  obra:     (document.getElementById('ne-obra')?.value||'').trim(),
                })""")

                if not vals.get("titulo"):
                    ui.notify("Preencha o título do evento.", type="warning")
                    return
                if not vals.get("dataIni"):
                    ui.notify("Selecione a data de início.", type="warning")
                    return

                # Monta descrição com todos os metadados
                linhas = []
                if vals.get("equipe"):
                    linhas.append(f"Equipe: {vals['equipe']}")
                if vals.get("obra"):
                    # Resolve nome da obra pelo id
                    obra_nome = next(
                        (f"{o.get('cliente_nome','?')} — {o.get('obra_log','')}, {o.get('obra_cidade','')}"
                         for o in _obras if o.get("id") == vals["obra"]), vals["obra"]
                    )
                    linhas.append(f"Obra: {obra_nome}")
                if vals.get("modificador"):
                    linhas.append(f"Modificador: {vals['modificador']}")
                if vals.get("desc"):
                    linhas.append(vals["desc"])
                desc_final = "\n".join(linhas)

                try:
                    if vals["allday"]:
                        d_fim = vals["dataFim"] or vals["dataIni"]
                        d_obj = datetime.strptime(d_fim, "%Y-%m-%d").date()
                        d_fim_exc = (d_obj + timedelta(days=1)).isoformat()
                        await asyncio.to_thread(
                            create_event, vals["titulo"], desc_final, vals["local"],
                            True, vals["dataIni"], d_fim_exc,
                        )
                    else:
                        start_iso = f"{vals['dataIni']}T{vals['horaIni']}:00"
                        d_fim     = vals["dataFim"] or vals["dataIni"]
                        end_iso   = f"{d_fim}T{vals['horaFim']}:00"
                        await asyncio.to_thread(
                            create_event, vals["titulo"], desc_final, vals["local"],
                            False, vals["dataIni"], d_fim, start_iso, end_iso,
                        )
                    ui.notify(f"✓ Evento '{vals['titulo']}' criado!", type="positive")
                    dlg.close()
                except Exception as exc:
                    ui.notify(f"Erro ao criar evento: {exc}", type="negative")

            ui.button("Criar Evento", on_click=_criar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style("padding:0 22px")

    dlg.open()

    ui.run_javascript("""
    setTimeout(function() {

      // ── Modificador toggle ────────────────────────────────────────
      var _ACTIVE_STYLE = 'border-color:#60A5FA;background:rgba(96,165,250,.08)';
      var _ACTIVE_MEIA  = 'border-color:#FBBF24;background:rgba(251,191,36,.08)';
      var _ACTIVE_LEV   = 'border-color:#34D399;background:rgba(52,211,153,.08)';
      var _IDLE_STYLE   = 'border:1px solid var(--dmc-b1);background:var(--dmc-bg3)';

      function neSetMod(val) {
        var inp  = document.getElementById('ne-modificador');
        var btnD = document.getElementById('ne-mod-diaria');
        var btnM = document.getElementById('ne-mod-meia');
        var btnL = document.getElementById('ne-mod-lev');
        if (!inp) return;
        var same  = inp.value === val;
        inp.value = same ? '' : val;
        if (btnD) btnD.style.cssText = (!same && val==='Diária')        ? _ACTIVE_STYLE : _IDLE_STYLE;
        if (btnM) btnM.style.cssText = (!same && val==='Meia Diária')   ? _ACTIVE_MEIA  : _IDLE_STYLE;
        if (btnL) btnL.style.cssText = (!same && val==='Levantamento')  ? _ACTIVE_LEV   : _IDLE_STYLE;
      }

      var btnD = document.getElementById('ne-mod-diaria');
      var btnM = document.getElementById('ne-mod-meia');
      var btnL = document.getElementById('ne-mod-lev');
      if (btnD) btnD.onclick = function() { neSetMod('Diária'); };
      if (btnM) btnM.onclick = function() { neSetMod('Meia Diária'); };
      if (btnL) btnL.onclick = function() { neSetMod('Levantamento'); };

      // ── Equipe toggle ─────────────────────────────────────────────
      var equipeBtn = document.getElementById('ne-equipe-btn');
      if (equipeBtn) {
        equipeBtn.onclick = function() {
          var wrap  = document.getElementById('ne-resp-wrap');
          var arrow = document.getElementById('ne-equipe-arrow');
          var txt   = document.getElementById('ne-equipe-btn-txt');
          if (!wrap) return;
          var open = wrap.style.display === 'none' || wrap.style.display === '';
          wrap.style.display    = open ? 'block' : 'none';
          if (arrow) arrow.style.transform = open ? 'rotate(180deg)' : '';
          if (txt)   txt.textContent       = open ? 'Fechar' : 'Selecionar';
        };
      }

      // badge contador da equipe
      document.querySelectorAll('.ne-resp-cb').forEach(function(cb) {
        cb.onchange = function() {
          var checked = document.querySelectorAll('.ne-resp-cb:checked').length;
          var badge   = document.getElementById('ne-equipe-badge');
          if (!badge) return;
          badge.textContent    = checked;
          badge.style.display  = checked ? 'inline' : 'none';
        };
      });

    }, 200);
    """)
