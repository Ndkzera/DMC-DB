"""Diálogos de processamento — Norte Magnético e outras ferramentas."""

import base64
import io
import math
from datetime import date

from nicegui import ui

from config import CLIENTES_DIR


def _build_cliente_selector(state: dict) -> None:
    """Renderiza seletor inline de cliente. Atualiza state['cliente']."""
    from services.clientes import load_clientes

    wrap        = ui.element('div')
    results_area = ui.element('div').style(
        'border:1px solid var(--dmc-b1);border-radius:8px;'
        'overflow:hidden;margin-top:2px;'
    )

    def _render():
        wrap.clear()
        results_area.clear()
        c = state.get('cliente')
        if c:
            with wrap:
                with ui.element('div').style(
                    'display:flex;align-items:center;gap:10px;'
                    'background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.25);'
                    'border-radius:8px;padding:9px 12px;'
                ):
                    ui.html(
                        '<span class="material-icons" '
                        'style="font-size:16px;color:var(--dmc-green);flex-shrink:0">person</span>'
                        f'<span style="font:500 13px var(--dmc-fm);color:var(--dmc-text);flex:1">'
                        f'{c["nome"]}</span>'
                    )
                    clr = ui.element('button').style(
                        'background:none;border:none;cursor:pointer;padding:2px;'
                        'color:var(--dmc-muted2);display:flex;flex-shrink:0'
                    )
                    with clr:
                        ui.html('<span class="material-icons" style="font-size:18px">close</span>')
                    def _clear():
                        state['cliente'] = None
                        _render()
                    clr.on('click', _clear)
        else:
            with wrap:
                def _on_search(e):
                    q = (e.value or '').strip().lower()
                    results_area.clear()
                    if not q:
                        return
                    matches = [
                        cc for cc in load_clientes()
                        if q in cc.get('nome', '').lower()
                    ][:8]
                    if not matches:
                        return
                    with results_area:
                        for cc in matches:
                            card = ui.element('div').style(
                                'padding:9px 14px;cursor:pointer;'
                                'border-bottom:1px solid var(--dmc-b1);'
                                'transition:background .1s;'
                            )
                            with card:
                                ui.html(
                                    f'<span style="font:500 13px var(--dmc-fm);'
                                    f'color:var(--dmc-text)">{cc["nome"]}</span>'
                                    + (
                                        f'<span style="font:11px var(--dmc-mono);'
                                        f'color:var(--dmc-muted2);margin-left:10px">'
                                        f'{cc["cpf"]}</span>'
                                        if cc.get('cpf') else ''
                                    )
                                )
                            def _select(ccc=cc):
                                state['cliente'] = ccc
                                results_area.clear()
                                _render()
                            card.on('click', _select)

                ui.input(
                    placeholder='Buscar cliente pelo nome…',
                    on_change=_on_search,
                ).style('width:100%').props('outlined dense clearable')

    _render()


def _save_to_cliente(nome_cliente: str, filename: str, data: bytes) -> None:
    """Salva cópia do arquivo na pasta do cliente em #CLIENTES."""
    invalidos = set(r'\/:*?"<>|')
    safe = ''.join(c for c in nome_cliente if c not in invalidos).strip()
    if not safe:
        return
    pasta = CLIENTES_DIR / safe
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / filename).write_bytes(data)

try:
    import pyproj
    _PYPROJ = True
except ImportError:
    _PYPROJ = False

try:
    import ezdxf
    _EZDXF = True
except ImportError:
    _EZDXF = False


# ── Utilitários ──────────────────────────────────────────────────────────

def _dms_dir(deg: float, pos_dir: str, neg_dir: str) -> str:
    """Graus decimais → D°MM'SS,SSSSS DIR (vírgula decimal, padrão BR)."""
    neg = deg < 0
    d = abs(deg)
    dd = int(d)
    mm = int((d - dd) * 60)
    ss = ((d - dd) * 60 - mm) * 60
    ss_str = f'{ss:08.5f}'.replace('.', ',')
    return f"{dd}°{mm:02d}'{ss_str}\" {neg_dir if neg else pos_dir}"


def _cm_dms(cm_deg: float) -> str:
    """Convergência em D°MM'SS,SS\" (vírgula decimal)."""
    neg = cm_deg < 0
    d = abs(cm_deg)
    dd = int(d)
    mm = int((d - dd) * 60)
    ss = ((d - dd) * 60 - mm) * 60
    ss_str = f'{ss:05.2f}'.replace('.', ',')
    sign = '-' if neg else '+'
    return f"{sign}{dd}°{mm:02d}'{ss_str}\""


def _mc_label(mc: int) -> str:
    if mc < 0:
        return f'{abs(mc)}° W'
    return f'{mc}° E'


def _utm_zone(mc: int) -> int:
    return int((mc + 180) / 6) + 1


def _compute(norte: float, leste: float, mc: int, hemisferio: str) -> dict:
    if not _PYPROJ:
        raise RuntimeError('pyproj não instalado')

    zone = _utm_zone(mc)
    south_param = '+south' if hemisferio.lower() == 'sul' else ''
    src = pyproj.CRS.from_proj4(
        f'+proj=utm +zone={zone} {south_param} +ellps=GRS80 +units=m +no_defs'
    )
    dst = pyproj.CRS.from_epsg(4674)  # SIRGAS2000 geográfico
    t = pyproj.Transformer.from_crs(src, dst, always_xy=True)
    lon, lat = t.transform(leste, norte)

    lat_r = math.radians(lat)
    dlon_r = math.radians(lon - mc)
    e2 = 0.00669437999014   # GRS80
    e_prime2 = e2 / (1 - e2)
    a = 6378137.0
    N_curv = a / math.sqrt(1 - e2 * math.sin(lat_r) ** 2)
    eta2 = e_prime2 * math.cos(lat_r) ** 2

    # Convergência Meridiana — série de Helmert (corresponde ao resultado do software)
    sl = math.sin(lat_r)
    cl = math.cos(lat_r)
    cm_rad = (dlon_r * sl
              + (dlon_r ** 3 / 3) * sl * cl ** 2 * (1 + 3 * eta2 + 2 * eta2 ** 2))
    cm_deg = math.degrees(cm_rad)

    # Fator de Escala K — 4ª ordem (corresponde ao resultado do software)
    k0 = 0.9996
    x = leste - 500000.0
    t_val = math.tan(lat_r)
    K = k0 * (
        1
        + x ** 2 * (1 + eta2) / (2 * N_curv ** 2)
        + x ** 4 * (5 + 6 * t_val ** 2 + eta2 * (1 + 4 * eta2) - 4 * eta2 ** 2)
        / (24 * N_curv ** 4)
    )

    return {
        'lat': lat,
        'lon': lon,
        'lat_dms': _dms_dir(lat, 'N', 'S'),
        'lon_dms': _dms_dir(lon, 'E', 'W'),
        'cm_deg': cm_deg,
        'cm_dms': _cm_dms(cm_deg),
        'K': K,
        'zone': zone,
    }


# ── DXF ──────────────────────────────────────────────────────────────────

def _arrowhead(msp, center, tip, size: float = 6.0):
    """Seta com cabeça aberta (estilo levantamento topográfico)."""
    dx = tip[0] - center[0]
    dy = tip[1] - center[1]
    ln = math.hypot(dx, dy)
    if ln == 0:
        return
    ux, uy = dx / ln, dy / ln   # direção unitária
    px, py = -uy, ux             # perpendicular

    b1 = (tip[0] - size * ux + size * 0.45 * px,
          tip[1] - size * uy + size * 0.45 * py)
    b2 = (tip[0] - size * ux - size * 0.45 * px,
          tip[1] - size * uy - size * 0.45 * py)
    msp.add_line(tip, b1)
    msp.add_line(tip, b2)


