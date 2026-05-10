"""Serviço NFS-e Nacional — emissão, consulta e cancelamento (API gov.br)."""

import base64
import gzip
import hashlib
import io
import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

# ── Dependências opcionais ────────────────────────────────────────────
try:
    from lxml import etree as ET
    _LXML = True
except ImportError:
    _LXML = False

try:
    from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
    import cryptography.x509
    _CRYPTO = True
except ImportError:
    _CRYPTO = False

try:
    import httpx
    _HTTPX = True
except ImportError:
    _HTTPX = False

_DEPS_OK = _LXML and _CRYPTO and _HTTPX
_DEPS_MSG = (
    'Dependências ausentes. Instale:\n'
    '  pip install lxml cryptography httpx'
)

# ── Caminhos ──────────────────────────────────────────────────────────
_DATA_DIR   = Path('data/nfse')
_CONFIG_FILE = Path('data/nfse_config.json')
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── URLs da API NFS-e Nacional ────────────────────────────────────────
_URLS = {
    'homologacao': 'https://sefin.producaorestrita.nfse.gov.br/SefinNacional',
    'producao':    'https://sefin.nfse.gov.br/SefinNacional',
}

_NS_DPS  = 'http://www.sped.fazenda.gov.br/nfse'
_NS_DSIG = 'http://www.w3.org/2000/09/xmldsig#'


# ── Configuração ───────────────────────────────────────────────────────

def load_config() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text('utf-8'))
        except Exception:
            pass
    return {
        'cnpj':          '',
        'im':            '',
        'cod_municipio': '',
        'razao_social':  '',
        'cert_path':     '',
        'cert_senha':    '',
        'ambiente':      'homologacao',
        'aliquota_iss':  '5.00',
        'serie':         '1',
        'proximo_num':   1,
    }


def save_config(cfg: dict) -> None:
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), 'utf-8')


# ── Certificado ────────────────────────────────────────────────────────

def _load_pfx(pfx_path: str, senha: str):
    if not _CRYPTO:
        raise RuntimeError(_DEPS_MSG)
    data = Path(pfx_path).read_bytes()
    pw   = senha.encode() if senha else b''
    return pkcs12.load_key_and_certificates(data, pw)


def cert_info(pfx_path: str, senha: str) -> dict:
    """Retorna dict com CN, validade e CNPJ extraído do cert."""
    pk, cert, _ = _load_pfx(pfx_path, senha)
    cn = ''
    try:
        cn = cert.subject.get_attributes_for_oid(
            cryptography.x509.NameOID.COMMON_NAME
        )[0].value
    except Exception:
        pass
    return {
        'cn':       cn,
        'validade': cert.not_valid_after_utc.strftime('%d/%m/%Y'),
    }


def _cert_to_pem(pfx_path: str, senha: str) -> tuple[bytes, bytes]:
    pk, cert, _ = _load_pfx(pfx_path, senha)
    cert_pem = cert.public_bytes(Encoding.PEM)
    key_pem  = pk.private_bytes(Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption())
    return cert_pem, key_pem


def _cert_der_b64(pfx_path: str, senha: str) -> str:
    _, cert, _ = _load_pfx(pfx_path, senha)
    return base64.b64encode(cert.public_bytes(Encoding.DER)).decode()


# ── Builder DPS ────────────────────────────────────────────────────────

def _clean(v: str, digits_only: bool = True) -> str:
    if digits_only:
        return ''.join(c for c in (v or '') if c.isdigit())
    return (v or '').strip()


