"""Optional LLM access (Anthropic Messages API via stdlib urllib). No key -> returns None and the copilot
falls back to its deterministic, KG-only verbaliser. Set ANTHROPIC_API_KEY (and optionally LLM_MODEL)."""
import os, json, urllib.request, urllib.error

DEFAULT_MODEL = "claude-sonnet-5-5"


def available():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def ask(system, user, max_tokens=700, timeout=60):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    body = json.dumps({"model": os.environ.get("LLM_MODEL", DEFAULT_MODEL), "max_tokens": max_tokens,
                       "system": system, "messages": [{"role": "user", "content": user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, method="POST",
                                 headers={"content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip() or None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return None
