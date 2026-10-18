from dataclasses import dataclass, field

PROMPT = (
    "You read a table of decimal numbers from the document and the code boxes on its right. "
    "Return ONLY one valid JSON object, no commentary:\n"
    '{"columns": ["I","II","III","IV","V","code"], "rows": [{"No": 1, "I": "01", "II": "01", "III": "01", "IV": "01", "V": "00", "code": "16073"}, ...]}\n'
    "Rules:\n"
    "1. Column names: Take Roman-numeral columns exactly from the table header (e.g. I, II, III, IV, V). Always place a final column named 'code' after the Roman columns.\n"
    "2. Table values: One object per table row in order (No: 1 through 25). Copy each number as written (e.g. '01', '00', '13.45'). Use null for an empty cell. Never guess or invent numbers.\n"
    "3. 'code' column rules (read from the handwritten boxes on the right side of the document):\n"
    "   - Row 1: Grader code from top box 1 (e.g. '16073').\n"
    "   - Row 2: Group leader code from top box 2 (e.g. '16192').\n"
    "   - Row 3: Distributor code from top box 3 (e.g. '32476').\n"
    "   - Row 4: Inspection count from top box 4. If empty or equal to 'គ្មាន' (none), code MUST be null.\n"
    "   - Row 5: Computer ID and Sheet ID from bottom computer box 1, combined as 'ID1 & ID2' (e.g. '08 & 130').\n"
    "   - Row 6: Data entry code from bottom computer box 2 (e.g. '6560').\n"
    "   - Row 7: Verification code from bottom computer box 3 (e.g. '6333').\n"
    "   - Row 8 through 25 (and any other rows): code MUST be null."
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
