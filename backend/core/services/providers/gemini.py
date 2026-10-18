import logging
import time
from django.conf import settings
from django.core.cache import cache
from ..tables import SchemaError, extract_json, validate_table
from .base import PROMPT, PageResult, Provider, ProviderError

log = logging.getLogger(__name__)

COOLDOWN_SECONDS = 60


def _model():
    from ...models import SiteSettings
    try:
        return SiteSettings.get().gemini_model or settings.AUTOMCS.get("GEMINI_MODEL", "gemini-3.8-flash")
    except Exception:
        return settings.AUTOMCS.get("GEMINI_MODEL", "gemini-3.8-flash")


def get_key_slot(index: int) -> dict:
    """Returns information about slot index (1..4)."""
    from ...models import SiteSettings
    try:
        ss = SiteSettings.get()
        db_key = getattr(ss, f"gemini_api_key_{index}", "").strip()
    except Exception:
        db_key = ""

    env_key = str(settings.AUTOMCS.get(f"GEMINI_API_KEY_{index}") or "").strip()
    if not env_key and index == 1:
        env_key = str(settings.AUTOMCS.get("GEMINI_API_KEY") or "").strip()

    if db_key:
        key = db_key
        source = "settings"
    elif env_key:
        key = env_key
        source = "env"
    else:
        key = ""
        source = "none"

    cooldown_until = cache.get(f"automcs_gemini_cooldown_{index}", 0)
    now = time.time()
    remaining = max(0, int(cooldown_until - now)) if cooldown_until > now else 0

    return {
        "index": index,
        "key": key,
        "source": source,
        "configured": bool(key),
        "cooling": remaining > 0,
        "cooldown_remaining": remaining,
    }


def get_all_key_slots() -> list[dict]:
    return [get_key_slot(i) for i in range(1, 5)]


def mark_key_exhausted(index: int, reason: str = "", cooldown: int = COOLDOWN_SECONDS):
    until = time.time() + cooldown
    cache.set(f"automcs_gemini_cooldown_{index}", until, timeout=cooldown)
    log.warning("Gemini API key %d marked exhausted (cooldown %ds). Reason: %s", index, cooldown, reason)


def clear_key_cooldown(index: int):
    cache.delete(f"automcs_gemini_cooldown_{index}")


def is_quota_or_token_error(err: Exception) -> bool:
    code = getattr(err, "code", None)
    status = getattr(err, "status", "")
    msg = str(getattr(err, "message", err)).lower()
    if code in (429, 403) and any(w in msg for w in ("quota", "resource_exhausted", "exhausted", "rate", "token", "limit")):
        return True
    if code == 429:
        return True
    if "resource_exhausted" in str(status).lower() or "resourceexhausted" in str(err).lower():
        return True
    if any(phrase in msg for phrase in ("rate limit", "quota exceeded", "out of quota", "tokens per minute", "resource has been exhausted")):
        return True
    return False


class GeminiProvider(Provider):
    name = "gemini"
    label = "Gemini API (Auto-switch 1-4)"

    def __init__(self, preferred_slot: int | None = None):
        self.preferred_slot = preferred_slot
        if preferred_slot:
            self.name = f"gemini_{preferred_slot}"
            self.label = f"Gemini API {preferred_slot}"

    @property
    def model_id(self):
        return _model()

    def preflight(self):
        slots = get_all_key_slots()
        configured = [s for s in slots if s["configured"]]
        out = []
        if not configured:
            out.append("No Gemini API keys are configured (slots 1-4). Set them in Settings or .env.")
        elif self.preferred_slot:
            pref = next((s for s in slots if s["index"] == self.preferred_slot), None)
            if not pref or not pref["configured"]:
                out.append(f"Gemini API Key {self.preferred_slot} is not configured.")
        if not _model():
            out.append("No Gemini model configured (Settings or GEMINI_MODEL).")
        return out

    def _call_gemini_single(self, key: str, png: bytes):
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(
            model=_model(),
            contents=[types.Part.from_bytes(data=png, mime_type="image/png"), PROMPT],
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0),
        )
        return resp.text or ""

    def extract_page(self, png: bytes, page_number: int) -> PageResult:
        from google.genai import errors

        slots = get_all_key_slots()
        configured = [s for s in slots if s["configured"]]
        if not configured:
            raise ProviderError("No Gemini API keys are configured on the server.")

        # Order candidates: if preferred_slot is given, try it first; else try from slot 1..4
        # Deprioritize slots that are currently cooling down
        if self.preferred_slot:
            ordered_slots = sorted(configured, key=lambda s: (s["index"] != self.preferred_slot, s["cooling"]))
        else:
            ordered_slots = sorted(configured, key=lambda s: (s["cooling"], s["index"]))

        last_error = None
        used_slot = None
        raw_text = ""

        for s in ordered_slots:
            slot_idx = s["index"]
            api_key = s["key"]
            try:
                log.info("Attempting extraction page %d using Gemini API Key %d", page_number, slot_idx)
                raw_text = self._call_gemini_single(api_key, png)
                used_slot = slot_idx
                # Clear cooldown on success in case it was flagged
                if s["cooling"]:
                    clear_key_cooldown(slot_idx)
                break
            except errors.APIError as e:
                code = getattr(e, "code", None)
                msg_str = getattr(e, "message", str(e))
                if is_quota_or_token_error(e):
                    mark_key_exhausted(slot_idx, reason=f"API error {code}: {msg_str}")
                    log.warning(
                        "Gemini API Key %d out of tokens/quota (%s). Auto-switching to next available key...",
                        slot_idx,
                        msg_str,
                    )
                    last_error = e
                    continue
                # For non-quota errors (e.g. 500/503/400), don't immediately exhaust the key
                raise ProviderError(f"Gemini error {code}: {msg_str}", retryable=code in (500, 503))
            except Exception as e:
                if is_quota_or_token_error(e):
                    mark_key_exhausted(slot_idx, reason=str(e))
                    log.warning(
                        "Gemini API Key %d quota error (%s). Auto-switching...",
                        slot_idx,
                        str(e),
                    )
                    last_error = e
                    continue
                log.exception("Gemini request unexpected failure on Key %d", slot_idx)
                raise ProviderError(f"Gemini request failed on Key {slot_idx}: {e}", retryable=True)

        if used_slot is None:
            raise ProviderError(
                f"All configured Gemini API keys (tried {len(ordered_slots)}) are out of tokens or rate-limited: {last_error}",
                retryable=True,
            )

        model_label = f"{_model()} (Key {used_slot})"
        try:
            cols, rows = validate_table(extract_json(raw_text))
        except SchemaError as e:
            return PageResult(page_number, [], [], raw_text, model_label, warnings=[f"invalid_json: {e}"])
        return PageResult(page_number, cols, rows, raw_text, model_label)


def get_provider(name: str) -> Provider:
    if name in ("gemini", "gemini_auto"):
        return GeminiProvider()
    if name in ("gemini_1", "gemini_2", "gemini_3", "gemini_4"):
        slot = int(name.split("_")[1])
        return GeminiProvider(preferred_slot=slot)
    if name == "deepseek":
        # DeepSeek is retired; fallback to Gemini with notice
        log.warning("Provider 'deepseek' was requested but has been removed. Falling back to Gemini.")
        return GeminiProvider()
    raise ProviderError(f"Unknown provider '{name}'.")
