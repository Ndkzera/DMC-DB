"""Conversão KML/KMZ → Shapefile compatível com SIG-RI/ONR (EPSG:4674 SIRGAS 2000)."""

import io
import struct
import zipfile as _zf
from datetime import date as _date
from xml.etree import ElementTree as _ET

# PRJ — SIRGAS 2000 geográfico EPSG:4674 (WKT ESRI)
# TOWGS84 omitido propositalmente: sua presença (mesmo com zeros) faz algumas
# versões do PROJ/QGIS usar o método Helmert em vez do lookup pela AUTHORITY,
# podendo introduzir deslocamento. Sem TOWGS84 o GIS usa o EPSG:4674 diretamente.
_PRJ = (
    'GEOGCS["SIRGAS 2000",'
    'DATUM["Sistema_de_Referencia_Geocentrico_para_las_AmericaS_2000",'
    'SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],'
    'AUTHORITY["EPSG","6674"]],'
    'PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],'
    'UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],'
    'AUTHORITY["EPSG","4674"]]'
)


# ── Parsing KML ────────────────────────────────────────────────────────────────

def _ns(tag: str) -> str:
    return tag.split('}')[-1] if '}' in tag else tag


def _coords_from_el(el) -> list[tuple[float, float]]:
    for node in el.iter():
        if _ns(node.tag) == 'coordinates' and node.text:
            pts = []
            for tok in node.text.strip().split():
                parts = tok.split(',')
                if len(parts) >= 2:
                    try:
                        pts.append((float(parts[0]), float(parts[1])))
                    except ValueError:
                        pass
            return pts
    return []


def _walk(node, results: list) -> None:
    if _ns(node.tag) == 'Placemark':
        name = ''
        for child in node:
            if _ns(child.tag) == 'name' and child.text:
                name = child.text.strip()
                break

        rings: list[list[tuple[float, float]]] = []
        for poly_el in node.iter():
            if _ns(poly_el.tag) == 'Polygon':
                for boundary in poly_el:
                    bname = _ns(boundary.tag)
                    if bname in ('outerBoundaryIs', 'innerBoundaryIs'):
                        pts = _coords_from_el(boundary)
                        if pts:
                            rings.append(pts)

        if rings:
            results.append({'name': name, 'rings': rings})
    else:
        for child in node:
            _walk(child, results)


def parse_kml_bytes(data: bytes) -> list[dict]:
    """KML bytes → lista de {'name': str, 'rings': [[(lon, lat), ...]]}."""
    root = _ET.fromstring(data.decode('utf-8', errors='replace'))
    results: list[dict] = []
    _walk(root, results)
    return results


def parse_kmz_bytes(data: bytes) -> list[dict]:
    """KMZ bytes → lista de polígonos (extrai KML interno)."""
    with _zf.ZipFile(io.BytesIO(data)) as z:
        kml_name = next((n for n in z.namelist() if n.lower().endswith('.kml')), None)
        if not kml_name:
            raise ValueError('Nenhum arquivo .kml encontrado dentro do KMZ.')
        return parse_kml_bytes(z.read(kml_name))


# ── Shapefile writer ───────────────────────────────────────────────────────────

def _ring_area_sign(ring: list[tuple[float, float]]) -> float:
    """Shoelace: positivo = CCW, negativo = CW."""
    area = 0.0
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        area += (x1 - x0) * (y1 + y0)
    return area


def _ensure_closed(ring: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if ring and ring[0] != ring[-1]:
        ring = ring + [ring[0]]
    return ring


def _orient_rings(rings: list[list[tuple[float, float]]]) -> list[list[tuple[float, float]]]:
    """
    ESRI geographic shapefile: outer rings CCW, holes CW (Y-up / map convention).
    _ring_area_sign uses the trapezoidal formula which gives the OPPOSITE sign
    from the standard shoelace: CCW → negative, CW → positive.
    So: outer ring → force sign < 0 (CCW); holes → force sign > 0 (CW).
    """
    result = []
    for i, ring in enumerate(rings):
        ring = _ensure_closed(ring)
        sign = _ring_area_sign(ring)
        if i == 0:          # outer ring: must be CCW → sign < 0
            if sign > 0:
                ring = list(reversed(ring))
        else:               # hole: must be CW → sign > 0
            if sign < 0:
                ring = list(reversed(ring))
        result.append(ring)
    return result


def _build_shp_record(rings: list[list[tuple[float, float]]]) -> bytes:
    rings = _orient_rings(rings)
    nparts  = len(rings)
    npoints = sum(len(r) for r in rings)

    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]

    buf = io.BytesIO()
    buf.write(struct.pack('<i', 5))                         # shape type = Polygon
    buf.write(struct.pack('<4d', min(xs), min(ys), max(xs), max(ys)))
    buf.write(struct.pack('<2i', nparts, npoints))

    idx = 0
    for r in rings:
        buf.write(struct.pack('<i', idx))
        idx += len(r)

    for r in rings:
        for x, y in r:
            buf.write(struct.pack('<2d', x, y))

    return buf.getvalue()


