"""Página de login — /login"""

from nicegui import ui
from services.auth import check_login, login_user

_CSS = """
html, body, .nicegui-content {
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}
.dmc-login-wrap {
    min-height: 100vh;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #0C130C;
}
.dmc-login-card {
    background: var(--dmc-bg2, #111A11);
    border: 1px solid var(--dmc-b1, #1E301E);
    border-radius: 14px;
    padding: 40px 36px 36px;
    width: 360px;
    max-width: 95vw;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0;
}
.dmc-login-logo {
    font-size: 13px;
    font-weight: 700;
    color: var(--dmc-green, #4ADE80);
    letter-spacing: .18em;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.dmc-login-sub {
    font-size: 11px;
    color: var(--dmc-muted2, #527A52);
    letter-spacing: .12em;
    text-transform: uppercase;
    margin-bottom: 28px;
}
.dmc-login-field {
    width: 100%;
    margin-bottom: 14px;
}
.dmc-login-field label {
    display: block;
    font-size: 10px;
    color: var(--dmc-muted2, #527A52);
    letter-spacing: .12em;
    text-transform: uppercase;
    margin-bottom: 5px;
}
.dmc-login-field input {
    width: 100%;
    background: var(--dmc-bg, #0C130C);
    border: 1px solid var(--dmc-b1, #1E301E);
    border-radius: 7px;
    color: var(--dmc-fg, #D4E8D4);
    font-size: 14px;
    padding: 9px 12px;
    outline: none;
    box-sizing: border-box;
    transition: border-color .2s;
}
.dmc-login-field input:focus {
    border-color: var(--dmc-green, #4ADE80);
}
.dmc-login-btn {
    width: 100%;
    margin-top: 8px;
    height: 44px;
}
.dmc-login-err {
    margin-top: 12px;
    color: #F87171;
    font-size: 12px;
    text-align: center;
    min-height: 18px;
}
"""


@ui.page("/login")
def login_page():
    from services.auth import is_authenticated

    ui.dark_mode().enable()
    ui.add_head_html(f"<style>{_CSS}</style>")

    if is_authenticated():
        ui.navigate.to("/")
        return

    with ui.element("div").classes("dmc-login-wrap"):
        with ui.element("div").classes("dmc-login-card"):
            ui.html('<div class="dmc-login-logo">DMC Topografia</div>')
            ui.html('<div class="dmc-login-sub">Sistema de Arquivos</div>')

            ui.html("""
<div class="dmc-login-field">
  <label>Usuário / E-mail</label>
  <input id="li-user" type="text" autocomplete="username" placeholder="nome ou e-mail" />
</div>
<div class="dmc-login-field">
  <label>Senha</label>
  <input id="li-pass" type="password" autocomplete="current-password" placeholder="••••••••" />
</div>
""")

            btn = ui.element("button").classes("dmc-btn dmc-btn-primary dmc-login-btn")
            with btn:
                ui.html("Entrar")

            err_el = ui.html('<div class="dmc-login-err" id="li-err"></div>')

            async def do_login():
                result = await ui.run_javascript(
                    "({u: document.getElementById('li-user').value.trim(),"
                    " p: document.getElementById('li-pass').value})"
                )
                user_val = result.get("u", "")
                pass_val = result.get("p", "")
                user = check_login(user_val, pass_val)
                if user:
                    login_user(user)
                    if user.get("perfil") == "FUNCIONÁRIO CAMPO":
                        ui.navigate.to("/campo")
                    else:
                        is_mobile = await ui.run_javascript(
                            "window.innerWidth <= 768 || /Mobi|Android/i.test(navigator.userAgent)"
                        )
                        ui.navigate.to("/mobile" if is_mobile else "/")
                else:
                    await ui.run_javascript(
                        "document.getElementById('li-err').textContent='Usuário ou senha incorretos';"
                        "document.getElementById('li-pass').value='';"
                        "document.getElementById('li-pass').focus();"
                    )

            btn.on("click", do_login)

            ui.run_javascript("""
setTimeout(function(){
  var p = document.getElementById('li-pass');
  if(p) p.addEventListener('keydown', function(e){
    if(e.key==='Enter') document.querySelector('.dmc-login-btn').click();
  });
  var u = document.getElementById('li-user');
  if(u) u.addEventListener('keydown', function(e){
    if(e.key==='Enter') p && p.focus();
  });
}, 300);
""")
