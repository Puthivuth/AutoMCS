import json, re
from django.db import transaction
from .decimals import normalize


class SchemaError(ValueError):
    pass


def extract_json(text: str) -> dict:
    """Pull the first balanced JSON object out of model text (strips <think> blocks and code fences)."""
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S)
    text = re.sub(r"```(?:json)?", "", text)
    start = text.find("{")
    if start < 0:
        raise SchemaError("No JSON object found in model output.")
    depth = 0; in_str = False; esc = False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            esc = (c == "\\") and not esc
            if c == '"' and not esc: in_str = False
            if c != "\\": esc = False
        elif c == '"': in_str = True
        elif c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try: return json.loads(text[start:i + 1])
                except json.JSONDecodeError as e: raise SchemaError(f"Invalid JSON: {e}")
    raise SchemaError("Unterminated JSON object.")


def validate_table(obj: dict):
    cols = obj.get("columns"); rows = obj.get("rows")
    if not isinstance(cols, list) or not cols or not all(isinstance(c, str) for c in cols):
        raise SchemaError("'columns' must be a non-empty list of strings.")
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise SchemaError("'rows' must be a list of objects.")
    code = next((c for c in cols if c.lower() == "code"), None)
    cols = [c for c in cols if c.lower() != "code"] + [code or "code"]
    for ri, row in enumerate(rows):
        row.setdefault("code", None)
        c_val = row.get("code")
        if c_val is not None:
            c_str = str(c_val).strip()
            if ri >= 7:
                row["code"] = None
            elif ri == 3 and ("គ្មាន" in c_str or c_str.lower() in ("null", "none", "khmean", "")):
                row["code"] = None
            elif c_str.lower() in ("null", "none", ""):
                row["code"] = None
            elif ri == 4:
                m_pair = re.search(r"(\d+)\s*(?:&|/|,|\s|\+|and)\s*(\d+)", c_str)
                if m_pair:
                    row["code"] = f"{m_pair.group(1)} & {m_pair.group(2)}"
                else:
                    row["code"] = c_str
            else:
                row["code"] = c_str
        elif ri >= 7:
            row["code"] = None
    return cols, rows


@transaction.atomic
def save_prediction(document, page, job_item, provider, model_id, columns, rows, raw_output, warnings, bboxes=None, confidences=None):
    """Store the immutable prediction, then update working cells WITHOUT touching approved labels."""
    from ..models import Cell, CellEvent, Prediction, PredictionCell
    pred = Prediction.objects.create(document=document, job_item=job_item, page_number=page, provider=provider,
                                     model_id=model_id, columns=columns, raw_output=raw_output, warnings=warnings)
    n = uncertain = 0; pcs = []
    for ri, row in enumerate(rows):
        for ci, col in enumerate(columns):
            raw = row.get(col)
            raw = None if raw is None else str(raw)
            conf = (confidences or {}).get((ri, ci))
            if col.lower() == "code":
                if raw is None or raw.strip().lower() in ("", "null", "none", "គ្មាន"):
                    val = None
                    fl = ""
                    is_present = False
                else:
                    val = raw.strip()
                    fl = ""
                    is_present = True
                pcs.append(PredictionCell(prediction=pred, row_index=ri, col_index=ci, raw_text=raw, value=val, flags=fl, confidence=conf))
                cell, created = Cell.objects.get_or_create(document=document, page_number=page, row_index=ri, col_index=ci,
                    defaults=dict(column_name=col, raw_text=raw, predicted_value=val, flags=fl, confidence=conf,
                                  bbox=(bboxes or {}).get((ri, ci)), latest_prediction=pred))
                if created:
                    CellEvent.objects.create(cell=cell, action="predicted", source="ai", new_value=val)
                elif cell.status != "approved":
                    cell.column_name, cell.raw_text, cell.predicted_value = col, raw, val
                    cell.flags, cell.confidence, cell.latest_prediction = fl, conf, pred
                    if (bboxes or {}).get((ri, ci)): cell.bbox = bboxes[(ri, ci)]
                    cell.save()
                    CellEvent.objects.create(cell=cell, action="predicted", source="ai", new_value=val, note="re-extraction")
                n += is_present
                continue

            nz = normalize(raw)
            flags = []
            if nz.state == "invalid": flags.append("invalid_decimal")
            if nz.rounded: flags.append("rounded")
            if conf is not None and conf < 0.8: flags.append("low_confidence")
            fl = ",".join(flags); uncertain += bool(flags); n += nz.state != "blank"
            pcs.append(PredictionCell(prediction=pred, row_index=ri, col_index=ci, raw_text=raw, value=nz.value, flags=fl, confidence=conf))
            cell, created = Cell.objects.get_or_create(document=document, page_number=page, row_index=ri, col_index=ci,
                defaults=dict(column_name=col, raw_text=raw, predicted_value=nz.value, flags=fl, confidence=conf,
                              bbox=(bboxes or {}).get((ri, ci)), latest_prediction=pred))
            if created:
                CellEvent.objects.create(cell=cell, action="predicted", source="ai", new_value=nz.value)
            elif cell.status != "approved":      # approved ground truth is never overwritten
                cell.column_name, cell.raw_text, cell.predicted_value = col, raw, nz.value
                cell.flags, cell.confidence, cell.latest_prediction = fl, conf, pred
                if (bboxes or {}).get((ri, ci)): cell.bbox = bboxes[(ri, ci)]
                cell.save()
                CellEvent.objects.create(cell=cell, action="predicted", source="ai", new_value=nz.value, note="re-extraction")
    PredictionCell.objects.bulk_create(pcs)
    return pred, n, uncertain
