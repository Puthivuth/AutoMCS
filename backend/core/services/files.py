import hashlib, io, re
from pathlib import Path
from django.conf import settings

SIGS = [(b"\x89PNG\r\n\x1a\n", "image", "image/png"), (b"\xff\xd8\xff", "image", "image/jpeg"), (b"%PDF-", "pdf", "application/pdf")]


class UploadRejected(Exception):
    pass


def sniff(head: bytes):
    for sig, kind, mime in SIGS:
        if head.startswith(sig):
            return kind, mime
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image", "image/webp"
    return None, None


def inspect_upload(f):
    """Validate real content (not the extension). Returns (kind, mime, page_count, sha256)."""
    if f.size > settings.AUTOMCS["MAX_UPLOAD_BYTES"]:
        raise UploadRejected("File exceeds the size limit.")
    kind, mime = sniff(f.read(16)); f.seek(0)
    if not kind:
        raise UploadRejected("Unsupported or corrupt file type.")
    h = hashlib.sha256()
    for chunk in f.chunks():
        h.update(chunk)
    f.seek(0)
    try:
        if kind == "image":
            from PIL import Image
            Image.open(f).verify(); pages = 1
        else:
            import pypdfium2 as pdfium
            pages = len(pdfium.PdfDocument(f.read()))
    except Exception:
        raise UploadRejected("File could not be opened; it may be corrupt.")
    finally:
        f.seek(0)
    return kind, mime, pages, h.hexdigest()


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name).strip("._") or "file"


def clean_relpath(p: str) -> str:
    parts = [safe_name(x) for x in Path(p.replace("\\", "/")).parts if x not in ("", ".", "..", "/")]
    return "/".join(parts[:-1])


def render_page_png(document, page_number: int, scale: float = 2.0) -> bytes:
    path = document.file.path
    if document.kind == "image":
        from PIL import Image
        im = Image.open(path).convert("RGB")
    else:
        import pypdfium2 as pdfium
        im = pdfium.PdfDocument(path)[page_number - 1].render(scale=scale).to_pil().convert("RGB")
    buf = io.BytesIO(); im.save(buf, "PNG")
    return buf.getvalue()
