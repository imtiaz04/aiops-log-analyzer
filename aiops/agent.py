import json
import re
import urllib.error
import urllib.request

ALERT_LEVELS = ("CRITICAL", "ERROR", "WARNING")

_OLLAMA_BASE = "http://localhost:11434"
_PREFERRED_MODELS = ["llama3", "llama3.1", "llama3.2", "gemma", "gemma2", "mistral"]

_SYSTEM_PROMPT = """\
You are an AIOps expert. Analyze the log anomaly and respond with EXACTLY these four labeled lines and no other text:
Root cause: <one sentence explaining why this happened>
Impact: <one sentence describing the effect on the system>
Recommended fix: <one or two concrete steps to resolve this>
Prevention: <one or two measures to prevent recurrence>\
"""

_LEVEL_IMPACT = {
    "CRITICAL": "Service is likely unavailable or severely degraded.",
    "ERROR": "The affected operation failed and may be impacting users.",
    "WARNING": "System stability or performance may be degraded.",
}

_FIELD_PREFIXES = [
    ("root_cause",  ["root cause", "root_cause"]),
    ("impact",      ["impact"]),
    ("fix",         ["recommended fix", "fix"]),
    ("prevention",  ["prevention"]),
]


def detect_anomalies(lines: list[str]) -> list[tuple[str, int, str]]:
    """Return (level, line_number, line) for each anomalous log line."""
    alerts = []
    for i, line in enumerate(lines, 1):
        for level in ALERT_LEVELS:
            if level in line:
                alerts.append((level, i, line))
                break
    return alerts


def summarize(alerts: list[tuple[str, int, str]]) -> dict[str, int]:
    counts: dict[str, int] = {level: 0 for level in ALERT_LEVELS}
    for level, _, _ in alerts:
        counts[level] += 1
    return counts


def _pick_model() -> str:
    """Return the best available Ollama model, raising ConnectionError if unreachable."""
    try:
        with urllib.request.urlopen(f"{_OLLAMA_BASE}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read())
    except urllib.error.URLError:
        raise ConnectionError(
            "Ollama is not running. Start it with:\n\n    ollama serve\n"
        )

    available = [m["name"] for m in data.get("models", [])]
    if not available:
        raise RuntimeError(
            "No models found in Ollama. Pull one first:\n\n"
            "    ollama pull llama3\n"
        )

    for preferred in _PREFERRED_MODELS:
        for name in available:
            if name == preferred or name.startswith(preferred + ":") or name.startswith(preferred + "."):
                return name

    return available[0]


def _query_ollama(model: str, level: str, line_num: int, log_line: str) -> str:
    """Send a single anomaly to Ollama and return the raw response text."""
    user_msg = f"Log anomaly: [{level}] line {line_num}: {log_line.strip()}"

    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{_OLLAMA_BASE}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError:
        raise ConnectionError(
            "Ollama is not running. Start it with:\n\n    ollama serve\n"
        )

    return result["message"]["content"].strip()


def _parse_fields(text: str, level: str, log_line: str) -> dict[str, str]:
    """
    Extract the 4 fixed fields from Ollama's response by prefix matching.
    Falls back to safe defaults for any field that is missing or empty.
    """
    # Strip markdown bold/italic markers so "**Root cause:**" still matches
    clean = re.sub(r"\*+", "", text)

    fields: dict[str, str] = {}
    for key, prefixes in _FIELD_PREFIXES:
        for raw_line in clean.splitlines():
            stripped = raw_line.strip()
            low = stripped.lower()
            for prefix in prefixes:
                if low.startswith(prefix + ":"):
                    value = stripped[len(prefix) + 1:].strip()
                    if value:
                        fields[key] = value
                        break
            if key in fields:
                break

    # Fallbacks derived from the log line itself
    component = log_line.strip().split()[-1] if log_line.strip() else "unknown component"
    if "root_cause" not in fields:
        fields["root_cause"] = (
            f"Exact cause unclear; review the {level.lower()} condition near: {component}"
        )
    if "impact" not in fields:
        fields["impact"] = _LEVEL_IMPACT.get(level, "System behavior may be affected.")
    if "fix" not in fields:
        fields["fix"] = "Investigate the affected component and review recent changes or deployments."
    if "prevention" not in fields:
        fields["prevention"] = "Add monitoring and alerting for this condition to catch it earlier."

    return fields


def explain_anomalies(
    alerts: list[tuple[str, int, str]], model: str | None = None
) -> tuple[str, list[dict]]:
    """
    Query Ollama once per alert and return structured field dicts.
    Returns (model_name, list_of_field_dicts).
    """
    model = model or _pick_model()
    results = []
    for level, line_num, log_line in alerts:
        raw = _query_ollama(model, level, line_num, log_line)
        results.append(_parse_fields(raw, level, log_line))
    return model, results