def build_dps(dados: dict, cfg: dict) -> str:
    """
    Constrói XML DPS não-assinado.

    dados esperados:
      toma_tipo   : 'CNPJ' | 'CPF'
      toma_doc    : str
      toma_nome   : str
      toma_cep    : str
      toma_end    : str  (logradouro)
      toma_num    : str
      toma_bairro : str
      toma_cidade : str
      toma_uf     : str
      toma_cod_mun: str  (código IBGE do tomador)
      descricao   : str
      cod_tributacao : str  (cTribNac)
      cod_nbs     : str  (cNBS — obrigatório 2026+)
      valor       : float
      iss_retido  : bool
      num_dps     : int
    """
    if not _LXML:
        raise RuntimeError(_DEPS_MSG)

    agora    = datetime.now().astimezone()
    tz_str   = agora.strftime('%z')
    tz_fmt   = tz_str[:3] + ':' + tz_str[3:]
    dh_emi   = agora.strftime('%Y-%m-%dT%H:%M:%S') + tz_fmt
    d_compet = agora.strftime('%Y-%m')
    ambiente = '2' if cfg.get('ambiente', 'homologacao') == 'homologacao' else '1'
    n_dps    = str(dados.get('num_dps', 1))
    cnpj     = _clean(cfg.get('cnpj', ''))
    id_dps   = f'DPS{cnpj}{agora.strftime("%Y%m%d%H%M%S")}{n_dps.zfill(9)}'

    nsmap = {None: _NS_DPS}
    dps   = ET.Element('DPS', nsmap=nsmap)
    inf   = ET.SubElement(dps, 'infDPS', versao='1.00')
    inf.set('Id', id_dps)

    ET.SubElement(inf, 'tpAmb').text    = ambiente
    ET.SubElement(inf, 'dhEmi').text    = dh_emi
    ET.SubElement(inf, 'verAplic').text = '1.00'
    ET.SubElement(inf, 'serie').text    = cfg.get('serie', '1')
    ET.SubElement(inf, 'nDPS').text     = n_dps
    ET.SubElement(inf, 'dCompet').text  = d_compet
    ET.SubElement(inf, 'tpEmit').text   = '1'
    ET.SubElement(inf, 'cLocEmi').text  = cfg.get('cod_municipio', '')

    # Prestador
    prest = ET.SubElement(inf, 'prest')
    ET.SubElement(prest, 'CNPJ').text = cnpj
    if cfg.get('im'):
        ET.SubElement(prest, 'IM').text = cfg['im']

    # Tomador
    toma = ET.SubElement(inf, 'toma')
    doc_tipo = dados.get('toma_tipo', 'CNPJ')
    doc_val  = _clean(dados.get('toma_doc', ''))
    ET.SubElement(toma, doc_tipo).text = doc_val
    ET.SubElement(toma, 'xNome').text  = _clean(dados.get('toma_nome', ''), False)

    end = ET.SubElement(toma, 'end')
    ET.SubElement(end, 'xLgr').text    = _clean(dados.get('toma_end', ''), False)
    ET.SubElement(end, 'nro').text     = _clean(dados.get('toma_num', 'S/N'), False) or 'S/N'
    ET.SubElement(end, 'xBairro').text = _clean(dados.get('toma_bairro', ''), False)
    ET.SubElement(end, 'cMun').text    = _clean(dados.get('toma_cod_mun', '') or cfg.get('cod_municipio', ''))
    ET.SubElement(end, 'xMun').text    = _clean(dados.get('toma_cidade', ''), False)
    ET.SubElement(end, 'CEP').text     = _clean(dados.get('toma_cep', ''))
    ET.SubElement(end, 'cPais').text   = '1058'
    ET.SubElement(end, 'xPais').text   = 'BRASIL'
    ET.SubElement(end, 'UF').text      = _clean(dados.get('toma_uf', ''), False).upper()

    # Serviço
    serv     = ET.SubElement(inf, 'serv')
    locPrest = ET.SubElement(serv, 'locPrest')
    ET.SubElement(locPrest, 'cLocPrestacao').text  = cfg.get('cod_municipio', '')
    ET.SubElement(locPrest, 'cPaisPrestacao').text = '1058'

    cServ = ET.SubElement(serv, 'cServ')
    ET.SubElement(cServ, 'cTribNac').text  = dados.get('cod_tributacao', '010101')
    nbs = dados.get('cod_nbs', '').strip()
    if nbs:
        ET.SubElement(cServ, 'cNBS').text  = nbs
    ET.SubElement(cServ, 'xDescServ').text = dados.get('descricao', '')[:2000]

    comDesc = ET.SubElement(serv, 'comDesc')
    ET.SubElement(comDesc, 'xDscServ').text = dados.get('descricao', '')[:2000]

    # Valores
    valor     = float(dados.get('valor', 0) or 0)
    aliq      = float(cfg.get('aliquota_iss', '5.00') or '5.00')
    iss_val   = round(valor * aliq / 100, 2)

    valores    = ET.SubElement(inf, 'valores')
    vServPrest = ET.SubElement(valores, 'vServPrest')
    ET.SubElement(vServPrest, 'vReceb').text = f'{valor:.2f}'

    trib    = ET.SubElement(valores, 'trib')
    tribMun = ET.SubElement(trib, 'tribMun')
    ET.SubElement(tribMun, 'tribISS').text  = '1'
    ET.SubElement(tribMun, 'cLocIncid').text = cfg.get('cod_municipio', '')
    ET.SubElement(tribMun, 'pAliq').text    = f'{aliq:.4f}'
    ET.SubElement(tribMun, 'vISSQN').text   = f'{iss_val:.2f}'
    if dados.get('iss_retido'):
        ET.SubElement(tribMun, 'tpRetISSQN').text = '1'

    totTrib = ET.SubElement(trib, 'totTrib')
    ET.SubElement(totTrib, 'indTotTrib').text = '0'

    return ET.tostring(dps, encoding='unicode')


