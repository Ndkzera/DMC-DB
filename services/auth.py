"""Autenticação simples — usuários em JSON, senhas com sha256."""

import hashlib
import json
import uuid
from nicegui import app
from config import CONFIG_DIR

USUARIOS_FILE = CONFIG_DIR / "usuarios.json"

# Perfis disponíveis — ordem = nível de acesso (0 = maior)
PERFIS = [
    "DESENVOLVEDOR",
    "ADMINISTRADOR",
    "FUNCIONÁRIO PRIORITÁRIO",
    "FUNCIONÁRIO",
    "FUNCIONÁRIO CAMPO",
]

# Cor de badge por perfil
PERFIL_CORES = {
    "DESENVOLVEDOR":          ("#C4B5FD", "rgba(196,181,253,.12)", "rgba(196,181,253,.3)"),
    "ADMINISTRADOR":          ("#FBBF24", "rgba(251,191,36,.10)",  "rgba(251,191,36,.28)"),
    "FUNCIONÁRIO PRIORITÁRIO":("#60A5FA", "rgba(96,165,250,.10)",  "rgba(96,165,250,.28)"),
    "FUNCIONÁRIO":            ("#4ADE80", "rgba(74,222,128,.08)",  "rgba(74,222,128,.25)"),
    "FUNCIONÁRIO CAMPO":      ("#34D399", "rgba(52,211,153,.08)",  "rgba(52,211,153,.25)"),
}


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def _load() -> list:
    try:
        return json.loads(USUARIOS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(users: list) -> None:
    USUARIOS_FILE.write_text(
        json.dumps(users, ensure_ascii=False, indent=2), encoding="utf-8"
    )


_DEFAULT_EMAIL = "n_dk@live.com"
_DEFAULT_NOME  = "Nilton Jr"


def ensure_default_user() -> None:
    """Cria ou corrige o usuário padrão."""
    users = _load()
    default = next((u for u in users if u.get("perfil") == "DESENVOLVEDOR" or u.get("admin")), None)
    if default is None:
        _save([{
            "id":         str(uuid.uuid4()),
            "nome":       _DEFAULT_NOME,
            "email":      _DEFAULT_EMAIL,
            "telefone":   "",
            "cargo":      "Desenvolvedor",
            "senha_hash": _hash("1234"),
            "perfil":     "DESENVOLVEDOR",
            "admin":      True,
        }])
        return
    changed = False
    if default.get("email") != _DEFAULT_EMAIL:
        default["email"] = _DEFAULT_EMAIL
        changed = True
    if default.get("nome") != _DEFAULT_NOME:
        default["nome"] = _DEFAULT_NOME
        changed = True
    if not default.get("perfil"):
        default["perfil"] = "DESENVOLVEDOR"
        changed = True
    if changed:
        _save(users)


def check_login(email_or_nome: str, senha: str) -> dict | None:
    """Retorna o usuário se credenciais válidas, senão None."""
    h = _hash(senha)
    for u in _load():
        if (u.get("email") == email_or_nome or u.get("nome") == email_or_nome) and u.get("senha_hash") == h:
            return u
    return None


def is_authenticated() -> bool:
    return bool(app.storage.user.get("dmc_logged_in"))


def login_user(user: dict) -> None:
    app.storage.user["dmc_logged_in"] = True
    app.storage.user["dmc_user_nome"]  = user.get("nome", "")
    app.storage.user["dmc_user_email"] = user.get("email", "")
    app.storage.user["dmc_user_perfil"]= user.get("perfil", "FUNCIONÁRIO")
    app.storage.user["dmc_user_admin"] = user.get("admin", False)


def logout_user() -> None:
    app.storage.user["dmc_logged_in"] = False
    for k in ("dmc_user_nome", "dmc_user_email", "dmc_user_perfil", "dmc_user_admin"):
        app.storage.user.pop(k, None)


def current_user_name() -> str:
    return app.storage.user.get("dmc_user_nome", "")


def current_user_perfil() -> str:
    return app.storage.user.get("dmc_user_perfil", "FUNCIONÁRIO")


def current_user_label() -> str:
    """Melhor identificador do usuário: nome → e-mail → perfil."""
    nome = app.storage.user.get("dmc_user_nome", "").strip()
    if nome:
        return nome
    email = app.storage.user.get("dmc_user_email", "").strip()
    if email:
        return email.split("@")[0]
    return app.storage.user.get("dmc_user_perfil", "Usuário")