def _gen_dxf(nome: str, norte: float, leste: float,
             mc: int, hemisferio: str, data_str: str, result: dict) -> bytes:
    doc = ezdxf.new('R2010')
    doc.header['$MEASUREMENT'] = 1  # métrico

    # Fonte TrueType para suporte a caracteres acentuados
    txt_style = 'Standard'
    try:
        doc.styles.add('ARIAL_NM', font='arial.ttf')
        txt_style = 'ARIAL_NM'
    except Exception:
        pass

    msp = doc.modelspace()

    W, H = 310.0, 165.0

    # Borda externa
    msp.add_lwpolyline(
        [(0, 0), (W, 0), (W, H), (0, H)], close=True,
        dxfattribs={'lineweight': 50}
    )

    # ── Setas: NQ e NG cruzam-se no ponto central ────────────
    # O ângulo visual é fixo (8°) para legibilidade — o valor real fica no texto.
    # NQ = Norte Quadrícula (esquerda), NG = Norte Geográfico (direita).
    cx, cy = 42.0, 80.0     # ponto de cruzamento
    alen   = 72.0            # comprimento acima do cruzamento
    tlen   = 32.0            # comprimento abaixo do cruzamento (cauda)
    vis_a  = math.radians(10.0)  # ângulo visual de cada seta em relação à vertical

    # NQ: sobe para a esquerda  → ângulo de +vis_a à esquerda da vertical
    #     (sentido anti-horário a partir de cima = para a esquerda em DXF)
    nq_dx = -math.sin(vis_a)
    nq_dy =  math.cos(vis_a)
    nq_tip  = (cx + alen * nq_dx, cy + alen * nq_dy)
    nq_tail = (cx - tlen * nq_dx, cy - tlen * nq_dy)

    # NG: sobe para a direita
    ng_dx =  math.sin(vis_a)
    ng_dy =  math.cos(vis_a)
    ng_tip  = (cx + alen * ng_dx, cy + alen * ng_dy)
    ng_tail = (cx - tlen * ng_dx, cy - tlen * ng_dy)

    # Linhas
    msp.add_line(nq_tail, nq_tip)
    msp.add_line(ng_tail, ng_tip)

    # Cabeças de seta
    _arrowhead(msp, (cx, cy), nq_tip, size=6.0)
    _arrowhead(msp, (cx, cy), ng_tip, size=6.0)

    # Rótulos das setas
    def _txt(text, insert, height=4.5):
        msp.add_text(text, dxfattribs={'height': height, 'insert': insert, 'style': txt_style})

    _txt('NQ', (nq_tip[0] - 13, nq_tip[1] + 2), height=5.0)
    _txt('NG', (ng_tip[0] + 2,  ng_tip[1] + 2), height=5.0)

    # Linha horizontal onde as caudas se afastam (ao nível da cauda)
    tail_y = cy - tlen + 4
    msp.add_line((nq_tail[0] - 2, tail_y), (ng_tail[0] + 2, tail_y))

    # Linha divisória vertical setas / texto
    msp.add_line((82, 8), (82, H - 8), dxfattribs={'lineweight': 13})

    # ── Bloco de texto ───────────────────────────────────────
    tx = 90.0
    ty = H - 12.0
    lh = 11.5    # espaçamento entre linhas
    hs  = 4.8    # tamanho fonte
    hb  = 5.2    # tamanho fonte cabeçalho

    lines = [
        (hb, 'PROJECAO UNIVERSAL TRANSVERSA'),
        (hb, 'DE MERCATOR  -  UTM'),
        (hs, f'SGR  -  SIRGAS2000'),
        (hs, f'MC:  {_mc_label(mc)}'),
        (0,  ''),
        (hs, f'CM  {result["cm_dms"]}'),
        (hs, f'K:  {result["K"]:.8f}'),
        (0,  ''),
        (hs, f'VERTICE:  {nome}'),
        (hs, f'Lat:   {result["lat_dms"]}'),
        (hs, f'Long:  {result["lon_dms"]}'),
    ]

    # Linha horizontal abaixo de CM (underline)
    cm_line_y = ty - 4 * lh + 0.5
    msp.add_line((tx, cm_line_y), (tx + 145, cm_line_y))

    y = ty
    for h, text in lines:
        if h > 0 and text:
            msp.add_text(text, dxfattribs={'height': h, 'insert': (tx, y), 'style': txt_style})
        y -= lh

    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode('utf-8')


# ── Diálogo ──────────────────────────────────────────────────────────────

def norte_magnetico_dialog() -> None:
    _result: dict = {}
    _nm_state: dict = {'cliente': None, 'nome_arq': ''}

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(700px,97vw)!important;max-height:93vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        # ── Cabeçalho ────────────────────────────────────────
        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(96,165,250,.08);border:1px solid rgba(96,165,250,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#60A5FA">explore</span></div>'
            )
            with ui.element('div'):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Norte Magnético</div>')
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    'UTM → Geográfico · Convergência Meridiana · Fator de Escala</div>'
                )

        # ── Corpo ────────────────────────────────────────────
        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1'):

            # ── Nome do arquivo ───────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">'
                'Nome do Arquivo</div>'
            )
            with ui.element('div').style(
                'display:flex;align-items:stretch;height:40px;'
                'border:1px solid var(--dmc-b2);border-radius:8px;'
                'background:var(--dmc-bg);margin-bottom:6px;overflow:hidden;'
            ):
                ui.html(
                    '<span style="padding:0 14px;display:flex;align-items:center;'
                    'font:700 13px var(--dmc-mono);color:var(--dmc-text);'
                    'white-space:nowrap;background:var(--dmc-bg3);'
                    'border-right:1px solid var(--dmc-b1)">NM</span>'
                ).style('display:flex;align-self:stretch;flex-shrink:0')
                ui.input(
                    placeholder=' ',
                    on_change=lambda e: _nm_state.update({'nome_arq': e.value or ''}),
                ).props('borderless dense').style('flex:1;min-width:0')
            ui.html(
                '<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:16px">'
                'O arquivo será gerado como <b>NM  .dxf</b> (exemplo)</div>'
            )

            # ── Vincular cliente ─────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;'
                'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-bottom:10px">'
                'Vincular Cliente <span style="font-weight:400;text-transform:none;'
                'letter-spacing:0">(opcional)</span></div>'
            )
            _build_cliente_selector(_nm_state)

            ui.html('<div style="border-top:1px solid var(--dmc-b1);margin:16px 0 14px"></div>')

            # Seção 1: Configuração
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">'
                'Configuração UTM</div>'
            )
            with ui.element('div').style(
                'display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px'
            ):
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Datum</label>')
                    ui.html(
                        '<input class="dmc-input" value="SIRGAS2000" readonly '
                        'style="width:100%;opacity:.6;cursor:default">'
                    )
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Meridiano Central (°)</label>')
                    ui.html(
                        '<input class="dmc-input" id="nm-mc" type="number" value="-51" '
                        'step="3" style="width:100%" placeholder="-51">'
                    )

            with ui.element('div').style(
                'display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px'
            ):
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Hemisfério</label>')
                    ui.html(
                        '<select class="dmc-input" id="nm-hemi" style="width:100%">'
                        '<option value="Sul" selected>Sul</option>'
                        '<option value="Norte">Norte</option>'
                        '</select>'
                    )
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Data</label>')
                    today = date.today().strftime('%Y-%m-%d')
                    ui.html(
                        f'<input class="dmc-input" id="nm-data" type="date" '
                        f'value="{today}" style="width:100%">'
                    )

            # Seção 2: Dados
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;'
                'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-bottom:10px">'
                'Dados Norte Magnético</div>'
            )

            with ui.element('div').style('margin-bottom:12px'):
                ui.html('<label class="dmc-label">Nome do Vértice</label>')
                ui.html(
                    '<input class="dmc-input" id="nm-nome" placeholder="Ex: V-1" '
                    'style="width:100%">'
                )

            with ui.element('div').style(
                'display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px'
            ):
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Norte (m)</label>')
                    ui.html(
                        '<input class="dmc-input" id="nm-norte" type="number" step="0.001" '
                        'placeholder="Ex: Y.YYY.YYY,YYYY" style="width:100%">'
                    )
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Leste (m)</label>')
                    ui.html(
                        '<input class="dmc-input" id="nm-leste" type="number" step="0.001" '
                        'placeholder="Ex: XXX.XXX,XXXX" style="width:100%">'
                    )

            # Botão Calcular
            async def _calcular():
                try:
                    vals = await ui.run_javascript('''({
                        mc:    parseFloat(document.getElementById('nm-mc')?.value),
                        hemi:  document.getElementById('nm-hemi')?.value,
                        data:  document.getElementById('nm-data')?.value,
                        nome:  document.getElementById('nm-nome')?.value?.trim(),
                        norte: parseFloat(document.getElementById('nm-norte')?.value),
                        leste: parseFloat(document.getElementById('nm-leste')?.value),
                    })''')

                    if not vals or any(
                        v == '' or (isinstance(v, float) and math.isnan(v))
                        for v in [vals.get('norte'), vals.get('leste')]
                    ):
                        ui.notify('Preencha Norte e Leste.', type='warning')
                        return

                    res = _compute(
                        float(vals['norte']),
                        float(vals['leste']),
                        int(vals['mc']),
                        vals['hemi'],
                    )
                    _result.clear()
                    _result.update({
                        **res,
                        'nome': vals['nome'] or 'V-1',
                        'mc': int(vals['mc']),
                        'hemi': vals['hemi'],
                        'data': vals['data'],
                        'norte': float(vals['norte']),
                        'leste': float(vals['leste']),
                    })

                    res_container.clear()
                    with res_container:
                        _build_result_panel(res, vals)

                    res_container.style('display:block')
                    btn_dxf.enable()
                    ui.notify('Calculado com sucesso!', type='positive')

                except Exception as exc:
                    ui.notify(f'Erro: {exc}', type='negative')

            with ui.element('div').style('display:flex;justify-content:center;margin-bottom:16px'):
                ui.button('Calcular', on_click=_calcular).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary')

            # Painel de resultados (oculto inicialmente)
            res_container = ui.element('div').style('display:none')

        # ── Rodapé ───────────────────────────────────────────
        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0'
        ):
            ui.button('Fechar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _download_dxf():
                if not _result:
                    return
                try:
                    dxf_bytes = _gen_dxf(
                        _result['nome'],
                        _result['norte'],
                        _result['leste'],
                        _result['mc'],
                        _result['hemi'],
                        _result['data'],
                        _result,
                    )
                    arq_sufixo = _nm_state.get('nome_arq', '').strip()
                    filename = f"NM {arq_sufixo}.dxf" if arq_sufixo else \
                               f"NM_{_result['nome'].replace('/', '-')}.dxf"

                    b64 = base64.b64encode(dxf_bytes).decode()
                    await ui.run_javascript(f'''
                        const a = document.createElement('a');
                        a.href = 'data:application/octet-stream;base64,{b64}';
                        a.download = {repr(filename)};
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    ''')

                    if _nm_state.get('cliente'):
                        nome_cli = _nm_state['cliente'].get('nome', '')
                        _save_to_cliente(nome_cli, filename, dxf_bytes)
                        ui.notify(f'Cópia salva na pasta de {nome_cli}', type='positive')

                except Exception as exc:
                    ui.notify(f'Erro ao gerar DXF: {exc}', type='negative')

            btn_dxf = ui.button('Download DXF', icon='download', on_click=_download_dxf).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary')
            btn_dxf.disable()

    dlg.open()


def _build_result_panel(res: dict, vals: dict) -> None:
    cm_color = '#60A5FA'
    k_color  = '#4ADE80'

    ui.html(
        '<div style="background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
        'border-radius:12px;padding:16px 20px;margin-bottom:4px">'

        '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
        'letter-spacing:.14em;text-transform:uppercase;margin-bottom:12px">'
        'Resultado</div>'

        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">'

        f'<div><div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">LATITUDE</div>'
        f'<div style="font:600 13px var(--dmc-fm);color:var(--dmc-text);margin-top:2px">'
        f'{res["lat_dms"]}</div></div>'

        f'<div><div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">LONGITUDE</div>'
        f'<div style="font:600 13px var(--dmc-fm);color:var(--dmc-text);margin-top:2px">'
        f'{res["lon_dms"]}</div></div>'

        f'<div><div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">CONVERGÊNCIA MERIDIANA (CM)</div>'
        f'<div style="font:600 13px var(--dmc-mono);color:{cm_color};margin-top:2px">'
        f'{res["cm_dms"]}</div></div>'

        f'<div><div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">FATOR DE ESCALA (K)</div>'
        f'<div style="font:600 13px var(--dmc-mono);color:{k_color};margin-top:2px">'
        f'{res["K"]:.8f}</div></div>'

        f'<div><div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">ZONA UTM</div>'
        f'<div style="font:600 13px var(--dmc-fm);color:var(--dmc-text);margin-top:2px">'
        f'{res["zone"]}{"S" if vals.get("hemi", "Sul") == "Sul" else "N"}</div></div>'

        f'<div><div style="font:10px var(--dmc-mono);color:var(--dmc-muted2)">MC</div>'
        f'<div style="font:600 13px var(--dmc-fm);color:var(--dmc-text);margin-top:2px">'
        f'{_mc_label(int(vals.get("mc", -51)))}</div></div>'

        '</div></div>'
    )


# ═══════════════════════════════════════════════════════════════════════════
# PROCESSAMENTO DE CAMPO
# ═══════════════════════════════════════════════════════════════════════════

def _to_float(v) -> float:
    """Converte valor com vírgula ou ponto decimal para float."""
    return float(str(v).strip().replace(',', '.'))


def _fmt_cota(v: float) -> str:
    """Formata cota com vírgula decimal (padrão BR)."""
    return f'{v:.4f}'.replace('.', ',')


def _parse_text(content: str) -> list[dict]:
    """Parseia texto colado (TSV/CSV) → lista de dicts."""
    pontos = []
    for raw in content.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        if '\t' in line:
            parts = line.split('\t')
        elif ';' in line:
            parts = line.split(';')
        else:
            continue
        if len(parts) < 4:  # mínimo: PONTO, DESC, NORTE, LESTE
            continue
        try:
            cota_raw = parts[4].strip() if len(parts) > 4 else ''
            pontos.append({
                'ponto': parts[0].strip(),
                'desc':  parts[1].strip(),
                'norte': _to_float(parts[2]),
                'leste': _to_float(parts[3]),
                'cota':  _to_float(cota_raw) if cota_raw else 0.0,
            })
        except (ValueError, IndexError):
            continue
    return pontos



_DEFAULT_COLORS = {
    'desc':    '#00FFFF',   # ciano
    'ponto':   '#FF0000',   # vermelho
    'circulo': '#00B050',   # verde
    'cota':    '#FFFF00',   # amarelo
}


def _hex_tc(h: str) -> int:
    """Hex HTML (#RRGGBB) → inteiro true_color DXF."""
    h = h.lstrip('#')
    return (int(h[0:2], 16) << 16) | (int(h[2:4], 16) << 8) | int(h[4:6], 16)


def _sanitize_layer(name: str) -> str:
    """Remove caracteres inválidos de nomes de layer DXF."""
    invalid = r'<>/\":;?*|=`'
    out = ''.join(c if c not in invalid else '_' for c in name)
    return out[:31] or '_LAYER'


_BLOCK_NAMES = {
    'circulo':   'SIMB_CIRCULO',
    'triangulo': 'SIMB_TRIANGULO',
    'quadrado':  'SIMB_QUADRADO',
    'x':         'SIMB_X',
    'mais':      'SIMB_MAIS',
}


def _draw_symbol(blk, r: float, color_tc: int, shape: str) -> None:
    """Desenha o símbolo do ponto no bloco, centrado em (0,0) com raio r."""
    attrs = {'layer': '_TG'}
    if shape == 'circulo':
        e = blk.add_circle((0, 0), radius=r, dxfattribs=attrs)
        e.dxf.true_color = color_tc
    elif shape == 'triangulo':
        pts = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
               for a in (90, 210, 330)]
        e = blk.add_lwpolyline(pts, close=True, dxfattribs=attrs)
        e.dxf.true_color = color_tc
    elif shape == 'quadrado':
        e = blk.add_lwpolyline([(-r, -r), (r, -r), (r, r), (-r, r)],
                               close=True, dxfattribs=attrs)
        e.dxf.true_color = color_tc
    elif shape == 'x':
        for start, end in [((-r, -r), (r, r)), ((-r, r), (r, -r))]:
            e = blk.add_line(start, end, dxfattribs=attrs)
            e.dxf.true_color = color_tc
    elif shape == 'mais':
        for start, end in [((-r, 0), (r, 0)), ((0, -r), (0, r))]:
            e = blk.add_line(start, end, dxfattribs=attrs)
            e.dxf.true_color = color_tc


