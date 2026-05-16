"""CRUD de Contas a Pagar / Receber e Categorias."""

import uuid
from datetime import datetime

from services.database import get_conn


# ── Helpers ──────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def _today() -> str:
    return datetime.now().strftime("%d/%m/%Y")

def _r(valor: float) -> float:
    return round(float(valor or 0), 2)


# ── Categorias de Contas a Pagar ─────────────────────────────────────────

def load_categorias_pagar() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM categorias_pagar ORDER BY nome COLLATE NOCASE"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_categoria_pagar(nome: str, cor: str = "#8BAA8B") -> dict:
    cat = {"id": str(uuid.uuid4()), "nome": nome.strip(), "cor": cor}
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO categorias_pagar(id, nome, cor) VALUES(?,?,?)",
            (cat["id"], cat["nome"], cat["cor"]),
        )
        conn.commit()
    finally:
        conn.close()
    return cat


def update_categoria_pagar(cat_id: str, nome: str, cor: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE categorias_pagar SET nome=?, cor=? WHERE id=?",
            (nome.strip(), cor, cat_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_categoria_pagar(cat_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM categorias_pagar WHERE id=?", (cat_id,))
        conn.commit()
    finally:
        conn.close()


# ── Contas a Pagar ────────────────────────────────────────────────────────

def load_contas_pagar() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT cp.*, cat.nome AS categoria_nome, cat.cor AS categoria_cor "
            "FROM contas_pagar cp "
            "LEFT JOIN categorias_pagar cat ON cat.id = cp.categoria_id "
            "WHERE cp.deletado_em IS NULL "
            "ORDER BY cp.data_venc ASC, cp.data_criacao DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def load_contas_pagar_deletadas() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT cp.*, cat.nome AS categoria_nome, cat.cor AS categoria_cor "
            "FROM contas_pagar cp "
            "LEFT JOIN categorias_pagar cat ON cat.id = cp.categoria_id "
            "WHERE cp.deletado_em IS NOT NULL "
            "ORDER BY cp.deletado_em DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_conta_pagar(conta: dict) -> dict:
    conta["id"] = conta.get("id") or str(uuid.uuid4())
    conta.setdefault("data_criacao", _now())
    conta.setdefault("status", "pendente")
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO contas_pagar(id,descricao,categoria_id,obra_id,obra_nome,"
            "valor,data_venc,data_pag,status,observacao,data_criacao) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                conta["id"], conta.get("descricao",""),
                conta.get("categoria_id",""), conta.get("obra_id",""),
                conta.get("obra_nome",""), _r(conta.get("valor",0)),
                conta.get("data_venc",""), conta.get("data_pag",""),
                conta["status"], conta.get("observacao",""),
                conta["data_criacao"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return conta


def update_conta_pagar(conta_id: str, **fields) -> None:
    allowed = {"descricao","categoria_id","obra_id","obra_nome","valor",
               "data_venc","data_pag","status","observacao"}
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return
    conn = get_conn()
    try:
        placeholders = ", ".join(f"{k}=?" for k in sets)
        conn.execute(
            f"UPDATE contas_pagar SET {placeholders} WHERE id=?",
            (*sets.values(), conta_id),
        )
        conn.commit()
    finally:
        conn.close()


def pagar_conta(conta_id: str) -> None:
    update_conta_pagar(conta_id, status="pago", data_pag=_today())


def cancelar_conta_pagar(conta_id: str) -> None:
    update_conta_pagar(conta_id, status="cancelado")


def delete_conta_pagar(conta_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE contas_pagar SET deletado_em=? WHERE id=?",
            (_now(), conta_id),
        )
        conn.commit()
    finally:
        conn.close()


def restore_conta_pagar(conta_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE contas_pagar SET deletado_em=NULL WHERE id=?", (conta_id,))
        conn.commit()
    finally:
        conn.close()


def purge_conta_pagar(conta_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM contas_pagar WHERE id=?", (conta_id,))
        conn.commit()
    finally:
        conn.close()


# ── Contas a Receber ──────────────────────────────────────────────────────

def load_contas_receber() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM contas_receber WHERE deletado_em IS NULL "
            "ORDER BY data_venc ASC, data_criacao DESC"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            pags = conn.execute(
                "SELECT * FROM pagamentos_receber WHERE conta_receber_id=? ORDER BY data ASC",
                (d["id"],),
            ).fetchall()
            d["pagamentos"] = [dict(p) for p in pags]
            result.append(d)
        return result
    finally:
        conn.close()


def load_contas_receber_deletadas() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM contas_receber WHERE deletado_em IS NOT NULL "
            "ORDER BY deletado_em DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_conta_receber(conta: dict) -> dict:
    conta["id"] = conta.get("id") or str(uuid.uuid4())
    conta.setdefault("data_criacao", _now())
    conta.setdefault("status", "aberto")
    conta.setdefault("valor_pago", 0.0)
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO contas_receber(id,descricao,cliente_nome,cliente_cpf,"
            "obra_id,obra_nome,valor_total,valor_pago,parcelas,status,data_venc,data_criacao) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                conta["id"], conta.get("descricao",""),
                conta.get("cliente_nome",""), conta.get("cliente_cpf",""),
                conta.get("obra_id",""), conta.get("obra_nome",""),
                _r(conta.get("valor_total",0)), _r(conta.get("valor_pago",0)),
                int(conta.get("parcelas",1)), conta["status"],
                conta.get("data_venc",""), conta["data_criacao"],
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return conta


def delete_conta_receber(conta_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE contas_receber SET deletado_em=? WHERE id=?",
            (_now(), conta_id),
        )
        conn.commit()
    finally:
        conn.close()


def restore_conta_receber(conta_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute("UPDATE contas_receber SET deletado_em=NULL WHERE id=?", (conta_id,))
        conn.commit()
    finally:
        conn.close()


def purge_conta_receber(conta_id: str) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM pagamentos_receber WHERE conta_receber_id=?", (conta_id,))
        conn.execute("DELETE FROM contas_receber WHERE id=?", (conta_id,))
        conn.commit()
    finally:
        conn.close()


# ── Pagamentos ────────────────────────────────────────────────────────────

def add_pagamento(conta_receber_id: str, valor: float,
                  data: str = "", observacao: str = "") -> dict:
    pag = {
        "id": str(uuid.uuid4()),
        "conta_receber_id": conta_receber_id,
        "valor": _r(valor),
        "data": data or _today(),
        "observacao": observacao,
    }
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO pagamentos_receber(id,conta_receber_id,valor,data,observacao) "
            "VALUES(?,?,?,?,?)",
            (pag["id"], pag["conta_receber_id"], pag["valor"], pag["data"], pag["observacao"]),
        )
        # Atualiza valor_pago e status na conta
        total_pago = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM pagamentos_receber WHERE conta_receber_id=?",
            (conta_receber_id,),
        ).fetchone()[0]
        total_pago = _r(total_pago)
        valor_total = conn.execute(
            "SELECT valor_total FROM contas_receber WHERE id=?", (conta_receber_id,)
        ).fetchone()
        if valor_total:
            vt = _r(valor_total[0])
            if total_pago >= vt:
                novo_status = "quitado"
            elif total_pago > 0:
                novo_status = "parcial"
            else:
                novo_status = "aberto"
            conn.execute(
                "UPDATE contas_receber SET valor_pago=?, status=? WHERE id=?",
                (total_pago, novo_status, conta_receber_id),
            )
        conn.commit()
    finally:
        conn.close()
    return pag


def delete_pagamento(pagamento_id: str) -> None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT conta_receber_id FROM pagamentos_receber WHERE id=?", (pagamento_id,)
        ).fetchone()
        if not row:
            return
        conta_id = row[0]
        conn.execute("DELETE FROM pagamentos_receber WHERE id=?", (pagamento_id,))
        total_pago = conn.execute(
            "SELECT COALESCE(SUM(valor),0) FROM pagamentos_receber WHERE conta_receber_id=?",
            (conta_id,),
        ).fetchone()[0]
        total_pago = _r(total_pago)
        valor_total = conn.execute(
            "SELECT valor_total FROM contas_receber WHERE id=?", (conta_id,)
        ).fetchone()
        if valor_total:
            vt = _r(valor_total[0])
            if total_pago >= vt:
                novo_status = "quitado"
            elif total_pago > 0:
                novo_status = "parcial"
            else:
                novo_status = "aberto"
            conn.execute(
                "UPDATE contas_receber SET valor_pago=?, status=? WHERE id=?",
                (total_pago, novo_status, conta_id),
            )
        conn.commit()
    finally:
        conn.close()


# ── Sumários ──────────────────────────────────────────────────────────────

def resumo_pagar() -> dict:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT status, SUM(valor) FROM contas_pagar WHERE deletado_em IS NULL GROUP BY status"
        ).fetchall()
    finally:
        conn.close()
    r = {"pendente": 0.0, "pago": 0.0, "cancelado": 0.0, "total": 0.0}
    for status, total in rows:
        r[status] = _r(total or 0)
    r["total"] = _r(r["pendente"] + r["pago"])
    return r


def resumo_receber() -> dict:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT status, SUM(valor_total), SUM(valor_pago) FROM contas_receber "
            "WHERE deletado_em IS NULL GROUP BY status"
        ).fetchall()
    finally:
        conn.close()
    r = {"aberto": 0.0, "parcial": 0.0, "quitado": 0.0, "cancelado": 0.0,
         "total": 0.0, "recebido": 0.0, "a_receber": 0.0}
    for status, total, pago in rows:
        r[status] = _r(total or 0)
        r["recebido"] += _r(pago or 0)
    r["total"] = _r(r["aberto"] + r["parcial"] + r["quitado"])
    r["a_receber"] = _r(r["total"] - r["recebido"])
    return r


# ── Notificações ──────────────────────────────────────────────────────────────

def get_notificacoes() -> list[dict]:
    """
    Retorna lista de notificações ativas:
      - Contas a pagar vencidas (status=pendente, data_venc < hoje)
      - Contas a pagar vencendo em até 7 dias
      - Contas a receber vencidas (status=aberto|parcial, data_venc < hoje)
    Each dict: {tipo, titulo, detalhe, nivel}  nivel: 'danger'|'warning'|'info'
    """
    from datetime import date as _date_cls
    hoje = _date_cls.today()

    def _parse_br(s: str):
        try:
            d, m, y = s.split("/")
            return _date_cls(int(y), int(m), int(d))
        except Exception:
            return None

    notifs: list[dict] = []
    conn = get_conn()
    try:
        rows_p = conn.execute(
            "SELECT descricao, valor, data_venc FROM contas_pagar "
            "WHERE status='pendente' AND deletado_em IS NULL AND data_venc != ''"
        ).fetchall()
        rows_r = conn.execute(
            "SELECT descricao, valor_total, data_venc FROM contas_receber "
            "WHERE status IN ('aberto','parcial') AND deletado_em IS NULL AND data_venc != ''"
        ).fetchall()
    finally:
        conn.close()

    vencidas_p = vencendo_p = vencidas_r = 0
    for desc, val, dv in rows_p:
        d = _parse_br(dv)
        if d is None:
            continue
        delta = (d - hoje).days
        if delta < 0:
            vencidas_p += 1
        elif delta <= 7:
            vencendo_p += 1

    for desc, val, dv in rows_r:
        d = _parse_br(dv)
        if d is None:
            continue
        if (d - hoje).days < 0:
            vencidas_r += 1

    if vencidas_p:
        notifs.append({
            "tipo": "pagar_vencida",
            "titulo": f"{vencidas_p} conta(s) a pagar vencida(s)",
            "detalhe": "Ação imediata necessária",
            "nivel": "danger",
            "icon": "payments",
        })
    if vencendo_p:
        notifs.append({
            "tipo": "pagar_vencendo",
            "titulo": f"{vencendo_p} conta(s) a pagar vencem em até 7 dias",
            "detalhe": "Verifique o módulo financeiro",
            "nivel": "warning",
            "icon": "schedule",
        })
    if vencidas_r:
        notifs.append({
            "tipo": "receber_vencida",
            "titulo": f"{vencidas_r} conta(s) a receber vencida(s)",
            "detalhe": "Clientes com pagamento em atraso",
            "nivel": "warning",
            "icon": "account_balance_wallet",
        })
    return notifs
