"""OCR is a separate component so it can be swapped independently of the language model."""
from dataclasses import dataclass
from io import BytesIO
from django.conf import settings


@dataclass
class Word:
    text: str; x0: int; y0: int; x1: int; y1: int; conf: float


class TesseractEngine:
    def available(self):
        try:
            import pytesseract; pytesseract.get_tesseract_version(); return True
        except Exception:
            return False

    def read(self, png: bytes):
        import pytesseract
        from PIL import Image
        d = pytesseract.image_to_data(Image.open(BytesIO(png)), config="--psm 6", output_type=pytesseract.Output.DICT)
        return [Word(t, l, tp, l + w, tp + h, float(c)) for t, l, tp, w, h, c in
                zip(d["text"], d["left"], d["top"], d["width"], d["height"], d["conf"]) if t.strip() and float(c) >= 0]


def get_engine():
    return {"tesseract": TesseractEngine}[settings.AUTOMCS["OCR_ENGINE"]]()
