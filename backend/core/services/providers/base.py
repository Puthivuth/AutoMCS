from dataclasses import dataclass, field

PROMPT = (
    "You read a table of decimal numbers. Return ONLY one JSON object, no commentary:\n"
    '{"columns": ["I","II",...], "rows": [{"No": 1, "I": "13.45", "II": null}, ...]}\n'
    "Rules: take column names from the header; one object per table row in order; copy each number exactly as "
    "written, as a string; use null for an empty cell; never guess, round, or invent values."
)


class ProviderError(Exception):
    def __init__(self, msg, retryable=False):
        super().__init__(msg); self.retryable = retryable


@dataclass
class PageResult:
    page_number: int
    columns: list
    rows: list
    raw_output: str
    model_id: str
    warnings: list = field(default_factory=list)
    bboxes: dict = field(default_factory=dict)
    confidences: dict = field(default_factory=dict)


class Provider:
    name = ""; label = ""; model_id = ""
    def preflight(self) -> list:          # configuration problems, empty list = OK
        return []
    def prepare(self):                    # called once per job (e.g. load the local model)
        pass
    def extract_page(self, png: bytes, page_number: int) -> PageResult:
        raise NotImplementedError
