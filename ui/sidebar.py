"""Componente de sidebar — filtros de tipo de arquivo, menu de clientes e agenda."""

from nicegui import ui
from ui.agenda_dialogs import conectar_agenda_dialog, novo_evento_dialog, ver_agenda_dialog
from ui.obras_dialogs import nova_obra_dialog, ver_obras_dialog
from ui.campo_dialogs import agenda_campo_dialog, historico_dialog
from ui.processamento_dialogs import norte_magnetico_dialog, processamento_campo_dialog, processamento_campo_latlong_dialog, relatorio_campo_dialog, conversao_datum_dialog, kml_para_shapefile_dialog, gerador_kml_dialog
from ui.tecnicos_dialogs import cadastrar_tecnico_dialog, ver_tecnicos_dialog
from ui.modelos_dialogs import modelos_dialog
from services.agenda import is_connected
from services.auth import current_user_perfil
from services.acesso import has_access

FILTERS = [
    ("all",     "#64748B", "grid_view",      "Tudo"),
    ("cad",     "#FBBF24", "architecture",   "CAD / DWG"),
    ("pdf",     "#F87171", "picture_as_pdf", "PDF"),
    ("office",  "#60A5FA", "description",    "Office"),
    ("image",   "#C4B5FD", "image",          "Imagens"),
    ("gis",     "#34D399", "map",            "GIS / Mapas"),
    ("archive", "#FDE68A", "folder_zip",     "ZIP / RAR"),
]


