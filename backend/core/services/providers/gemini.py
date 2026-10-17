from django.conf import settings
from ..tables import SchemaError, extract_json, validate_table
from .base import PROMPT, PageResult, Provider, ProviderError


def _model():
    from ...models import SiteSettings
    return SiteSettings.get().gemini_model or settings.AUTOMCS["GEMINI_MODEL"]


class GeminiProvider(Provider):
    name = "gemini"; label = "Gemini API"

    @property
    def model_id(self):
        return _model()

    def preflight(self):
        out = []
        if not settings.AUTOMCS["GEMINI_API_KEY"]: out.append("GEMINI_API_KEY is not set on the server.")
        if not _model(): out.append("No Gemini model configured (Settings or GEMINI_MODEL).")
        return out

    def extract_page(self, png, page_number):
        from google import genai
        from google.genai import errors, types
        try:
            client = genai.Client(api_key=settings.AUTOMCS["GEMINI_API_KEY"])
            resp = client.models.generate_content(
                model=_model(),
                contents=[types.Part.from_bytes(data=png, mime_type="image/png"), PROMPT],
                config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0))
            text = resp.text or ""
        except errors.APIError as e:
            code = getattr(e, "code", None)
            raise ProviderError(f"Gemini error {code}: {getattr(e, 'message', e)}", retryable=code in (429, 500, 503))
        except Exception as e:
            raise ProviderError(f"Gemini request failed: {e}", retryable=True)
        try:
            cols, rows = validate_table(extract_json(text))
        except SchemaError as e:
            return PageResult(page_number, [], [], text, _model(), warnings=[f"invalid_json: {e}"])
        return PageResult(page_number, cols, rows, text, _model())