# ── Assinatura XMLDSIG ─────────────────────────────────────────────────

def sign_dps(xml_str: str, pfx_path: str, senha: str) -> str:
    """Assina infDPS com RSA-SHA256 (enveloped signature)."""
    if not _LXML or not _CRYPTO:
        raise RuntimeError(_DEPS_MSG)

    pk, cert, _ = _load_pfx(pfx_path, senha)

    root = ET.fromstring(xml_str.encode())
    ns   = {'n': _NS_DPS}
    inf  = root.find('n:infDPS', ns)
    if inf is None:
        raise ValueError('infDPS não encontrado')

    inf_id   = inf.get('Id', 'infDPS')
    inf_c14n = ET.tostring(inf, method='c14n', exclusive=True, with_comments=False)

    digest     = hashlib.sha256(inf_c14n).digest()
    digest_b64 = base64.b64encode(digest).decode()

    dsig     = 'http://www.w3.org/2000/09/xmldsig#'
    more     = 'http://www.w3.org/2001/04/xmldsig-more#'
    enc      = 'http://www.w3.org/2001/04/xmlenc#'
    c14n_alg = 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315'

    signed_info_xml = (
        f'<SignedInfo xmlns="{dsig}">'
        f'<CanonicalizationMethod Algorithm="{c14n_alg}"/>'
        f'<SignatureMethod Algorithm="{more}rsa-sha256"/>'
        f'<Reference URI="#{inf_id}">'
        f'<Transforms>'
        f'<Transform Algorithm="{dsig}enveloped-signature"/>'
        f'<Transform Algorithm="{c14n_alg}"/>'
        f'</Transforms>'
        f'<DigestMethod Algorithm="{enc}sha256"/>'
        f'<DigestValue>{digest_b64}</DigestValue>'
        f'</Reference>'
        f'</SignedInfo>'
    )

    si_el    = ET.fromstring(signed_info_xml.encode())
    si_c14n  = ET.tostring(si_el, method='c14n', exclusive=False, with_comments=False)
    sig_raw  = pk.sign(si_c14n, asym_padding.PKCS1v15(), hashes.SHA256())
    sig_b64  = base64.b64encode(sig_raw).decode()

    cert_b64 = base64.b64encode(cert.public_bytes(Encoding.DER)).decode()

    sig_el = ET.fromstring((
        f'<Signature xmlns="{dsig}">'
        f'{signed_info_xml}'
        f'<SignatureValue>{sig_b64}</SignatureValue>'
        f'<KeyInfo>'
        f'<X509Data><X509Certificate>{cert_b64}</X509Certificate></X509Data>'
        f'</KeyInfo>'
        f'</Signature>'
    ).encode())
    root.append(sig_el)

    return ET.tostring(root, encoding='unicode')


# ── API Client ─────────────────────────────────────────────────────────

def _compress(xml_str: str) -> str:
    return base64.b64encode(gzip.compress(xml_str.encode('utf-8'))).decode()


def _decompress(b64gz: str) -> str:
    return gzip.decompress(base64.b64decode(b64gz)).decode('utf-8')