def render_sidebar(state, on_filter, on_buscar_cliente, on_cadastrar_cliente=None) -> None:
    active_label = next((lb for fid, _, _, lb in FILTERS if fid == state.filter), "Tudo")

    with ui.element("nav").classes("dmc-sidebar"):
        # ── Tipo de arquivo ──────────────────────────────────────────
        hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
            "border-bottom:1px solid var(--dmc-b1);flex-shrink:0;justify-content:space-between;width:100%;"
        )
        with hdr:
            ui.html(
                f'<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                f'letter-spacing:.15em;text-transform:uppercase">Tipo de arquivo'
                f'<span id="sb-lbl" style="color:var(--dmc-green);font-weight:600;'
                f'margin-left:6px;letter-spacing:.04em">{active_label}</span></span>'
            )
            ui.html(
                '<span id="sb-arrow" class="material-icons" '
                'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                'expand_more</span>'
            )
        hdr.on("click", lambda: ui.run_javascript("sbToggle()"))

        menu = ui.element("div").style(
            "flex-shrink:0;overflow:hidden;transition:max-height .28s ease;max-height:0;"
        ).props('id="sb-menu"')
        with menu:
            with ui.element("div").style("padding:6px 0 4px"):
                for fid, color, icon, label in FILTERS:
                    active = state.filter == fid
                    extra = " active" if active else ""
                    b = ui.element("button").classes(f"dmc-sidebar-item{extra}")
                    with b:
                        ui.html(
                            f'<span class="dmc-dot" style="background:{color}"></span>'
                        )
                        ui.html(f"<span>{label}</span>")
                    b.on("click", lambda f=fid, lb=label: [
                        on_filter(f),
                        ui.run_javascript(f'sbClose("{lb}")')
                    ])

        # ── Seções scrolláveis ────────────────────────────────────────
        with ui.element("div").classes("dmc-sidebar-scroll").style("flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;"):

            # ── Clientes ──────────────────────────────────────────────
            with ui.element("div").style(
                "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
            ):
                cl_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                    "justify-content:space-between;width:100%;"
                )
                with cl_hdr:
                    ui.html(
                        '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.15em;text-transform:uppercase">Clientes</span>'
                    )
                    ui.html(
                        '<span id="cl-arrow" class="material-icons" '
                        'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                        'expand_more</span>'
                    )
                cl_hdr.on("click", lambda: ui.run_javascript("clToggle()"))

                cl_menu = ui.element("div").style(
                    "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                ).props('id="cl-menu"')

                _cadastrar_fn = on_cadastrar_cliente if on_cadastrar_cliente else lambda: ui.navigate.to("/cliente/cadastrar")
                _CLIENTE_BTNS = [
                    ("person_add", "#4ADE80", "Cadastrar Cliente",  _cadastrar_fn),
                    ("search",     "#60A5FA", "Procurar Cliente",   lambda: on_buscar_cliente("nome")),
                    ("phone",      "#FBBF24", "Procurar Telefone",  lambda: on_buscar_cliente("telefone")),
                    ("badge",      "#C4B5FD", "Procurar CPF/CNPJ",  lambda: on_buscar_cliente("cpf")),
                ]
                with cl_menu:
                    with ui.element("div").style("padding:4px 0 8px"):
                        for icon, color, label, fn in _CLIENTE_BTNS:
                            b = ui.element("button").classes("dmc-sidebar-item")
                            with b:
                                ui.html(
                                    f'<span class="material-icons" '
                                    f'style="font-size:15px;color:{color};flex-shrink:0">{icon}</span>'
                                )
                                ui.html(f"<span>{label}</span>")
                            b.on("click", fn)

            # ── Agenda Google ──────────────────────────────────────────
            with ui.element("div").style(
                "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
            ):
                ag_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                    "justify-content:space-between;width:100%;"
                )
                with ag_hdr:
                    with ui.element("div").style("display:flex;align-items:center;gap:7px"):
                        ui.html(
                            '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                            'letter-spacing:.15em;text-transform:uppercase">Agenda</span>'
                        )
                        dot_color = "#4ADE80" if is_connected() else "#374F37"
                        dot_title = "Conectado ao Google" if is_connected() else "Não conectado"
                        ui.html(
                            f'<span title="{dot_title}" style="'
                            f'width:6px;height:6px;border-radius:50%;'
                            f'background:{dot_color};display:inline-block;flex-shrink:0"></span>'
                        )
                    ui.html(
                        '<span id="ag-arrow" class="material-icons" '
                        'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                        'expand_more</span>'
                    )
                ag_hdr.on("click", lambda: ui.run_javascript("agToggle()"))

                ag_menu = ui.element("div").style(
                    "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                ).props('id="ag-menu"')

                _AGENDA_BTNS = [
                    ("calendar_month", "#FBBF24", "Ver Agenda",      ver_agenda_dialog),
                    ("add_circle",     "#4ADE80", "Novo Evento",     novo_evento_dialog),
                    ("link",           "#60A5FA", "Conectar Google", conectar_agenda_dialog),
                ]
                with ag_menu:
                    with ui.element("div").style("padding:4px 0 8px"):
                        for icon, color, label, fn in _AGENDA_BTNS:
                            b = ui.element("button").classes("dmc-sidebar-item")
                            with b:
                                ui.html(
                                    f'<span class="material-icons" '
                                    f'style="font-size:15px;color:{color};flex-shrink:0">{icon}</span>'
                                )
                                ui.html(f"<span>{label}</span>")
                            b.on("click", fn)

            # ── Obras ─────────────────────────────────────────────────
            with ui.element("div").style(
                "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
            ):
                ob_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                    "justify-content:space-between;width:100%;"
                )
                with ob_hdr:
                    ui.html(
                        '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.15em;text-transform:uppercase">Obras</span>'
                    )
                    ui.html(
                        '<span id="ob-arrow" class="material-icons" '
                        'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                        'expand_more</span>'
                    )
                ob_hdr.on("click", lambda: ui.run_javascript("obToggle()"))

                ob_menu = ui.element("div").style(
                    "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                ).props('id="ob-menu"')

                _OBRA_BTNS = [
                    ("add_circle",  "#4ADE80", "Nova Obra",    nova_obra_dialog),
                    ("engineering", "#60A5FA", "Ver Obras",    ver_obras_dialog),
                ]
                with ob_menu:
                    with ui.element("div").style("padding:4px 0 8px"):
                        for icon, color, label, fn in _OBRA_BTNS:
                            b = ui.element("button").classes("dmc-sidebar-item")
                            with b:
                                ui.html(
                                    f'<span class="material-icons" '
                                    f'style="font-size:15px;color:{color};flex-shrink:0">{icon}</span>'
                                )
                                ui.html(f"<span>{label}</span>")
                            b.on("click", fn)

            # ── Administrativo ────────────────────────────────────────
            with ui.element("div").style(
                "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
            ):
                adm_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                    "justify-content:space-between;width:100%;"
                )
                with adm_hdr:
                    ui.html(
                        '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.15em;text-transform:uppercase">Administrativo</span>'
                    )
                    ui.html(
                        '<span id="adm-arrow" class="material-icons" '
                        'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                        'expand_more</span>'
                    )
                adm_hdr.on("click", lambda: ui.run_javascript("admToggle()"))

                adm_menu = ui.element("div").style(
                    "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                ).props('id="adm-menu"')

                with adm_menu:
                    with ui.element("div").style("padding:4px 0 8px"):
                        # Registros
                        ui.html(
                            '<div style="padding:8px 14px 4px;font:9px var(--dmc-mono);'
                            'color:var(--dmc-muted2);letter-spacing:.18em;text-transform:uppercase;'
                            'opacity:.7">Registros</div>'
                        )
                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#FBBF24;flex-shrink:0">today</span>')
                            ui.html("<span>Agenda de Campo</span>")
                        b.on("click", agenda_campo_dialog)

                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#4ADE80;flex-shrink:0">assignment</span>')
                            ui.html("<span>Registro de Campo</span>")
                        b.on("click", lambda: ui.run_javascript("window.open('/campo','_blank','noopener,noreferrer')"))

                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#60A5FA;flex-shrink:0">history</span>')
                            ui.html("<span>Histórico de Checkin/Out</span>")
                        b.on("click", historico_dialog)

                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#FBBF24;flex-shrink:0">summarize</span>')
                            ui.html("<span>Relatório de Campo</span>")
                        b.on("click", relatorio_campo_dialog)

                        # Acessos — só exibe se o perfil tiver permissão
                        _perfil = current_user_perfil()
                        _pode_contas = has_access(_perfil, "adm_gestao_contas")
                        _pode_acesso = has_access(_perfil, "adm_config_acesso")
                        if _pode_contas or _pode_acesso:
                            ui.html(
                                '<div style="padding:8px 14px 4px;font:9px var(--dmc-mono);'
                                'color:var(--dmc-muted2);letter-spacing:.18em;text-transform:uppercase;'
                                'opacity:.7;border-top:1px solid var(--dmc-b1);margin-top:4px">Acessos</div>'
                            )
                        if _pode_contas:
                            b = ui.element("button").classes("dmc-sidebar-item")
                            with b:
                                ui.html('<span class="material-icons" style="font-size:15px;color:#4ADE80;flex-shrink:0">manage_accounts</span>')
                                ui.html("<span>Gestão de Contas</span>")
                            b.on("click", lambda: ui.run_javascript("window.open('/contas','_blank','noopener,noreferrer')"))

                        if _pode_acesso:
                            b = ui.element("button").classes("dmc-sidebar-item")
                            with b:
                                ui.html('<span class="material-icons" style="font-size:15px;color:#C4B5FD;flex-shrink:0">security</span>')
                                ui.html("<span>Configuração de Acesso</span>")
                            b.on("click", lambda: ui.run_javascript("window.open('/acesso','_blank','noopener,noreferrer')"))

                        # Técnicos Cadastrados
                        ui.html(
                            '<div style="padding:8px 14px 4px;font:9px var(--dmc-mono);'
                            'color:var(--dmc-muted2);letter-spacing:.18em;text-transform:uppercase;'
                            'opacity:.7;border-top:1px solid var(--dmc-b1);margin-top:4px">Técnicos Cadastrados</div>'
                        )
                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#4ADE80;flex-shrink:0">person_add</span>')
                            ui.html("<span>Cadastrar Técnico</span>")
                        b.on("click", cadastrar_tecnico_dialog)

                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#60A5FA;flex-shrink:0">engineering</span>')
                            ui.html("<span>Ver Técnicos</span>")
                        b.on("click", ver_tecnicos_dialog)

                        # Modelos de Documento
                        ui.html(
                            '<div style="padding:8px 14px 4px;font:9px var(--dmc-mono);'
                            'color:var(--dmc-muted2);letter-spacing:.18em;text-transform:uppercase;'
                            'opacity:.7;border-top:1px solid var(--dmc-b1);margin-top:4px">Documentos</div>'
                        )
                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#60A5FA;flex-shrink:0">folder_special</span>')
                            ui.html("<span>Modelos de Documento</span>")
                        b.on("click", modelos_dialog)

            # ── Log de Atividades ─────────────────────────────────────
            if has_access(current_user_perfil(), "adm_log"):
                with ui.element("div").style(
                    "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
                ):
                    lg_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                        "justify-content:space-between;width:100%;"
                    )
                    with lg_hdr:
                        ui.html(
                            '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                            'letter-spacing:.15em;text-transform:uppercase">Log</span>'
                        )
                        ui.html(
                            '<span id="lg-arrow" class="material-icons" '
                            'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                            'expand_more</span>'
                        )
                    lg_hdr.on("click", lambda: ui.run_javascript("lgToggle()"))

                    lg_menu = ui.element("div").style(
                        "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                    ).props('id="lg-menu"')

                    with lg_menu:
                        with ui.element("div").style("padding:4px 0 8px"):
                            b = ui.element("button").classes("dmc-sidebar-item")
                            with b:
                                ui.html('<span class="material-icons" style="font-size:15px;color:#60A5FA;flex-shrink:0">history</span>')
                                ui.html("<span>Log de Atividades</span>")
                            b.on("click", lambda: ui.run_javascript("window.open('/log','_blank','noopener,noreferrer')"))

            # ── Processamento ─────────────────────────────────────────
            with ui.element("div").style(
                "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
            ):
                pr_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                    "justify-content:space-between;width:100%;"
                )
                with pr_hdr:
                    ui.html(
                        '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.15em;text-transform:uppercase">Processamento</span>'
                    )
                    ui.html(
                        '<span id="pr-arrow" class="material-icons" '
                        'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                        'expand_more</span>'
                    )
                pr_hdr.on("click", lambda: ui.run_javascript("prToggle()"))

                pr_menu = ui.element("div").style(
                    "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                ).props('id="pr-menu"')

                with pr_menu:
                    with ui.element("div").style("padding:4px 0 8px"):
                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#60A5FA;flex-shrink:0">explore</span>')
                            ui.html("<span>Norte Magnético</span>")
                        b.on("click", norte_magnetico_dialog)

                        b2 = ui.element("button").classes("dmc-sidebar-item")
                        with b2:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#4ADE80;flex-shrink:0">terrain</span>')
                            ui.html("<span>Processamento de Campo</span>")
                        b2.on("click", processamento_campo_dialog)

                        b3 = ui.element("button").classes("dmc-sidebar-item")
                        with b3:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#A78BFA;flex-shrink:0">my_location</span>')
                            ui.html("<span>Campo LatLon → Plano Local</span>")
                        b3.on("click", processamento_campo_latlong_dialog)

                        b4 = ui.element("button").classes("dmc-sidebar-item")
                        with b4:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#06B6D4;flex-shrink:0">compare_arrows</span>')
                            ui.html("<span>Conversão de Datum</span>")
                        b4.on("click", conversao_datum_dialog)

                        b5 = ui.element("button").classes("dmc-sidebar-item")
                        with b5:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#34D399;flex-shrink:0">map</span>')
                            ui.html("<span>KML/KMZ → Shapefile</span>")
                        b5.on("click", kml_para_shapefile_dialog)

                        b6 = ui.element("button").classes("dmc-sidebar-item")
                        with b6:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#FBBF24;flex-shrink:0">place</span>')
                            ui.html("<span>Gerador de KML</span>")
                        b6.on("click", gerador_kml_dialog)

            # ── Financeiro ────────────────────────────────────────────
            with ui.element("div").style(
                "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
            ):
                fin_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                    "justify-content:space-between;width:100%;"
                )
                with fin_hdr:
                    ui.html(
                        '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.15em;text-transform:uppercase">Financeiro</span>'
                    )
                    ui.html(
                        '<span id="fin-arrow" class="material-icons" '
                        'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                        'expand_more</span>'
                    )
                fin_hdr.on("click", lambda: ui.run_javascript("finToggle()"))

                fin_menu = ui.element("div").style(
                    "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                ).props('id="fin-menu"')

                with fin_menu:
                    with ui.element("div").style("padding:4px 0 8px"):
                        b = ui.element("button").classes("dmc-sidebar-item")
                        with b:
                            ui.html('<span class="material-icons" style="font-size:15px;color:#4ADE80;flex-shrink:0">receipt_long</span>')
                            ui.html("<span>NFS-e / Financeiro</span>")
                        b.on("click", lambda: ui.run_javascript("window.open('/financeiro','_blank','noopener,noreferrer')"))

            # ── Links Rápidos ──────────────────────────────────────────
            with ui.element("div").style(
                "border-top:1px solid var(--dmc-b1);padding-top:4px;margin-top:4px;"
            ):
                lk_hdr = ui.element("button").classes("dmc-sidebar-toggle").style(
                    "justify-content:space-between;width:100%;"
                )
                with lk_hdr:
                    ui.html(
                        '<span style="font:10px var(--dmc-fm);color:var(--dmc-muted2);'
                        'letter-spacing:.15em;text-transform:uppercase">Links Rápidos</span>'
                    )
                    ui.html(
                        '<span id="lk-arrow" class="material-icons" '
                        'style="font-size:20px;color:var(--dmc-muted);transition:transform .25s">'
                        'expand_more</span>'
                    )
                lk_hdr.on("click", lambda: ui.run_javascript("lkToggle()"))

                lk_menu = ui.element("div").style(
                    "overflow:hidden;transition:max-height .28s ease;max-height:0;"
                ).props('id="lk-menu"')

                _LINKS = [
                    ("open_in_new",  "#FBBF24", "CFT-BR",                 "https://servicos.sinceti.net.br"),
                    ("map",          "#4ADE80", "SIG-RI",                 "https://mapa.onr.org.br/sigri/"),
                    ("location_city","#60A5FA", "Certidão Confrontantes", "https://geoportal.pmf.sc.gov.br/services/certidao-confrontantes"),
                    ("verified_user","#C4B5FD", "Assinatura Gov",         "https://sso.acesso.gov.br/login?client_id=assinador.iti.br&authorization_id=19daac7a1ea"),
                    ("grid_on",      "#F97316", "ProGrid / IBGE",         "https://www.ibge.gov.br/geociencias/informacoes-sobre-posicionamento-geodesico/servicos-para-posicionamento-geodesico/16312-progrid.html?=&t=processar-os-dados"),
                ]
                with lk_menu:
                    with ui.element("div").style("padding:4px 0 8px"):
                        for icon, color, label, url in _LINKS:
                            b = ui.element("button").classes("dmc-sidebar-item")
                            with b:
                                ui.html(
                                    f'<span class="material-icons" '
                                    f'style="font-size:15px;color:{color};flex-shrink:0">{icon}</span>'
                                )
                                ui.html(f"<span>{label}</span>")
                            b.on("click", lambda u=url: ui.run_javascript(
                                f"window.open({repr(u)},'_blank','noopener,noreferrer');"
                            ))
