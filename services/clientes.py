"""CRUD de clientes — persistência em SQLite."""

import shutil
from config import CLIENTES_DIR
from services.database import get_conn, _insert_cliente
from services.log import log_action


def _row_to_dict(row) -> dict:
    d = dict(row)
    d["obra_mesmo"] = bool(d.get("obra_mesmo", 1))
    return d


def load_clientes() -> list:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def save_clientes(clientes: list) -> None:
    """Substitui toda a tabela (mantido para compatibilidade)."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM clientes")
        for c in clientes:
            _insert_cliente(conn, c)
        conn.commit()
    finally:
        conn.close()


def _pasta_cliente(nome: str):
    invalidos = set(r'\/:*?"<>|')
    safe = "".join(c for c in nome if c not in invalidos).strip() or "cliente"
    return CLIENTES_DIR / safe


def _salvar_dados_pasta(cliente: dict) -> None:
    pasta = _pasta_cliente(cliente.get("nome", "cliente"))
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "dados.txt").write_text(cliente_to_txt(cliente), encoding="utf-8")


def cpf_exists(cpf: str) -> bool:
    conn = get_conn()
    try:
        row = conn.execute("SELECT 1 FROM clientes WHERE cpf=?", (cpf,)).fetchone()
        return row is not None
    finally:
        conn.close()


def add_cliente(cliente: dict, usuario: str = "", perfil: str = "") -> None:
    cpf = cliente.get("cpf", "")
    if cpf and cpf_exists(cpf):
        tipo_doc = "CNPJ" if len("".join(c for c in cpf if c.isdigit())) == 14 else "CPF"
        raise ValueError(f"{tipo_doc} {cpf} já está cadastrado.")
    conn = get_conn()
    try:
        _insert_cliente(conn, cliente)
        conn.commit()
    finally:
        conn.close()
    _salvar_dados_pasta(cliente)
    log_action(usuario, perfil, "criar", "cliente", cliente.get("nome", ""),
               str(_pasta_cliente(cliente.get("nome", ""))))


def update_cliente(original_cpf: str, updated: dict,
                   usuario: str = "", perfil: str = "") -> None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT nome FROM clientes WHERE cpf=?", (original_cpf,)
        ).fetchone()
        old_nome = row["nome"] if row else None
        _insert_cliente(conn, updated)
        conn.commit()
    finally:
        conn.close()

    new_nome = updated.get("nome", "")
    if old_nome and old_nome != new_nome:
        pasta_antiga = _pasta_cliente(old_nome)
        pasta_nova = _pasta_cliente(new_nome)
        if pasta_antiga.exists() and not pasta_nova.exists():
            pasta_antiga.rename(pasta_nova)
        log_action(usuario, perfil, "renomear", "cliente", new_nome,
                   str(_pasta_cliente(new_nome)), f"{old_nome} → {new_nome}")
    else:
        log_action(usuario, perfil, "editar", "cliente", new_nome,
                   str(_pasta_cliente(new_nome)))
    _salvar_dados_pasta(updated)


def delete_cliente(cpf: str, nome: str, usuario: str = "", perfil: str = "") -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM clientes WHERE cpf=?", (cpf,))
        conn.commit()
    finally:
        conn.close()
    pasta = _pasta_cliente(nome)
    log_action(usuario, perfil, "excluir", "cliente", nome, str(pasta))
    if pasta.exists():
        shutil.rmtree(pasta)


def fmt_cpf(v: str) -> str:
    d = "".join(c for c in v if c.isdigit())[:11]
    if len(d) == 11:
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    return d


def fmt_tel(v: str) -> str:
    d = "".join(c for c in v if c.isdigit())[:11]
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    return d


def cliente_to_txt(c: dict) -> str:
    lines = [
        "=" * 48,
        f"  CLIENTE — {c.get('tipo', '').upper()}",
        "=" * 48,
    ]
    if c["tipo"] == "PF":
        lines += [f"Nome        : {c.get('nome', '')}", f"CPF         : {c.get('cpf', '')}"]
    else:
        lines += [f"Razão Social: {c.get('nome', '')}", f"CNPJ        : {c.get('cpf', '')}"]
    lines += [
        f"Telefone    : {c.get('telefone', '')}",
        "",
        "── Endereço Pessoal / Comercial ──",
        f"Logradouro  : {c.get('end_log', '')}, {c.get('end_num', '')}",
    ]
    if c.get("end_comp"):
        lines.append(f"Complemento : {c['end_comp']}")
    lines += [
        f"Bairro      : {c.get('end_bairro', '')}",
        f"Cidade/UF   : {c.get('end_cidade', '')} - {c.get('end_estado', '')}",
        f"CEP         : {c.get('end_cep', '')}",
    ]
    if c.get("end_maps"):
        lines.append(f"Maps        : {c['end_maps']}")
    lines += ["", "── Endereço da Obra ──"]
    if c.get("obra_mesmo"):
        lines.append("(Mesmo endereço acima)")
    else:
        lines.append(f"Logradouro  : {c.get('obra_log', '')}, {c.get('obra_num', '')}")
        if c.get("obra_comp"):
            lines.append(f"Complemento : {c['obra_comp']}")
        lines += [
            f"Bairro      : {c.get('obra_bairro', '')}",
            f"Cidade/UF   : {c.get('obra_cidade', '')} - {c.get('obra_estado', '')}",
            f"CEP         : {c.get('obra_cep', '')}",
        ]
        if c.get("obra_maps"):
            lines.append(f"Maps        : {c['obra_maps']}")
    lines += ["=" * 48, f"Cadastrado  : {c.get('data', '')}"]
    return "\n".join(lines)
