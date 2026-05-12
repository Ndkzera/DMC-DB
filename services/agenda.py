"""Integração com Google Calendar API."""

from datetime import datetime, timedelta
from pathlib import Path

from config import CONFIG_DIR

SCOPES      = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = "primary"
TZ_BRASIL   = "America/Sao_Paulo"

# Procura credentials.json na ordem: pasta services/ → raiz do projeto → CONFIG_DIR
_HERE       = Path(__file__).parent          # c:\DB DMC\services
_ROOT       = _HERE.parent                   # c:\DB DMC
_CANDIDATES = [_HERE, _ROOT, CONFIG_DIR]

def _find_credentials() -> Path:
    for folder in _CANDIDATES:
        p = folder / "credentials.json"
        if p.exists():
            return p
    return CONFIG_DIR / "credentials.json"   # fallback (pode não existir)

CREDENTIALS_FILE = _find_credentials()
TOKEN_FILE       = CREDENTIALS_FILE.parent / "token.json"  # mesma pasta do credentials.json


# ── Autenticação ──────────────────────────────────────────────────────

def _load_creds():
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request

        if not TOKEN_FILE.exists():
            return None
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
            except Exception:
                return None
        return creds if creds.valid else None
    except Exception:
        return None


def is_connected() -> bool:
    return _load_creds() is not None


def _get_service():
    creds = _load_creds()
    if not creds:
        raise RuntimeError("not_authenticated")
    from googleapiclient.discovery import build
    return build("calendar", "v3", credentials=creds)


_auth_state: dict = {}  # flow pendente entre start_auth_flow e complete_auth_with_code


def start_auth_flow(base_url: str = "http://localhost:8080") -> str:
    """Gera URL de autorização Google usando /oauth_callback do próprio NiceGUI.
    base_url deve ser a URL acessível pelo browser (localhost ou tunnel)."""
    if not CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"credentials.json não encontrado em:\n{CREDENTIALS_FILE}\n"
            "Baixe o arquivo no Google Cloud Console e coloque-o nessa pasta."
        )
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    flow.redirect_uri = f"{base_url.rstrip('/')}/oauth_callback"
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    _auth_state["flow"] = flow
    return auth_url


def complete_auth_with_code(code: str) -> None:
    """Chamado pela rota /oauth_callback após o Google redirecionar de volta."""
    flow = _auth_state.get("flow")
    if not flow:
        raise RuntimeError("Nenhum fluxo OAuth pendente.")
    flow.fetch_token(code=code)
    TOKEN_FILE.write_text(flow.credentials.to_json(), encoding="utf-8")
    _auth_state.clear()


def disconnect():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()


# ── Eventos ───────────────────────────────────────────────────────────

def get_events_for_month(year: int, month: int) -> list[dict]:
    import calendar as _cal
    svc = _get_service()
    last_day = _cal.monthrange(year, month)[1]
    time_min = f"{year:04d}-{month:02d}-01T00:00:00Z"
    time_max = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z"
    result = svc.events().list(
        calendarId=CALENDAR_ID,
        timeMin=time_min,
        timeMax=time_max,
        maxResults=200,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return result.get("items", [])


def get_events(days: int = 30, max_results: int = 50) -> list[dict]:
    svc = _get_service()
    now = datetime.utcnow().isoformat() + "Z"
    end = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
    result = svc.events().list(
        calendarId=CALENDAR_ID,
        timeMin=now,
        timeMax=end,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    return result.get("items", [])


def create_event(
    title: str,
    description: str = "",
    location: str   = "",
    all_day: bool   = False,
    start_date: str = "",   # "YYYY-MM-DD"
    end_date: str   = "",   # "YYYY-MM-DD" (exclusive para all-day)
    start_iso: str  = "",   # "YYYY-MM-DDTHH:MM:SS"
    end_iso: str    = "",   # "YYYY-MM-DDTHH:MM:SS"
) -> dict:
    svc = _get_service()
    if all_day:
        body = {
            "summary":     title,
            "description": description,
            "location":    location,
            "start": {"date": start_date},
            "end":   {"date": end_date},
        }
    else:
        body = {
            "summary":     title,
            "description": description,
            "location":    location,
            "start": {"dateTime": start_iso, "timeZone": TZ_BRASIL},
            "end":   {"dateTime": end_iso,   "timeZone": TZ_BRASIL},
        }
    return svc.events().insert(calendarId=CALENDAR_ID, body=body).execute()


def delete_event(event_id: str):
    svc = _get_service()
    svc.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()


# ── Helpers de formatação ─────────────────────────────────────────────

_MESES = ["jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez"]
_DIAS  = ["seg","ter","qua","qui","sex","sáb","dom"]


def fmt_event(evt: dict) -> dict:
    """Normaliza um evento para exibição."""
    start = evt.get("start", {})
    end   = evt.get("end",   {})

    if "dateTime" in start:
        dt_start = datetime.fromisoformat(start["dateTime"])
        dt_end   = datetime.fromisoformat(end.get("dateTime", start["dateTime"]))
        all_day  = False
        time_str = f"{dt_start.strftime('%H:%M')} – {dt_end.strftime('%H:%M')}"
        date_key = dt_start.date().isoformat()
        date_label = (
            f"{_DIAS[dt_start.weekday()].upper()} · "
            f"{dt_start.day:02d} {_MESES[dt_start.month - 1].upper()}"
        )
    else:
        d = datetime.strptime(start.get("date", "1970-01-01"), "%Y-%m-%d")
        all_day    = True
        time_str   = "Dia inteiro"
        date_key   = d.date().isoformat()
        date_label = f"{_DIAS[d.weekday()].upper()} · {d.day:02d} {_MESES[d.month - 1].upper()}"

    today = datetime.utcnow().date().isoformat()
    is_today = date_key == today

    return {
        "id":         evt.get("id", ""),
        "title":      evt.get("summary", "(sem título)"),
        "description":evt.get("description", ""),
        "location":   evt.get("location", ""),
        "all_day":    all_day,
        "time_str":   time_str,
        "date_key":   date_key,
        "date_label": date_label,
        "is_today":   is_today,
        "color":      evt.get("colorId", ""),
        "html_link":  evt.get("htmlLink", ""),
    }
