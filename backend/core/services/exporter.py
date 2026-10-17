import csv, io, json, zipfile
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from ..models import CellEvent, Document
from .files import safe_name


def _tables(doc, cells):
    pages = {}
    for c in cells: pages.setdefault(c.page_number, []).append(c)
    out = []
    for pn, cs in sorted(pages.items()):
        cols = [c.column_name for c in sorted((c for c in cs if c.row_index == 0), key=lambda c: c.col_index)]
        rows = {}
        for c in cs: rows.setdefault(c.row_index, {"No": c.row_index + 1})[c.column_name] = c.verified_value if c.status == "approved" else None
        out.append({"page_number": pn, "columns": cols, "rows": [rows[k] for k in sorted(rows)]})
    return out


def build_zip(job):
    o = job.options; project = job.project
    docs = Document.objects.filter(project=project)
    if o.get("document_ids"): docs = docs.filter(id__in=o["document_ids"])
    dest = Path(settings.EXPORTS_DIR) / str(project.id); dest.mkdir(parents=True, exist_ok=True)
    path = dest / f"export_{job.id}.zip"
    used, included, skipped, jsonl = set(), [], [], []
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for d in docs:
            cells = list(d.cells.all())
            approved = [c for c in cells if c.status == "approved"]
            if not approved or (len(approved) < len(cells) and not o.get("allow_partial")):
                skipped.append({"document": d.original_name, "reason": "no approved cells" if not approved else "not fully approved"}); continue
            stem = safe_name(d.original_name.rsplit(".", 1)[0]); n = 1; base = stem
            while stem in used: n += 1; stem = f"{base}_{n}"
            used.add(stem); ext = d.file.name.rsplit(".", 1)[-1]
            z.write(d.file.path, f"image_pdf/{stem}.{ext}")
            tabs = _tables(d, cells)
            rec = {"document_id": d.id, "filename": f"{stem}.{ext}", "pages": tabs}
            if len(approved) < len(cells): rec["unapproved_cells"] = [[c.page_number, c.row_index, c.column_name] for c in cells if c.status != "approved"]
            jsonl.append(rec)
            z.writestr(f"groundtruth/{stem}.json", json.dumps(rec, indent=2, ensure_ascii=False))
            buf = io.StringIO(); w = csv.writer(buf)
            for t in tabs:
                w.writerow(["page", "No"] + t["columns"])
                for r in t["rows"]: w.writerow([t["page_number"], r["No"]] + ["" if r.get(c) is None else r[c] for c in t["columns"]])
            z.writestr(f"groundtruth/{stem}.csv", buf.getvalue())
            if o.get("include_history"):
                ev = CellEvent.objects.filter(cell__document=d).select_related("cell")
                z.writestr(f"history/{stem}.json", json.dumps([dict(page=e.cell.page_number, row=e.cell.row_index + 1, column=e.cell.column_name,
                    action=e.action, source=e.source, old=e.old_value, new=e.new_value, note=e.note, at=e.created_at.isoformat()) for e in ev], indent=1))
            included.append(d.original_name)
        if o.get("jsonl"): z.writestr("groundtruth.jsonl", "\n".join(json.dumps(r, ensure_ascii=False) for r in jsonl))
        z.writestr("manifest.json", json.dumps(dict(project=project.name, created=timezone.now().isoformat(), rounding=settings.AUTOMCS["ROUNDING"],
            value_format="two-decimal strings; null = blank cell", included=included, skipped=skipped), indent=1))
    return str(path), {"included": len(included), "skipped": skipped}
