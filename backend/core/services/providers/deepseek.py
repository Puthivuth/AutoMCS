"""Local DeepSeek-R1-Distill-Qwen-1.5B is TEXT-ONLY. It never sees the image: OCR + layout produce
text, and the model only structures/cleans it into the shared JSON schema."""
from .. import model_manager
from ..tables import SchemaError, extract_json, validate_table
from . import ocr, table_layout
from .base import PROMPT, PageResult, Provider, ProviderError


class DeepSeekProvider(Provider):
    name = "deepseek"; label = "Local DeepSeek 1.5B"

    @property
    def model_id(self):
        return model_manager.model_label()

    def preflight(self):
        out = model_manager.config_problems()
        if not ocr.get_engine().available(): out.append("OCR engine (Tesseract) is not installed on the worker.")
        return out

    def prepare(self):
        model_manager.ensure_ready()   # download (if enabled) -> validate -> load -> readiness check

    def extract_page(self, png, page_number):
        words = ocr.get_engine().read(png)
        grid, boxes = table_layout.to_grid(words)
        if not grid: raise ProviderError("OCR found no text on this page.")
        tsv = "\n".join(f"r{ri}\t" + "\t".join(c or "" for c in row) for ri, row in enumerate(grid))
        out = model_manager.generate(f"{PROMPT}\n\nOCR text, tab-separated cells (first column is the OCR row id):\n{tsv}")
        try:
            cols, rows = validate_table(extract_json(out))
        except SchemaError as e:
            return PageResult(page_number, [], [], out, self.model_id, warnings=[f"invalid_json: {e}"])
        warn, bb = [], {}
        if len(rows) == len(grid) - 1 or len(rows) == len(grid):    # same shape as OCR grid -> keep source positions
            off = len(grid) - len(rows)
            for (ri, ci), b in boxes.items():
                if ri - off >= 0 and ci - 1 >= 0: bb[(ri - off, ci - 1)] = b
        return PageResult(page_number, cols, rows, out, self.model_id, warn, bb)


def get_provider(name):
    from .gemini import GeminiProvider
    try: return {"gemini": GeminiProvider, "deepseek": DeepSeekProvider}[name]()
    except KeyError: raise ProviderError(f"Unknown provider '{name}'.")
