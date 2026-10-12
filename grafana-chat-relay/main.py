import hmac
import os
import time
import functions_framework
import requests

DEFAULT_SPACE = "spaces/AAQAD9vqp48"
METADATA_TOKEN_URL = (
    "http://metadata.google.internal/computeMetadata/v1/instance/"
    "service-accounts/default/token?scopes=https://www.googleapis.com/auth/chat.bot"
)

_token = None
_token_expiry = 0.0


def get_chat_token():
    global _token, _token_expiry
    now = time.time()
    if _token and now < _token_expiry - 60:
        return _token
    resp = requests.get(
        METADATA_TOKEN_URL,
        headers={"Metadata-Flavor": "Google"},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    _token = data["access_token"]
    _token_expiry = now + float(data.get("expires_in", 3600))
    return _token


def format_alert(alert, default_status, common_labels):
    status = alert.get("status", default_status).upper()
    labels = {**common_labels, **(alert.get("labels") or {})}
    annotations = alert.get("annotations") or {}
    name = labels.get("alertname", "Alert")
    scope = (
        "/".join(filter(None, [labels.get("org"), labels.get("platform")]))
        or "/".join(filter(None, [labels.get("pipeline"), labels.get("job")]))
        or labels.get("source", "")
    )
    values = alert.get("values") or {}
    val = values.get("A", next(iter(values.values()), None))
    if isinstance(val, float):
        val = int(val) if val.is_integer() else round(val, 2)

    parts = [f"*[{status}] {name}*"]
    if scope:
        parts.append(f"`{scope}`")
    if val is not None:
        parts.append(f"(value={val})")
    summary = annotations.get("summary") or annotations.get("description")
    if summary:
        parts.append(f"— {summary}")
    url = alert.get("generatorURL")
    if url:
        parts.append(f"(<{url}|rule>)")
    return " ".join(parts)


def format_message(payload):
    status = payload.get("status", "firing")
    common_labels = payload.get("commonLabels") or {}
    alerts = payload.get("alerts") or []
    if not alerts:
        title = payload.get("title") or f"[{status.upper()}] Alert"
        msg = payload.get("message") or ""
        return f"*{title}*\n{msg}".strip()
    return "\n".join(format_alert(a, status, common_labels) for a in alerts)


@functions_framework.http
def relay(request):
    if request.method != "POST":
        return ("Method Not Allowed\n", 405)

    secret = os.environ.get("WEBHOOK_SECRET", "").strip()
    auth = request.headers.get("Authorization", "")
    if not secret or not hmac.compare_digest(auth.encode(), f"Bearer {secret}".encode()):
        return ("Unauthorized\n", 401)

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return ("Bad Request\n", 400)

    space = os.environ.get("CHAT_SPACE", DEFAULT_SPACE).strip()
    if not space.startswith("spaces/"):
        space = f"spaces/{space}"

    resp = requests.post(
        f"https://chat.googleapis.com/v1/{space}/messages",
        headers={"Authorization": f"Bearer {get_chat_token()}"},
        json={"text": format_message(payload)},
        timeout=10,
    )
    if resp.status_code >= 400:
        return (f"Chat API error: {resp.status_code}\n", 502)
    return ("OK\n", 200)