def _gen_campo_dxf(
    pontos: list[dict],
    font_size: float = 1.5,
    layer_mode: str = 'single',
    colors: dict | None = None,
    symbol: str = 'circulo',
    show_desc: bool = True,
    show_cota: bool = True,
) -> bytes:
    """Gera um DXF dos ponto.

    layer_mode: 'single' → tudo em _TG | 'by_desc' → layer por descrição
    colors: dict com chaves 'desc','ponto','circulo','cota' em hex #RRGGBB
    """
    c = {**_DEFAULT_COLORS, **(colors or {})}

    doc = ezdxf.new('R2010')
    doc.header['$MEASUREMENT'] = 1

    # Fonte Arial — styles.add() exige font= como kwarg obrigatório
    style_name = 'Standard'
    try:
        doc.styles.add('ARIAL', font='arial.ttf')
        style_name = 'ARIAL'
    except Exception:
        pass

    # Layers
    doc.layers.add('_TG', dxfattribs={'color': 3})
    if layer_mode == 'by_desc':
        for p in pontos:
            lname = _sanitize_layer(p['desc']) if p['desc'] else '_TG'
            if not doc.layers.has_entry(lname):
                doc.layers.add(lname, dxfattribs={'color': 3})

    # ── Definição do bloco ───────────────────────────────────
    blk_name = _BLOCK_NAMES.get(symbol, 'SIMB_CIRCULO')
    blk = doc.blocks.new(blk_name)

    _draw_symbol(blk, font_size * 0.25, _hex_tc(c['circulo']), symbol)

    dy_desc  =  font_size * 1.6
    dy_ponto =  font_size * 0.2
    dy_cota  = -font_size * 1.6
    dx       =  font_size * 0.5

    def _attdef(tag, dy):
        ad = blk.add_attdef(tag, (dx, dy), height=font_size,
                            dxfattribs={'layer': '_TG', 'style': style_name})
        return ad

    if show_desc:
        ad_desc = _attdef('DESC', dy_desc)
        ad_desc.dxf.true_color = _hex_tc(c['desc'])
    ad_ponto = _attdef('PONTO', dy_ponto)
    ad_ponto.dxf.true_color = _hex_tc(c['ponto'])
    if show_cota:
        ad_cota = _attdef('COTA', dy_cota)
        ad_cota.dxf.true_color = _hex_tc(c['cota'])

    msp = doc.modelspace()

    for p in pontos:
        if layer_mode == 'by_desc' and p['desc']:
            layer = _sanitize_layer(p['desc'])
        else:
            layer = '_TG'
        ref = msp.add_blockref(
            blk_name,
            insert=(p['leste'], p['norte'], p['cota']),
            dxfattribs={'layer': layer},
        )
        attribs = {'PONTO': p['ponto']}
        if show_desc:
            attribs['DESC'] = p['desc']
        if show_cota:
            attribs['COTA'] = _fmt_cota(p['cota'])
        ref.add_auto_attribs(attribs)

    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode('utf-8')


# ── Diálogo ──────────────────────────────────────────────────────────────

