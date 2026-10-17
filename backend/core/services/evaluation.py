from decimal import Decimal
from ..models import Cell, Prediction, PredictionCell

RULES = {"ground_truth": "approved cells only", "compare": "string equality of two-decimal values",
         "blank_vs_blank": "correct", "blank_prediction_vs_value": "missing", "value_vs_blank_truth": "extra",
         "invalid_prediction": "counted invalid and incorrect", "unreviewed_predictions": "never used as truth"}


def evaluate(project, documents, provider="", model_id="", tolerance="0"):
    tol = Decimal(tolerance or 0)
    m = dict(cells=0, exact=0, within_tolerance=0, missing=0, extra=0, invalid=0, uncertain=0, mismatched=0,
             docs_without_prediction=0, by_column={}, by_document={}, abs_err_sum=Decimal(0), abs_err_n=0)
    tables = {}
    for doc in documents:
        q = Prediction.objects.filter(document=doc)
        if provider: q = q.filter(provider=provider)
        if model_id: q = q.filter(model_id=model_id)
        latest = {}                                           # newest prediction per page
        for p in q.order_by("created_at"): latest[p.page_number] = p
        gt = list(Cell.objects.filter(document=doc, status="approved"))
        if not gt: continue
        if not latest: m["docs_without_prediction"] += 1; continue
        pc = {(p.page_number, c.row_index, c.col_index): c for p in latest.values() for c in p.cells.all()}
        for c in gt:
            if c.page_number not in latest: continue
            pr = pc.get((c.page_number, c.row_index, c.col_index))
            pv, flags = (pr.value, pr.flags) if pr else (None, "")
            ok = False; m["cells"] += 1
            if "low_confidence" in flags: m["uncertain"] += 1
            if "invalid_decimal" in flags: m["invalid"] += 1
            elif pv == c.verified_value: ok = True; m["exact"] += 1
            elif pv is None: m["missing"] += 1
            elif c.verified_value is None: m["extra"] += 1
            else:
                err = abs(Decimal(pv) - Decimal(c.verified_value)); m["abs_err_sum"] += err; m["abs_err_n"] += 1
                if err <= tol: m["within_tolerance"] += 1
                else: m["mismatched"] += 1
            if pv is not None and c.verified_value is not None and ok: m["abs_err_n"] += 1
            if not ok:
                m["by_column"][c.column_name] = m["by_column"].get(c.column_name, 0) + 1
                m["by_document"][doc.original_name] = m["by_document"].get(doc.original_name, 0) + 1
            tables.setdefault((doc.id, c.page_number), []).append(ok)
    n = m["cells"]
    docs = {}
    for (d, _), oks in tables.items(): docs.setdefault(d, []).append(all(oks))
    return dict(cells_evaluated=n, exact_cell_accuracy=(m["exact"] / n) if n else None,
                table_accuracy=(sum(all(v) for v in tables.values()) / len(tables)) if tables else None,
                document_accuracy=(sum(all(v) for v in docs.values()) / len(docs)) if docs else None,
                mean_abs_error=float(m["abs_err_sum"] / m["abs_err_n"]) if m["abs_err_n"] else None,
                missing=m["missing"], extra=m["extra"], invalid=m["invalid"], uncertain=m["uncertain"],
                mismatched=m["mismatched"], within_tolerance=m["within_tolerance"], tolerance=str(tol),
                documents_without_prediction=m["docs_without_prediction"], mismatches_by_column=m["by_column"],
                mismatches_by_document=m["by_document"])
