"""Configuração de permissões de acesso por perfil — persistência em SQLite."""

import json
from services.auth import PERFIS
from services.database import get_conn

FEATURES: list[tuple[str, str, str]] = [
    # Sistema
    ("login_criar",        "Criar login de acesso ao sistema",     "Sistema"),
    ("login_logar",        "Logar no sistema",                     "Sistema"),
    ("login_sair",         "Sair do sistema",                      "Sistema"),
    ("campo_login",        "Logar somente para registro de campo", "Sistema"),
    # Agenda
    ("agenda_criar",       "Criar eventos na agenda",              "Agenda"),
    ("agenda_novo",        "Novo evento",                          "Agenda"),
    ("agenda_google",      "Conectar Google",                      "Agenda"),
    # Clientes
    ("cli_cadastrar",      "Cadastrar cliente",                    "Clientes"),
    ("cli_nome",           "Procurar por nome",                    "Clientes"),
    ("cli_telefone",       "Procurar por telefone",                "Clientes"),
    ("cli_cpf",            "Procurar por CPF/CNPJ",                "Clientes"),
    ("cli_editar",         "Editar clientes",                      "Clientes"),
    # Obras
    ("obras_nova",         "Nova obra",                            "Obras"),
    ("obras_ver",          "Ver obras",                            "Obras"),
    # Administrativo
    ("adm_agenda_campo",   "Agenda de campo",                      "Administrativo"),
    ("adm_checkin",        "Checkin/out",                          "Administrativo"),
    ("adm_registro",       "Registro de campo",                    "Administrativo"),
    ("adm_historico",      "Histórico de checkin/out",             "Administrativo"),
    ("adm_links",          "Links rápidos",                        "Administrativo"),
    ("adm_gestao_contas",  "Gestão de Contas",                     "Administrativo"),
    ("adm_config_acesso",  "Configuração de Acesso",               "Administrativo"),
    ("adm_log",            "Log de Atividades",                    "Administrativo"),
    # Arquivos
    ("arq_visualizar",     "Visualização dos arquivos",            "Arquivos"),
    ("arq_upload",         "Upload de arquivos",                   "Arquivos"),
    ("arq_pasta",          "Criar nova pasta",                     "Arquivos"),
    ("arq_voltar",         "Voltar pasta",                         "Arquivos"),
    ("arq_deletar",        "Deletar arquivos",                     "Arquivos"),
    ("arq_compartilhar",   "Compartilhar arquivos",                "Arquivos"),
    ("arq_lixeira",        "Lixeira",                              "Arquivos"),
]

_FIELD_DEFAULTS: dict[str, dict[str, bool]] = {
    "DESENVOLVEDOR":           {fid: True  for fid, _, _ in FEATURES},
    "ADMINISTRADOR":           {fid: True  for fid, _, _ in FEATURES},
    "FUNCIONÁRIO PRIORITÁRIO": {fid: True  for fid, _, _ in FEATURES},
    "FUNCIONÁRIO":             {fid: True  for fid, _, _ in FEATURES},
    "FUNCIONÁRIO CAMPO":       {fid: False for fid, _, _ in FEATURES},
}
for _f in ("campo_login", "login_logar", "login_sair", "adm_checkin",
           "adm_registro", "adm_links", "arq_visualizar"):
    _FIELD_DEFAULTS["FUNCIONÁRIO CAMPO"][_f] = True

for _p in ("FUNCIONÁRIO PRIORITÁRIO", "FUNCIONÁRIO", "FUNCIONÁRIO CAMPO"):
    _FIELD_DEFAULTS[_p]["adm_gestao_contas"] = False
    _FIELD_DEFAULTS[_p]["adm_config_acesso"] = False
    _FIELD_DEFAULTS[_p]["adm_log"]           = False

for _p in PERFIS:
    _FIELD_DEFAULTS[_p]["login_logar"] = True
    _FIELD_DEFAULTS[_p]["login_sair"]  = True


def _default() -> dict:
    return {
        p: dict(_FIELD_DEFAULTS.get(p, {fid: True for fid, _, _ in FEATURES}))
        for p in PERFIS
    }


def load_access() -> dict:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT perfil, config FROM acesso").fetchall()
    finally:
        conn.close()

    if not rows:
        return _default()

    default = _default()
    data: dict = {}
    for row in rows:
        try:
            cfg = json.loads(row["config"])
        except Exception:
            cfg = {}
        data[row["perfil"]] = cfg

    for p in PERFIS:
        data.setdefault(p, {})
        for fid, _, _ in FEATURES:
            data[p].setdefault(fid, default[p].get(fid, True))

    return data


def save_access(config: dict) -> None:
    conn = get_conn()
    try:
        for perfil, cfg in config.items():
            conn.execute(
                "INSERT OR REPLACE INTO acesso(perfil, config) VALUES(?,?)",
                (perfil, json.dumps(cfg, ensure_ascii=False)),
            )
        conn.commit()
    finally:
        conn.close()


def has_access(perfil: str, feature_id: str) -> bool:
    return load_access().get(perfil, {}).get(feature_id, True)
