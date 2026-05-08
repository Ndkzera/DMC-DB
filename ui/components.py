"""Widgets reutilizáveis da interface."""

from nicegui import ui


def tbtn(label: str, icon: str = "", primary: bool = False) -> ui.element:
    variant = "dmc-btn-primary" if primary else "dmc-btn-secondary"
    b = ui.element("button").classes(f"dmc-btn {variant} dmc-btn-sm")
    with b:
        if icon:
            ui.html(f'<span class="material-icons">{icon}</span>')
        ui.html(f"<span>{label}</span>")
    return b


def sec_hdr(text: str) -> None:
    with ui.element("div").style(
        "display:flex;align-items:center;gap:10px;margin-bottom:12px;"
    ):
        ui.html(
            f'<span style="font:500 10px var(--dmc-fm);color:var(--dmc-muted2);'
            f'letter-spacing:.15em;text-transform:uppercase;white-space:nowrap">{text}</span>'
        )
        ui.element("div").style("flex:1;height:1px;background:var(--dmc-b1)")
