from dataclasses import dataclass, field

PROMPT = (
    "You read a table of decimal numbers and the small code boxes to its right. Return ONLY one JSON object, no commentary:\n"
    '{"columns": ["I","II","III","code"], "rows": [{"No": 1, "I": "13.45", "II": null, "code": null}, ...]}\n'
    "Rules: take the Roman-numeral column names exactly from the image header; there may be I through IV, V, VI, VII, or VIII, and never assume a fixed final Roman column. "
    "Always put a final column named code after the detected table columns. One object per table row in order; copy each number exactly as written, as a string; use null for an empty cell; never guess, round, or invent values. "
    "Read code values from the boxes on the right and place each value on its matching row; rows without a box must have code null."
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