def _client(pfx_path: str, senha: str):
    cert_pem, key_pem = _cert_to_pem(pfx_path, senha)
    tdir   = tempfile.mkdtemp()
    c_path = os.path.join(tdir, 'cert.pem')
    k_path = os.path.join(tdir, 'key.pem')
    Path(c_path).write_bytes(cert_pem)
    Path(k_path).write_bytes(key_pem)
    client = httpx.Client(cert=(c_path, k_path), verify=True, timeout=30)
    return client, tdir


def _cleanup(tdir: str) -> None:
    import shutil
    shutil.rmtree(tdir, ignore_errors=True)


def emit_nfse(dados: dict, cfg: dict) -> dict:
    if not _DEPS_OK:
        raise RuntimeError(_DEPS_MSG)

    num = cfg.get('proximo_num', 1)
    dados = {**dados, 'num_dps': num}

    dps_xml    = build_dps(dados, cfg)
    signed_xml = sign_dps(dps_xml, cfg['cert_path'], cfg['cert_senha'])
    url        = _URLS[cfg.get('ambiente', 'homologacao')] + '/nfse'

    client, tdir = _client(cfg['cert_path'], cfg['cert_senha'])
    try:
        r = client.post(url, json={'xmlDps': _compress(signed_xml)},
                        headers={'Content-Type': 'application/json'})
        resp = r.json()
    finally:
        client.close()
        _cleanup(tdir)

    result: dict = {
        'id':           uuid.uuid4().hex,
        'sucesso':      False,
        'nfse_xml':     '',
        'chave_acesso': '',
        'numero':       str(num),
        'erros':        [],
        'dps_xml':      signed_xml,
        'dados':        dados,
        'emitido_em':   datetime.now().isoformat(),
        'ambiente':     cfg.get('ambiente', 'homologacao'),
        'valor':        float(dados.get('valor', 0)),
        'tomador':      dados.get('toma_nome', ''),
        'descricao':    dados.get('descricao', ''),
    }

    if resp.get('xmlNfse'):
        nfse_xml = _decompress(resp['xmlNfse'])
        result['sucesso']  = True
        result['nfse_xml'] = nfse_xml
        try:
            root  = ET.fromstring(nfse_xml.encode())
            chave = root.find('.//{*}chNFSe')
            num_n = root.find('.//{*}nNFSe')
            if chave is not None:
                result['chave_acesso'] = chave.text or ''
            if num_n is not None:
                result['numero'] = num_n.text or str(num)
        except Exception:
            pass
    else:
        msgs = resp.get('mensagens') or resp.get('erros') or []
        if isinstance(msgs, list):
            result['erros'] = [m.get('xMsg', str(m)) if isinstance(m, dict) else str(m) for m in msgs]
        elif msgs:
            result['erros'] = [str(msgs)]
        if not result['erros']:
            result['erros'] = [f'HTTP {r.status_code}: {r.text[:300]}']

    return result


def consult_nfse(chave_acesso: str, cfg: dict) -> dict:
    url = _URLS[cfg.get('ambiente', 'homologacao')] + f'/nfse/{chave_acesso}'
    client, tdir = _client(cfg['cert_path'], cfg['cert_senha'])
    try:
        r = client.get(url)
        return r.json()
    finally:
        client.close()
        _cleanup(tdir)


def cancel_nfse(chave_acesso: str, motivo: str, cfg: dict) -> dict:
    url = _URLS[cfg.get('ambiente', 'homologacao')] + f'/nfse/{chave_acesso}/eventos'
    client, tdir = _client(cfg['cert_path'], cfg['cert_senha'])
    try:
        r = client.post(url, json={'tpEvento': '1', 'xMotivo': motivo},
                        headers={'Content-Type': 'application/json'})
        return r.json()
    finally:
        client.close()
        _cleanup(tdir)


# ── Armazenamento local ────────────────────────────────────────────────

def save_nfse(result: dict) -> Path:
    key  = result.get('chave_acesso') or result.get('id') or uuid.uuid4().hex
    path = _DATA_DIR / f'{key}.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    return path


def list_nfse() -> list[dict]:
    out = []
    for f in sorted(_DATA_DIR.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            out.append(json.loads(f.read_text('utf-8')))
        except Exception:
            pass
    return out


def delete_nfse_local(entry: dict) -> None:
    key  = entry.get('chave_acesso') or entry.get('id', '')
    path = _DATA_DIR / f'{key}.json'
    if path.exists():
        path.unlink()