def _shp_file_header(file_len_words: int, bbox: tuple) -> bytes:
    gxmin, gymin, gxmax, gymax = bbox
    h = io.BytesIO()
    h.write(struct.pack('>i', 9994))        # file code
    h.write(b'\x00' * 20)                   # unused
    h.write(struct.pack('>i', file_len_words))
    h.write(struct.pack('<i', 1000))         # version
    h.write(struct.pack('<i', 5))            # shape type = Polygon
    h.write(struct.pack('<8d', gxmin, gymin, gxmax, gymax, 0.0, 0.0, 0.0, 0.0))
    return h.getvalue()


def _build_dbf(names: list[str]) -> bytes:
    today     = _date.today()
    flen      = 254
    n_recs    = len(names)
    hdr_size  = 32 + 32 + 1      # main + 1 field descriptor + terminator
    rec_size  = 1 + flen

    buf = io.BytesIO()
    buf.write(struct.pack('B', 3))
    buf.write(struct.pack('3B', today.year - 1900, today.month, today.day))
    buf.write(struct.pack('<I', n_recs))
    buf.write(struct.pack('<H', hdr_size))
    buf.write(struct.pack('<H', rec_size))
    buf.write(b'\x00' * 20)

    # Field: NOME  C  254
    buf.write(b'NOME\x00\x00\x00\x00\x00\x00\x00')
    buf.write(b'C')
    buf.write(b'\x00' * 4)
    buf.write(struct.pack('B', flen))
    buf.write(struct.pack('B', 0))
    buf.write(b'\x00' * 14)

    buf.write(b'\r')  # header terminator

    for name in names:
        buf.write(b' ')  # not deleted
        enc = name.encode('utf-8', errors='replace')[:flen]
        buf.write(enc.ljust(flen, b' '))

    buf.write(b'\x1a')  # EOF
    return buf.getvalue()


def make_shapefile_zip(polygons: list[dict], base_name: str = 'poligonos') -> bytes:
    """
    Gera ZIP com .shp/.shx/.dbf/.prj/.cpg no padrão SIG-RI/ONR.
    polygons: lista de {'name': str, 'rings': [[(lon, lat), ...]]}
    """
    if not polygons:
        raise ValueError('Nenhum polígono para exportar.')

    records   = [_build_shp_record(p['rings']) for p in polygons]
    names     = [p.get('name', '') for p in polygons]

    # Bounding box global
    all_xs, all_ys = [], []
    for p in polygons:
        for r in p['rings']:
            all_xs += [pt[0] for pt in r]
            all_ys += [pt[1] for pt in r]
    global_bbox = (min(all_xs), min(all_ys), max(all_xs), max(all_ys))

    # SHP
    shp_words = 50
    for rec in records:
        shp_words += 4 + len(rec) // 2

    shp_buf = io.BytesIO()
    shp_buf.write(_shp_file_header(shp_words, global_bbox))

    # SHX
    shx_words = 50 + len(records) * 4
    shx_buf = io.BytesIO()
    shx_buf.write(_shp_file_header(shx_words, global_bbox))

    offset = 50  # words
    for rec_num, rec in enumerate(records):
        cw = len(rec) // 2
        shp_buf.write(struct.pack('>2i', rec_num + 1, cw))
        shp_buf.write(rec)
        shx_buf.write(struct.pack('>2i', offset, cw))
        offset += 4 + cw

    # Bundle
    zip_buf = io.BytesIO()
    with _zf.ZipFile(zip_buf, 'w', _zf.ZIP_DEFLATED) as zf:
        zf.writestr(f'{base_name}.shp', shp_buf.getvalue())
        zf.writestr(f'{base_name}.shx', shx_buf.getvalue())
        zf.writestr(f'{base_name}.dbf', _build_dbf(names))
        zf.writestr(f'{base_name}.prj', _PRJ)
        zf.writestr(f'{base_name}.cpg', 'UTF-8')

    return zip_buf.getvalue()