def processamento_campo_dialog() -> None:
    _pontos: list[dict] = []
    _cm_state: dict = {'cliente': None, 'nome_arq': ''}

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(860px,97vw)!important;max-height:94vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        # ── Cabeçalho ────────────────────────────────────────
        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(74,222,128,.08);border:1px solid rgba(74,222,128,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:var(--dmc-green)">terrain</span></div>'
            )
            with ui.element('div'):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Processamento de Campo</div>')
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    'Importa pontos (PONTO · DESC · NORTE · LESTE · COTA) e gera DXF com bloco selecionado</div>'
                )

        # ── Corpo ────────────────────────────────────────────
        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1;min-height:0'):

            # ── Entrada de dados ──────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px">'
                'Entrada de dados</div>'
            )

            # Textarea para paste — HTML nativo para evitar problemas de largura do wrapper Quasar
            ui.html(
                '<label class="dmc-label">Cole aqui os dados do Excel ou CSV</label>'
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);margin-bottom:6px">'
                'Colunas: PONTO · DESCRIÇÃO · NORTE · LESTE · COTA &nbsp;'
                '<span style="opacity:.6">(descrição e cota podem ficar em branco)</span></div>'
            )
            ui.html(
                '<textarea id="cm-paste-area" rows="7" '
                'placeholder="1&#9;Marco 01&#9;7.483.250,1234&#9;531.870,5678&#9;948,3210&#10;'
                '2&#9;Marco 02&#9;7.483.251,0000&#9;531.871,0000&#9;&#10;'
                '3&#9;&#9;7.483.252,0000&#9;531.872,0000" '
                'style="width:100%;box-sizing:border-box;resize:vertical;'
                'font:12px var(--dmc-mono);color:var(--dmc-text);'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:10px 12px;outline:none;'
                'min-height:120px;"></textarea>'
            )

            with ui.element('div').style('display:flex;justify-content:center;margin-top:12px;margin-bottom:16px'):
                async def _processar():
                    text = await ui.run_javascript(
                        "document.getElementById('cm-paste-area')?.value || ''"
                    )
                    if not text or not text.strip():
                        ui.notify('Cole os dados ou faça upload de um arquivo.', type='warning')
                        return
                    try:
                        pts = _parse_text(text)
                        if not pts:
                            ui.notify('Nenhum ponto reconhecido. Verifique o formato.', type='warning')
                            return
                        _pontos.clear()
                        _pontos.extend(pts)
                        _refresh_preview()
                        ui.notify(f'{len(pts)} pontos processados.', type='positive')
                    except Exception as exc:
                        ui.notify(f'Erro: {exc}', type='negative')

                ui.button('Processar', icon='play_arrow', on_click=_processar).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary')

            # ── Preview ───────────────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;'
                'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-bottom:8px">'
                'Pré-visualização</div>'
            )

            preview_container = ui.element('div')

            def _refresh_preview():
                preview_container.clear()
                with preview_container:
                    if not _pontos:
                        ui.html(
                            '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);'
                            'padding:12px;text-align:center">Nenhum dado carregado.</div>'
                        )
                        btn_dxf.disable()
                        return

                    # Header count
                    ui.html(
                        f'<div style="font:12px var(--dmc-mono);color:var(--dmc-green);'
                        f'margin-bottom:8px">{len(_pontos)} pontos</div>'
                    )

                    # Table
                    cols = [
                        ('PONTO', '60px'), ('DESC', '160px'),
                        ('NORTE', '130px'), ('LESTE', '130px'), ('COTA', '100px'),
                    ]
                    hdr = ''.join(
                        f'<th style="padding:6px 10px;text-align:left;'
                        f'font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                        f'letter-spacing:.1em;text-transform:uppercase;width:{w}">{c}</th>'
                        for c, w in cols
                    )
                    rows_html = ''
                    for i, p in enumerate(_pontos):
                        bg = 'var(--dmc-bg3)' if i % 2 == 0 else 'var(--dmc-bg2)'
                        rows_html += (
                            f'<tr style="background:{bg}">'
                            f'<td style="padding:5px 10px;font:12px var(--dmc-mono);color:var(--dmc-green)">'
                            f'{p["ponto"]}</td>'
                            f'<td style="padding:5px 10px;font:12px var(--dmc-fm);color:var(--dmc-text)">'
                            f'{p["desc"]}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                            f'{p["norte"]:.4f}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                            f'{p["leste"]:.4f}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:var(--dmc-muted2)">'
                            f'{p["cota"]:.4f}</td>'
                            f'</tr>'
                        )

                    ui.html(
                        f'<div style="overflow-x:auto;border:1px solid var(--dmc-b1);'
                        f'border-radius:8px;overflow:hidden;max-height:260px;overflow-y:auto">'
                        f'<table style="width:100%;border-collapse:collapse">'
                        f'<thead><tr style="border-bottom:1px solid var(--dmc-b1)">{hdr}</tr></thead>'
                        f'<tbody>{rows_html}</tbody>'
                        f'</table></div>'
                    )
                    btn_dxf.enable()

            # ── Configuração DXF ──────────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;'
                'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-top:4px;margin-bottom:10px">'
                'Configuração DXF</div>'
            )

            # Nome do arquivo
            ui.html('<label class="dmc-label">Nome do Arquivo</label>')
            with ui.element('div').style(
                'display:flex;align-items:stretch;height:40px;'
                'border:1px solid var(--dmc-b2);border-radius:8px;'
                'background:var(--dmc-bg);margin-bottom:6px;overflow:hidden;'
            ):
                ui.html(
                    '<span style="padding:0 14px;display:flex;align-items:center;'
                    'font:700 13px var(--dmc-mono);color:var(--dmc-text);'
                    'white-space:nowrap;background:var(--dmc-bg3);'
                    'border-right:1px solid var(--dmc-b1)">LEV</span>'
                ).style('display:flex;align-self:stretch;flex-shrink:0')
                ui.input(
                    placeholder=' ',
                    on_change=lambda e: _cm_state.update({'nome_arq': e.value or ''}),
                ).props('borderless dense').style('flex:1;min-width:0')
            ui.html(
                '<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:14px">'
                'O arquivo será gerado como <b>LEV  .dxf</b> (exemplo)</div>'
            )

            # Vincular cliente
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">'
                'Vincular Cliente <span style="font-weight:400;text-transform:none;'
                'letter-spacing:0">(opcional)</span></div>'
            )
            _build_cliente_selector(_cm_state)
            ui.html('<div style="margin-bottom:14px"></div>')

            with ui.element('div').style(
                'display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px'
            ):
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Tamanho da fonte (m)</label>')
                    ui.html(
                        '<input class="dmc-input" id="cm-font" type="number" '
                        'value="1.0" step="0.1" min="0.1" max="50" style="width:100%">'
                    )
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Layers</label>')
                    ui.html(
                        '<select class="dmc-input" id="cm-layer" style="width:100%">'
                        '<option value="single" selected>Único (_TG)</option>'
                        '<option value="by_desc">Por descrição</option>'
                        '</select>'
                    )

            # Toggles de exibição
            ui.html(
                '<div style="display:flex;gap:20px;margin-bottom:14px;flex-wrap:wrap">'

                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:12px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="checkbox" id="cm-show-desc" checked '
                'style="width:15px;height:15px;accent-color:var(--dmc-green);cursor:pointer">'
                'Exibir Descrição no DXF</label>'

                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:12px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="checkbox" id="cm-show-cota" checked '
                'style="width:15px;height:15px;accent-color:var(--dmc-green);cursor:pointer">'
                'Exibir Cota no DXF</label>'

                '</div>'
            )

            # Seletor de símbolo
            def _sym(val, label, svg_inner, checked=False):
                sel = 'border:2px solid #4ADE80;color:#4ADE80' if checked else 'border:2px solid rgba(255,255,255,0.08);color:#666'
                chk = ' checked' if checked else ''
                return (
                    f'<label style="display:flex;flex-direction:column;align-items:center;gap:5px;'
                    f'padding:9px 13px;border-radius:10px;cursor:pointer;background:var(--dmc-bg3);'
                    f'{sel};transition:border-color .15s,color .15s;user-select:none">'
                    f'<input type="radio" name="cm-symbol" value="{val}"{chk} style="display:none">'
                    f'<svg width="30" height="30" viewBox="0 0 32 32" fill="none" '
                    f'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
                    f'style="pointer-events:none">{svg_inner}</svg>'
                    f'<span style="font:10px var(--dmc-mono)">{label}</span>'
                    f'</label>'
                )

            ui.html(
                '<div class="dmc-label" style="margin-bottom:8px">Símbolo do ponto</div>'
                '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">'
                + _sym('circulo',   'Círculo',   '<circle cx="16" cy="16" r="10"/>', checked=True)
                + _sym('triangulo', 'Triângulo', '<polygon points="16,3 1,29 31,29"/>')
                + _sym('quadrado',  'Quadrado',  '<rect x="3" y="3" width="26" height="26"/>')
                + _sym('x',        'X',          '<line x1="4" y1="4" x2="28" y2="28"/><line x1="28" y1="4" x2="4" y2="28"/>')
                + _sym('mais',     '+',          '<line x1="16" y1="3" x2="16" y2="29"/><line x1="3" y1="16" x2="29" y2="16"/>')
                + '</div>'
            )

            # Modo de cores
            ui.html(
                '<div style="margin-bottom:10px">'
                '<div class="dmc-label" style="margin-bottom:6px">Modo de cores</div>'
                '<label style="display:inline-flex;align-items:center;gap:6px;'
                'font:12px var(--dmc-fm);color:var(--dmc-text);margin-right:20px;cursor:pointer">'
                '<input type="radio" name="cm-color-mode" value="default" checked> Padrão</label>'
                '<label style="display:inline-flex;align-items:center;gap:6px;'
                'font:12px var(--dmc-fm);color:var(--dmc-text);cursor:pointer">'
                '<input type="radio" name="cm-color-mode" value="custom"> Personalizado</label>'
                '</div>'
            )

            # Paleta de cores (oculta por padrão)
            ui.html(
                '<div id="cm-custom-colors" style="'
                'display:none;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:4px">'

                # DESC
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="cm-c-desc" value="#00FFFF" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Descrição</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#00FFFF;margin-left:auto" id="cm-dot-desc"></span>'
                '</label>'

                # NOME
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="cm-c-ponto" value="#FF0000" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Nome do ponto</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#FF0000;margin-left:auto" id="cm-dot-ponto"></span>'
                '</label>'

                # CÍRCULO
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="cm-c-circ" value="#00B050" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Círculo</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#00B050;margin-left:auto" id="cm-dot-circ"></span>'
                '</label>'

                # COTA
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="cm-c-cota" value="#FFFF00" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Cota</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#FFFF00;margin-left:auto" id="cm-dot-cota"></span>'
                '</label>'

                '</div>'
            )

        # ── Rodapé ───────────────────────────────────────────
        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0'
        ):
            ui.button('Fechar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _download_dxf():
                if not _pontos:
                    ui.notify('Nenhum ponto para exportar.', type='warning')
                    return
                try:
                    cfg = await ui.run_javascript('''({
                        font_size:  parseFloat(document.getElementById('cm-font')?.value) || 1.5,
                        layer_mode: document.getElementById('cm-layer')?.value || 'single',
                        color_mode: (document.querySelector('input[name="cm-color-mode"]:checked')?.value) || 'default',
                        symbol:     (document.querySelector('input[name="cm-symbol"]:checked')?.value) || 'circulo',
                        desc:    document.getElementById('cm-c-desc')?.value  || '#00FFFF',
                        ponto:   document.getElementById('cm-c-ponto')?.value || '#FF0000',
                        circulo: document.getElementById('cm-c-circ')?.value  || '#00B050',
                        cota:    document.getElementById('cm-c-cota')?.value  || '#FFFF00',
                        show_desc: document.getElementById('cm-show-desc')?.checked ?? true,
                        show_cota: document.getElementById('cm-show-cota')?.checked ?? true,
                    })''')

                    colors = None
                    if cfg.get('color_mode') == 'custom':
                        colors = {
                            'desc':    cfg['desc'],
                            'ponto':   cfg['ponto'],
                            'circulo': cfg['circulo'],
                            'cota':    cfg['cota'],
                        }

                    dxf_bytes = _gen_campo_dxf(
                        _pontos,
                        font_size=float(cfg.get('font_size', 1.5)),
                        layer_mode=cfg.get('layer_mode', 'single'),
                        colors=colors,
                        symbol=cfg.get('symbol', 'circulo'),
                        show_desc=bool(cfg.get('show_desc', True)),
                        show_cota=bool(cfg.get('show_cota', True)),
                    )
                    arq_sufixo = _cm_state.get('nome_arq', '').strip()
                    filename = f"LEV {arq_sufixo}.dxf" if arq_sufixo else 'pontos_campo.dxf'

                    b64 = base64.b64encode(dxf_bytes).decode()
                    await ui.run_javascript(f'''
                        const a = document.createElement('a');
                        a.href = 'data:application/octet-stream;base64,{b64}';
                        a.download = {repr(filename)};
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    ''')
                    ui.notify(f'{len(_pontos)} pontos exportados.', type='positive')

                    if _cm_state.get('cliente'):
                        nome_cli = _cm_state['cliente'].get('nome', '')
                        _save_to_cliente(nome_cli, filename, dxf_bytes)
                        ui.notify(f'Cópia salva na pasta de {nome_cli}', type='positive')
                except Exception as exc:
                    ui.notify(f'Erro ao gerar DXF: {exc}', type='negative')

            btn_dxf = ui.button('Download DXF', icon='download', on_click=_download_dxf).props('unelevated no-caps').classes('dmc-btn dmc-btn-primary')
            btn_dxf.disable()

        # Renderiza preview inicial após btn_dxf estar definido
        _refresh_preview()

        # JS: toggle paleta de cores + live preview + seletor de símbolo
        ui.timer(0.05, lambda: ui.run_javascript('''
            (function() {
                // Paleta de cores
                const radios = document.querySelectorAll('input[name="cm-color-mode"]');
                const colDiv = document.getElementById('cm-custom-colors');
                if (colDiv) {
                    radios.forEach(r => r.addEventListener('change', () => {
                        colDiv.style.display = r.value === 'custom' && r.checked ? 'grid' : 'none';
                    }));
                }

                [['cm-c-desc','cm-dot-desc'],['cm-c-ponto','cm-dot-ponto'],
                 ['cm-c-circ','cm-dot-circ'],['cm-c-cota','cm-dot-cota']].forEach(([inp,dot]) => {
                    const i = document.getElementById(inp);
                    const d = document.getElementById(dot);
                    if (i && d) i.addEventListener('input', () => { d.style.background = i.value; });
                });

                // Seletor de símbolo
                function symUpdate() {
                    document.querySelectorAll('input[name="cm-symbol"]').forEach(r => {
                        const lbl = r.closest('label');
                        if (!lbl) return;
                        if (r.checked) {
                            lbl.style.borderColor = '#4ADE80';
                            lbl.style.color = '#4ADE80';
                        } else {
                            lbl.style.borderColor = 'rgba(255,255,255,0.08)';
                            lbl.style.color = '#666';
                        }
                    });
                }
                document.querySelectorAll('input[name="cm-symbol"]').forEach(r => {
                    r.addEventListener('change', symUpdate);
                });
            })();
        '''), once=True)

    dlg.open()


# ═══════════════════════════════════════════════════════════════════════════
# PROCESSAMENTO DE CAMPO — LAT/LON → PLANO LOCAL
# ═══════════════════════════════════════════════════════════════════════════

def _parse_dms(s: str) -> float:
    """Graus decimais ou DMS → float.
    Aceita: -27.590123 | -27,590123 | -27°35'24.443" | 27°35'24.443"S | 27 35 24.443 S"""
    s = str(s).strip().replace(',', '.')
    neg = False
    if s.startswith('-'):
        neg = True
        s = s[1:].strip()
    su = s.upper()
    if any(c in su for c in ('S', 'W')):
        neg = True
    for c in ('N', 'S', 'E', 'W', 'n', 's', 'e', 'w'):
        s = s.replace(c, ' ')
    try:
        v = float(s.strip())
        return -abs(v) if neg else abs(v)
    except ValueError:
        pass
    for c in ('°', "'", '"', 'd'):
        s = s.replace(c, ' ')
    parts = [x.strip() for x in s.split() if x.strip()]
    if not parts:
        raise ValueError(f'Não foi possível interpretar: {s!r}')
    d = abs(float(parts[0]))
    m = float(parts[1]) if len(parts) > 1 else 0.0
    sec = float(parts[2]) if len(parts) > 2 else 0.0
    dd = d + m / 60.0 + sec / 3600.0
    return -dd if neg else dd


# Fusos UTM do Brasil (hemisfério sul)
_BR_FUSOS: list[tuple[int, int, str]] = [
    (18, -75, "AC"),
    (19, -69, "AM · AC · RO"),
    (20, -63, "AM · MT · RO"),
    (21, -57, "MT · MS · GO · PA"),
    (22, -51, "SC · PR · SP · RS"),
    (23, -45, "MG · RJ · ES · SP · GO"),
    (24, -39, "BA · MG · SE · AL"),
    (25, -33, "BA · PE · PB · RN"),
]
_FUSO_DEFAULT = 22   # Santa Catarina


def _latlon_to_utm(lat_deg: float, lon_deg: float, zone: int) -> tuple[float, float]:
    """Lat/lon (GRS80/SIRGAS2000) → (Norte, Leste) UTM — hemisfério sul.
    Usa pyproj quando disponível; fallback: série de Redfearn."""
    if _PYPROJ:
        src = pyproj.CRS.from_epsg(4674)  # SIRGAS2000 geográfico
        dst = pyproj.CRS.from_proj4(
            f'+proj=utm +zone={zone} +south +ellps=GRS80 +units=m +no_defs'
        )
        t = pyproj.Transformer.from_crs(src, dst, always_xy=True)
        e, n = t.transform(lon_deg, lat_deg)
        return n, e

    # ── Série de Redfearn (GRS80) ────────────────────────────────────────
    a   = 6378137.0
    f   = 1.0 / 298.257222101
    e2  = 2 * f - f * f
    e4  = e2 * e2
    e6  = e2 * e4
    k0  = 0.9996
    E0  = 500_000.0
    N0s = 10_000_000.0   # false northing south

    mc  = 6 * zone - 183
    lat = math.radians(lat_deg)
    dlon = math.radians(lon_deg - mc)

    sl = math.sin(lat);  cl = math.cos(lat);  tl = math.tan(lat)
    N_r = a / math.sqrt(1 - e2 * sl * sl)
    T   = tl * tl
    C   = (e2 / (1 - e2)) * cl * cl
    A   = cl * dlon

    M = a * (
        (1 - e2/4 - 3*e4/64  - 5*e6/256)   * lat
      - (3*e2/8 + 3*e4/32   + 45*e6/1024)  * math.sin(2*lat)
      + (15*e4/256 + 45*e6/1024)            * math.sin(4*lat)
      - (35*e6/3072)                         * math.sin(6*lat)
    )

    leste = E0 + k0 * N_r * (
        A
        + (1 - T + C)                                     * A**3 / 6
        + (5 - 18*T + T*T + 72*C - 58*e2/(1-e2))         * A**5 / 120
    )
    norte = N0s + k0 * (
        M + N_r * tl * (
              A*A / 2
            + (5 - T + 9*C + 4*C*C)                      * A**4 / 24
            + (61 - 58*T + T*T + 600*C - 330*e2/(1-e2))  * A**6 / 720
        )
    )
    return norte, leste


def _parse_text_latlon(content: str) -> list[dict]:
    """Parseia TSV/CSV com PONTO · DESC · LAT · LON · COTA → lista de dicts."""
    pontos = []
    for raw in content.strip().splitlines():
        line = raw.strip()
        if not line:
            continue
        if '\t' in line:
            parts = line.split('\t')
        elif ';' in line:
            parts = line.split(';')
        else:
            continue
        if len(parts) < 4:
            continue
        try:
            cota_raw = parts[4].strip() if len(parts) > 4 else ''
            pontos.append({
                'ponto': parts[0].strip(),
                'desc':  parts[1].strip(),
                'lat':   _parse_dms(parts[2]),
                'lon':   _parse_dms(parts[3]),
                'cota':  _to_float(cota_raw) if cota_raw else 0.0,
            })
        except (ValueError, IndexError):
            continue
    return pontos


def processamento_campo_latlong_dialog() -> None:
    _pontos_utm: list[dict] = []   # {ponto, desc, norte, leste, cota, lat, lon}
    _ll_state: dict = {'cliente': None, 'nome_arq': '', 'fuso': _FUSO_DEFAULT}

    # ── seletor de fuso (estado reativo) ─────────────────────────────────────
    fuso_area = None   # preenchido depois da construção do card

    def _fuso_cards_html(sel: int) -> str:
        items = ''
        for zone, mc, uf in _BR_FUSOS:
            active = zone == sel
            bc = '#A78BFA' if active else 'rgba(255,255,255,.07)'
            tc = '#A78BFA' if active else 'var(--dmc-muted2)'
            bg = 'rgba(167,139,250,.08)' if active else 'var(--dmc-bg3)'
            fw = '700' if active else '500'
            items += (
                f'<div data-zone="{zone}" style="flex:0 0 auto;cursor:pointer;'
                f'background:{bg};border:1.5px solid {bc};border-radius:10px;'
                f'padding:8px 14px;text-align:center;min-width:68px;transition:all .15s">'
                f'<div style="font:{fw} 13px var(--dmc-mono);color:{tc}">{zone}S</div>'
                f'<div style="font:10px var(--dmc-mono);color:{tc};margin-top:1px">{mc}°</div>'
                f'<div style="font:9px var(--dmc-fm);color:var(--dmc-muted2);margin-top:3px;'
                f'white-space:nowrap;overflow:hidden;max-width:72px;text-overflow:ellipsis">{uf}</div>'
                f'</div>'
            )
        return (
            '<div style="display:flex;gap:8px;flex-wrap:nowrap;overflow-x:auto;'
            'padding-bottom:4px;margin-bottom:4px" id="ll-fuso-row">' + items + '</div>'
        )

    # ─────────────────────────────────────────────────────────────────────────

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(900px,97vw)!important;max-height:94vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        # ── Cabeçalho ────────────────────────────────────────────────────────
        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(167,139,250,.08);border:1px solid rgba(167,139,250,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#A78BFA">my_location</span></div>'
            )
            with ui.element('div'):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Campo LatLon → UTM SIRGAS2000</div>')
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    'Importa pontos (PONTO · DESC · LAT · LON · COTA), converte para UTM no fuso selecionado e gera DXF</div>'
                )

        # ── Corpo ────────────────────────────────────────────────────────────
        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1;min-height:0'):

            # ── Fuso UTM ──────────────────────────────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">'
                'Fuso UTM — SIRGAS2000 Hemisfério Sul</div>'
            )
            fuso_area = ui.element('div')
            with fuso_area:
                ui.html(_fuso_cards_html(_ll_state['fuso']))

            mc_atual = 6 * _ll_state['fuso'] - 183
            info_fuso = ui.html(
                f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:14px">'
                f'Fuso <b style="color:#A78BFA">{_ll_state["fuso"]}S</b> · '
                f'Meridiano Central <b style="color:#A78BFA">{mc_atual}°</b> · '
                f'SIRGAS2000 (GRS80) · k₀ = 0,9996</div>'
            )

            def _set_fuso(z: int) -> None:
                _ll_state['fuso'] = z
                mc = 6 * z - 183
                fuso_area.clear()
                with fuso_area:
                    ui.html(_fuso_cards_html(z))
                info_fuso.set_content(
                    f'<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:14px">'
                    f'Fuso <b style="color:#A78BFA">{z}S</b> · '
                    f'Meridiano Central <b style="color:#A78BFA">{mc}°</b> · '
                    f'SIRGAS2000 (GRS80) · k₀ = 0,9996</div>'
                )

            # ── Entrada de dados ──────────────────────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;'
                'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-bottom:8px">'
                'Entrada de dados</div>'
            )
            ui.html(
                '<label class="dmc-label">Cole aqui os dados do Excel ou CSV</label>'
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);margin-bottom:6px">'
                'Colunas: PONTO · DESCRIÇÃO · LATITUDE · LONGITUDE · COTA &nbsp;'
                '<span style="opacity:.6">'
                '(lat/lon em graus decimais ou DMS · negativo para Sul/Oeste · cota opcional)'
                '</span></div>'
            )
            ui.html(
                '<textarea id="ll-paste-area" rows="7" '
                r'placeholder="1&#9;Marco 01&#9;-27.590123&#9;-48.561234&#9;10.1234&#10;'
                r'2&#9;Marco 02&#9;-27.590456&#9;-48.561789&#9;10.2345&#10;'
                r'3&#9;&#9;-27°35\'24.443&quot;&#9;-48°33\'40.424&quot;" '
                'style="width:100%;box-sizing:border-box;resize:vertical;'
                'font:12px var(--dmc-mono);color:var(--dmc-text);'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:10px 12px;outline:none;'
                'min-height:120px;"></textarea>'
            )

            with ui.element('div').style('display:flex;justify-content:center;margin-top:12px;margin-bottom:16px'):
                async def _processar():
                    text = await ui.run_javascript(
                        "document.getElementById('ll-paste-area')?.value || ''"
                    )
                    if not text or not text.strip():
                        ui.notify('Cole os dados ou faça upload de um arquivo.', type='warning')
                        return
                    try:
                        pts_raw = _parse_text_latlon(text)
                        if not pts_raw:
                            ui.notify('Nenhum ponto reconhecido. Verifique o formato (TAB ou ; entre colunas).', type='warning')
                            return

                        zone = _ll_state['fuso']
                        converted = []
                        for p in pts_raw:
                            n, e = _latlon_to_utm(p['lat'], p['lon'], zone)
                            converted.append({
                                'ponto': p['ponto'], 'desc': p['desc'],
                                'norte': n, 'leste': e, 'cota': p['cota'],
                                'lat': p['lat'], 'lon': p['lon'],
                            })

                        _pontos_utm.clear()
                        _pontos_utm.extend(converted)
                        _refresh_preview()
                        src = 'pyproj' if _PYPROJ else 'Redfearn'
                        ui.notify(f'{len(converted)} pontos convertidos para UTM {zone}S ({src}).', type='positive')
                    except Exception as exc:
                        ui.notify(f'Erro: {exc}', type='negative')

                ui.button('Processar', icon='play_arrow', on_click=_processar).props(
                    'unelevated no-caps'
                ).classes('dmc-btn dmc-btn-primary').style('background:#7C3AED!important')

            # ── Preview ───────────────────────────────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;'
                'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-bottom:8px">'
                'Pré-visualização</div>'
            )

            preview_container = ui.element('div')

            def _refresh_preview():
                preview_container.clear()
                with preview_container:
                    if not _pontos_utm:
                        ui.html(
                            '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);'
                            'padding:12px;text-align:center">Nenhum dado carregado.</div>'
                        )
                        btn_dxf.disable()
                        return

                    z = _ll_state['fuso']
                    mc = 6 * z - 183
                    ui.html(
                        f'<div style="display:flex;align-items:center;gap:16px;'
                        f'background:rgba(167,139,250,.07);border:1px solid rgba(167,139,250,.2);'
                        f'border-radius:8px;padding:8px 14px;margin-bottom:10px;flex-wrap:wrap">'
                        f'<span style="font:10px var(--dmc-mono);color:#A78BFA;letter-spacing:.1em">UTM</span>'
                        f'<span style="font:11px var(--dmc-mono);color:var(--dmc-text)">'
                        f'Fuso {z}S · MC {mc}° · SIRGAS2000</span>'
                        f'<span style="font:12px var(--dmc-mono);color:var(--dmc-green);margin-left:auto">'
                        f'{len(_pontos_utm)} pontos</span>'
                        f'</div>'
                    )

                    cols = [
                        ('PONTO', '56px'), ('DESC', '120px'),
                        ('LAT (°)', '108px'), ('LON (°)', '108px'),
                        ('NORTE UTM (m)', '128px'), ('LESTE UTM (m)', '128px'), ('COTA', '80px'),
                    ]
                    hdr = ''.join(
                        f'<th style="padding:6px 10px;text-align:left;'
                        f'font:10px var(--dmc-mono);color:var(--dmc-muted2);'
                        f'letter-spacing:.09em;text-transform:uppercase;width:{w}">{c}</th>'
                        for c, w in cols
                    )
                    rows_html = ''
                    for i, p in enumerate(_pontos_utm):
                        bg = 'var(--dmc-bg3)' if i % 2 == 0 else 'var(--dmc-bg2)'
                        rows_html += (
                            f'<tr style="background:{bg}">'
                            f'<td style="padding:5px 10px;font:12px var(--dmc-mono);color:var(--dmc-green)">{p["ponto"]}</td>'
                            f'<td style="padding:5px 10px;font:12px var(--dmc-fm);color:var(--dmc-text)">{p["desc"]}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:var(--dmc-muted2)">{p["lat"]:.6f}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:var(--dmc-muted2)">{p["lon"]:.6f}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:#A78BFA">{p["norte"]:.3f}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:#A78BFA">{p["leste"]:.3f}</td>'
                            f'<td style="padding:5px 10px;font:11px var(--dmc-mono);color:var(--dmc-muted2)">{p["cota"]:.4f}</td>'
                            f'</tr>'
                        )
                    ui.html(
                        f'<div style="overflow-x:auto;border:1px solid var(--dmc-b1);'
                        f'border-radius:8px;overflow:hidden;max-height:240px;overflow-y:auto">'
                        f'<table style="width:100%;border-collapse:collapse">'
                        f'<thead><tr style="border-bottom:1px solid var(--dmc-b1)">{hdr}</tr></thead>'
                        f'<tbody>{rows_html}</tbody>'
                        f'</table></div>'
                    )
                    btn_dxf.enable()

            # ── Configuração DXF ──────────────────────────────────────────────
            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;'
                'border-top:1px solid var(--dmc-b1);padding-top:14px;margin-top:4px;margin-bottom:10px">'
                'Configuração DXF</div>'
            )

            ui.html('<label class="dmc-label">Nome do Arquivo</label>')
            with ui.element('div').style(
                'display:flex;align-items:stretch;height:40px;'
                'border:1px solid var(--dmc-b2);border-radius:8px;'
                'background:var(--dmc-bg);margin-bottom:6px;overflow:hidden;'
            ):
                ui.html(
                    '<span style="padding:0 14px;display:flex;align-items:center;'
                    'font:700 13px var(--dmc-mono);color:var(--dmc-text);'
                    'white-space:nowrap;background:var(--dmc-bg3);'
                    'border-right:1px solid var(--dmc-b1)">GEO</span>'
                ).style('display:flex;align-self:stretch;flex-shrink:0')
                ui.input(
                    placeholder=' ',
                    on_change=lambda e: _ll_state.update({'nome_arq': e.value or ''}),
                ).props('borderless dense').style('flex:1;min-width:0')
            ui.html(
                '<div style="font:11px var(--dmc-fm);color:var(--dmc-muted2);margin-bottom:14px">'
                'O arquivo será gerado como <b>GEO  .dxf</b> (exemplo)</div>'
            )

            ui.html(
                '<div style="font:11px var(--dmc-mono);color:var(--dmc-muted2);'
                'letter-spacing:.14em;text-transform:uppercase;margin-bottom:10px">'
                'Vincular Cliente <span style="font-weight:400;text-transform:none;'
                'letter-spacing:0">(opcional)</span></div>'
            )
            _build_cliente_selector(_ll_state)
            ui.html('<div style="margin-bottom:14px"></div>')

            with ui.element('div').style(
                'display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px'
            ):
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Tamanho da fonte (m)</label>')
                    ui.html(
                        '<input class="dmc-input" id="ll-font" type="number" '
                        'value="1.0" step="0.1" min="0.1" max="50" style="width:100%">'
                    )
                with ui.element('div'):
                    ui.html('<label class="dmc-label">Layers</label>')
                    ui.html(
                        '<select class="dmc-input" id="ll-layer" style="width:100%">'
                        '<option value="single" selected>Único (_TG)</option>'
                        '<option value="by_desc">Por descrição</option>'
                        '</select>'
                    )

            ui.html(
                '<div style="display:flex;gap:20px;margin-bottom:14px;flex-wrap:wrap">'
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:12px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="checkbox" id="ll-show-desc" checked '
                'style="width:15px;height:15px;accent-color:var(--dmc-green);cursor:pointer">'
                'Exibir Descrição no DXF</label>'
                '<label style="display:inline-flex;align-items:center;gap:8px;cursor:pointer;'
                'font:12px var(--dmc-fm);color:var(--dmc-text)">'
                '<input type="checkbox" id="ll-show-cota" checked '
                'style="width:15px;height:15px;accent-color:var(--dmc-green);cursor:pointer">'
                'Exibir Cota no DXF</label>'
                '</div>'
            )

            def _sym_ll(val, label, svg_inner, checked=False):
                sel = 'border:2px solid #A78BFA;color:#A78BFA' if checked else 'border:2px solid rgba(255,255,255,0.08);color:#666'
                chk = ' checked' if checked else ''
                return (
                    f'<label style="display:flex;flex-direction:column;align-items:center;gap:5px;'
                    f'padding:9px 13px;border-radius:10px;cursor:pointer;background:var(--dmc-bg3);'
                    f'{sel};transition:border-color .15s,color .15s;user-select:none">'
                    f'<input type="radio" name="ll-symbol" value="{val}"{chk} style="display:none">'
                    f'<svg width="30" height="30" viewBox="0 0 32 32" fill="none" '
                    f'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
                    f'style="pointer-events:none">{svg_inner}</svg>'
                    f'<span style="font:10px var(--dmc-mono)">{label}</span>'
                    f'</label>'
                )

            ui.html(
                '<div class="dmc-label" style="margin-bottom:8px">Símbolo do ponto</div>'
                '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">'
                + _sym_ll('circulo',   'Círculo',   '<circle cx="16" cy="16" r="10"/>', checked=True)
                + _sym_ll('triangulo', 'Triângulo', '<polygon points="16,3 1,29 31,29"/>')
                + _sym_ll('quadrado',  'Quadrado',  '<rect x="3" y="3" width="26" height="26"/>')
                + _sym_ll('x',        'X',          '<line x1="4" y1="4" x2="28" y2="28"/><line x1="28" y1="4" x2="4" y2="28"/>')
                + _sym_ll('mais',     '+',          '<line x1="16" y1="3" x2="16" y2="29"/><line x1="3" y1="16" x2="29" y2="16"/>')
                + '</div>'
            )

            ui.html(
                '<div style="margin-bottom:10px">'
                '<div class="dmc-label" style="margin-bottom:6px">Modo de cores</div>'
                '<label style="display:inline-flex;align-items:center;gap:6px;'
                'font:12px var(--dmc-fm);color:var(--dmc-text);margin-right:20px;cursor:pointer">'
                '<input type="radio" name="ll-color-mode" value="default" checked> Padrão</label>'
                '<label style="display:inline-flex;align-items:center;gap:6px;'
                'font:12px var(--dmc-fm);color:var(--dmc-text);cursor:pointer">'
                '<input type="radio" name="ll-color-mode" value="custom"> Personalizado</label>'
                '</div>'
            )
            ui.html(
                '<div id="ll-custom-colors" style="'
                'display:none;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:4px">'
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="ll-c-desc" value="#00FFFF" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Descrição</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#00FFFF;margin-left:auto" id="ll-dot-desc"></span></label>'
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="ll-c-ponto" value="#FF0000" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Nome do ponto</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#FF0000;margin-left:auto" id="ll-dot-ponto"></span></label>'
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="ll-c-circ" value="#00B050" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Círculo</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#00B050;margin-left:auto" id="ll-dot-circ"></span></label>'
                '<label style="display:flex;align-items:center;gap:8px;'
                'background:var(--dmc-bg3);border:1px solid var(--dmc-b1);'
                'border-radius:8px;padding:8px 12px;cursor:pointer">'
                '<input type="color" id="ll-c-cota" value="#FFFF00" style="width:28px;height:28px;'
                'border:none;background:none;cursor:pointer;border-radius:4px">'
                '<span style="font:12px var(--dmc-fm);color:var(--dmc-muted2)">Cota</span>'
                '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                'background:#FFFF00;margin-left:auto" id="ll-dot-cota"></span></label>'
                '</div>'
            )

        # ── Rodapé ───────────────────────────────────────────────────────────
        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0'
        ):
            ui.button('Fechar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _download_dxf():
                if not _pontos_utm:
                    ui.notify('Nenhum ponto para exportar.', type='warning')
                    return
                try:
                    cfg = await ui.run_javascript('''({
                        font_size:  parseFloat(document.getElementById('ll-font')?.value) || 1.0,
                        layer_mode: document.getElementById('ll-layer')?.value || 'single',
                        color_mode: (document.querySelector('input[name="ll-color-mode"]:checked')?.value) || 'default',
                        symbol:     (document.querySelector('input[name="ll-symbol"]:checked')?.value) || 'circulo',
                        desc:    document.getElementById('ll-c-desc')?.value  || '#00FFFF',
                        ponto:   document.getElementById('ll-c-ponto')?.value || '#FF0000',
                        circulo: document.getElementById('ll-c-circ')?.value  || '#00B050',
                        cota:    document.getElementById('ll-c-cota')?.value  || '#FFFF00',
                        show_desc: document.getElementById('ll-show-desc')?.checked ?? true,
                        show_cota: document.getElementById('ll-show-cota')?.checked ?? true,
                    })''')

                    colors = None
                    if cfg.get('color_mode') == 'custom':
                        colors = {
                            'desc':    cfg['desc'],
                            'ponto':   cfg['ponto'],
                            'circulo': cfg['circulo'],
                            'cota':    cfg['cota'],
                        }

                    dxf_bytes = _gen_campo_dxf(
                        _pontos_utm,
                        font_size=float(cfg.get('font_size', 1.0)),
                        layer_mode=cfg.get('layer_mode', 'single'),
                        colors=colors,
                        symbol=cfg.get('symbol', 'circulo'),
                        show_desc=bool(cfg.get('show_desc', True)),
                        show_cota=bool(cfg.get('show_cota', True)),
                    )
                    z = _ll_state['fuso']
                    arq_sufixo = _ll_state.get('nome_arq', '').strip()
                    filename = f'GEO {arq_sufixo}.dxf' if arq_sufixo else f'UTM{z}S_pontos.dxf'

                    b64 = base64.b64encode(dxf_bytes).decode()
                    await ui.run_javascript(f'''
                        const a = document.createElement('a');
                        a.href = 'data:application/octet-stream;base64,{b64}';
                        a.download = {repr(filename)};
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    ''')
                    ui.notify(f'{len(_pontos_utm)} pontos exportados — UTM {z}S.', type='positive')

                    if _ll_state.get('cliente'):
                        nome_cli = _ll_state['cliente'].get('nome', '')
                        _save_to_cliente(nome_cli, filename, dxf_bytes)
                        ui.notify(f'Cópia salva na pasta de {nome_cli}', type='positive')
                except Exception as exc:
                    ui.notify(f'Erro ao gerar DXF: {exc}', type='negative')

            btn_dxf = ui.button('Download DXF', icon='download', on_click=_download_dxf).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style('background:#7C3AED!important')
            btn_dxf.disable()

        # Renderiza preview inicial
        _refresh_preview()

        # JS: clique nos cards de fuso + paleta + símbolo
        ui.timer(0.05, lambda: ui.run_javascript('''
            (function(){
                var row = document.getElementById('ll-fuso-row');
                if(row){
                    row.addEventListener('click', function(e){
                        var card = e.target.closest('[data-zone]');
                        if(!card) return;
                        var z = parseInt(card.getAttribute('data-zone'));
                        emitEvent('ll_fuso_click', {zone: z});
                    });
                }
                // Paleta de cores
                var radios = document.querySelectorAll('input[name="ll-color-mode"]');
                var colDiv = document.getElementById('ll-custom-colors');
                if(colDiv){
                    radios.forEach(function(r){
                        r.addEventListener('change', function(){
                            colDiv.style.display = r.value==='custom' && r.checked ? 'grid' : 'none';
                        });
                    });
                }
                [['ll-c-desc','ll-dot-desc'],['ll-c-ponto','ll-dot-ponto'],
                 ['ll-c-circ','ll-dot-circ'],['ll-c-cota','ll-dot-cota']].forEach(function(p){
                    var i=document.getElementById(p[0]),d=document.getElementById(p[1]);
                    if(i&&d) i.addEventListener('input',function(){d.style.background=i.value;});
                });
                // Seletor de símbolo
                function symUpdate(){
                    document.querySelectorAll('input[name="ll-symbol"]').forEach(function(r){
                        var lbl=r.closest('label'); if(!lbl) return;
                        lbl.style.borderColor = r.checked ? '#A78BFA' : 'rgba(255,255,255,0.08)';
                        lbl.style.color = r.checked ? '#A78BFA' : '#666';
                    });
                }
                document.querySelectorAll('input[name="ll-symbol"]').forEach(function(r){
                    r.addEventListener('change', symUpdate);
                });
            })();
        '''), once=True)

        # Recebe clique de fuso via evento NiceGUI
        ui.on('ll_fuso_click', lambda e: _set_fuso(int(e.args.get('zone', _FUSO_DEFAULT))))

    dlg.open()


# ═══════════════════════════════════════════════════════════════════════════
# RELATÓRIO DE CAMPO
# ═══════════════════════════════════════════════════════════════════════════

def relatorio_campo_dialog() -> None:
    from datetime import date as _date
    from services.ponto import load_ponto
    from services.relatorio_campo import _MESES_PT, gerar_relatorio_bytes

    now = _date.today()
    registros = load_ponto()
    obras        = sorted({r.get("obra", "")    for r in registros if r.get("obra")})
    funcionarios = sorted({r.get("usuario", "") for r in registros if r.get("usuario")})

    sel_state: dict = {"modo": "obra", "item": ""}

    _mes_opts = "".join(
        f'<option value="{i + 1}"{" selected" if i + 1 == now.month else ""}>{m}</option>'
        for i, m in enumerate(_MESES_PT)
    )

    with ui.dialog() as dlg, ui.card().style(
        'background:var(--dmc-bg2)!important;border:1px solid var(--dmc-b2)!important;'
        'border-radius:18px!important;padding:0;'
        'width:min(720px,97vw)!important;max-height:92vh;'
        'display:flex;flex-direction:column;color:var(--dmc-text)!important;position:relative;'
    ):
        ui.button(icon='close', on_click=dlg.close).props('flat round dense').style(
            'color:var(--dmc-muted);position:absolute;top:12px;right:12px;z-index:10;'
        )

        # ── Cabeçalho ────────────────────────────────────────────────
        with ui.element('div').style(
            'padding:18px 24px;border-bottom:1px solid var(--dmc-b1);'
            'display:flex;align-items:center;gap:14px;flex-shrink:0;padding-right:52px;'
        ):
            ui.html(
                '<div style="width:40px;height:40px;border-radius:10px;flex-shrink:0;'
                'background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.25);'
                'display:flex;align-items:center;justify-content:center;">'
                '<span class="material-icons" style="font-size:20px;color:#FBBF24">summarize</span></div>'
            )
            with ui.element('div'):
                ui.html('<div style="font:700 16px var(--dmc-fd);color:var(--dmc-text)">Relatório de Campo</div>')
                ui.html(
                    '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);margin-top:1px">'
                    'Check-in e check-out por obra ou funcionário</div>'
                )

        # ── Corpo ────────────────────────────────────────────────────
        with ui.element('div').style('padding:20px 24px;overflow-y:auto;flex:1;min-height:0'):

            def _sec(text: str) -> None:
                ui.html(
                    f'<div style="font:9px var(--dmc-mono);color:var(--dmc-muted2);'
                    f'letter-spacing:.16em;text-transform:uppercase;margin-bottom:10px">{text}</div>'
                )

            _sec('Tipo de Relatório')
            modo_area = ui.element('div').style('display:flex;gap:8px;margin-bottom:20px')

            ui.element('div').style('height:2px')
            _sec('Selecionar')
            item_area = ui.element('div').style('margin-bottom:20px')

            _sec('Período')
            ui.html(
                f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">'

                f'<div>'
                f'<label class="dmc-label">De</label>'
                f'<div style="display:flex;gap:8px">'
                f'<select class="dmc-input" id="rc-mes-ini" style="flex:1">{_mes_opts}</select>'
                f'<input class="dmc-input" id="rc-ano-ini" type="number" value="{now.year}" '
                f'min="2000" max="2100" style="width:76px">'
                f'</div></div>'

                f'<div>'
                f'<label class="dmc-label">Até</label>'
                f'<div style="display:flex;gap:8px">'
                f'<select class="dmc-input" id="rc-mes-fim" style="flex:1">{_mes_opts}</select>'
                f'<input class="dmc-input" id="rc-ano-fim" type="number" value="{now.year}" '
                f'min="2000" max="2100" style="width:76px">'
                f'</div></div>'

                f'</div>'
            )

        # ── Rodapé ───────────────────────────────────────────────────
        with ui.element('div').style(
            'padding:14px 24px;border-top:1px solid var(--dmc-b1);'
            'display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;'
        ):
            ui.button('Cancelar', on_click=dlg.close).props('flat no-caps').classes('dmc-btn dmc-btn-ghost')

            async def _gerar():
                if not sel_state['item']:
                    ui.notify('Selecione uma obra ou funcionário.', type='warning')
                    return

                vals = await ui.run_javascript("""({
                    mes_ini: parseInt(document.getElementById('rc-mes-ini')?.value) || 1,
                    ano_ini: parseInt(document.getElementById('rc-ano-ini')?.value) || 2026,
                    mes_fim: parseInt(document.getElementById('rc-mes-fim')?.value) || 1,
                    ano_fim: parseInt(document.getElementById('rc-ano-fim')?.value) || 2026,
                })""")

                from datetime import date as _d
                try:
                    di = _d(vals['ano_ini'], vals['mes_ini'], 1)
                    df = _d(vals['ano_fim'], vals['mes_fim'], 1)
                except Exception:
                    ui.notify('Período inválido.', type='warning')
                    return
                if df < di:
                    ui.notify('O período final deve ser maior ou igual ao inicial.', type='warning')
                    return

                try:
                    content = gerar_relatorio_bytes(
                        registros,
                        sel_state['modo'],
                        sel_state['item'],
                        vals['ano_ini'], vals['mes_ini'],
                        vals['ano_fim'], vals['mes_fim'],
                    )
                    nome_safe = ''.join(
                        c if c.isalnum() or c in '_-' else '_'
                        for c in sel_state['item']
                    )[:40]
                    ui.download(content, f'Relatorio_Campo_{nome_safe}.docx')
                    ui.notify('Relatório gerado!', type='positive')
                    dlg.close()
                except Exception as e:
                    ui.notify(f'Erro ao gerar: {e}', type='negative')

            ui.button('Gerar Relatório', icon='download', on_click=_gerar).props(
                'unelevated no-caps'
            ).classes('dmc-btn dmc-btn-primary').style('padding:0 20px')

        # ── Renderização ─────────────────────────────────────────────

        def render_modo():
            modo_area.clear()
            with modo_area:
                for m, label, icon in [
                    ('obra', 'Por Obra', 'business'),
                    ('funcionario', 'Por Funcionário', 'person'),
                ]:
                    active = sel_state['modo'] == m
                    border = '1.5px solid var(--dmc-green)' if active else '1px solid var(--dmc-b1)'
                    bg = 'rgba(74,222,128,.08)' if active else 'var(--dmc-bg3)'
                    card = ui.element('div').style(
                        f'background:{bg};border:{border};border-radius:10px;'
                        'padding:10px 18px;cursor:pointer;display:flex;align-items:center;'
                        'gap:8px;flex:1;justify-content:center;transition:border .15s;'
                    )
                    with card:
                        ic_col = 'var(--dmc-green)' if active else 'var(--dmc-muted2)'
                        ui.html(f'<span class="material-icons" style="font-size:18px;color:{ic_col}">{icon}</span>')
                        ui.html(
                            f'<span style="font:{"600" if active else "500"} 13px var(--dmc-fm);'
                            f'color:var(--dmc-text)">{label}</span>'
                        )

                    def _set_modo(mode=m):
                        sel_state['modo'] = mode
                        sel_state['item'] = ''
                        render_modo()
                        render_items()

                    card.on('click', _set_modo)

        def render_items():
            item_area.clear()
            items = obras if sel_state['modo'] == 'obra' else funcionarios
            with item_area:
                if not items:
                    ui.html(
                        '<div style="font:12px var(--dmc-fm);color:var(--dmc-muted2);padding:4px 0">'
                        'Nenhum registro de campo encontrado.</div>'
                    )
                    return
                with ui.element('div').style('display:flex;gap:8px;flex-wrap:wrap'):
                    for item in items:
                        active = sel_state['item'] == item
                        border = '1.5px solid var(--dmc-green)' if active else '1px solid var(--dmc-b1)'
                        bg = 'rgba(74,222,128,.08)' if active else 'var(--dmc-bg3)'
                        icon = 'business' if sel_state['modo'] == 'obra' else 'person'
                        card = ui.element('div').style(
                            f'background:{bg};border:{border};border-radius:10px;'
                            'padding:8px 14px;cursor:pointer;display:flex;align-items:center;'
                            'gap:8px;transition:border .15s;'
                        )
                        with card:
                            ic_col = 'var(--dmc-green)' if active else 'var(--dmc-muted2)'
                            ui.html(f'<span class="material-icons" style="font-size:15px;color:{ic_col}">{icon}</span>')
                            ui.html(f'<span style="font:500 13px var(--dmc-fm);color:var(--dmc-text)">{item}</span>')
                            if active:
                                ui.html(
                                    '<span class="material-icons" '
                                    'style="font-size:14px;color:var(--dmc-green);margin-left:2px">check_circle</span>'
                                )

                        def _select(i=item):
                            sel_state['item'] = '' if sel_state['item'] == i else i
                            render_items()

                        card.on('click', _select)

        render_modo()
        render_items()

    dlg.open()
