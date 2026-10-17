"""Words (with boxes) -> grid of cells. Heuristic; independent of OCR and of the model."""
from statistics import median


def _cluster(values, gap):
    groups = []
    for v in sorted(values):
        if groups and v - groups[-1][-1] <= gap: groups[-1].append(v)
        else: groups.append([v])
    return [sum(g) / len(g) for g in groups]


def to_grid(words):
    if not words: return [], {}
    h = median(w.y1 - w.y0 for w in words); wd = median(w.x1 - w.x0 for w in words)
    rows_c = _cluster([(w.y0 + w.y1) / 2 for w in words], h * 0.6)
    cols_c = _cluster([(w.x0 + w.x1) / 2 for w in words], max(wd * 1.2, h))
    grid = [[[] for _ in cols_c] for _ in rows_c]; boxes = {}
    for w in sorted(words, key=lambda w: w.x0):
        ri = min(range(len(rows_c)), key=lambda i: abs(rows_c[i] - (w.y0 + w.y1) / 2))
        ci = min(range(len(cols_c)), key=lambda i: abs(cols_c[i] - (w.x0 + w.x1) / 2))
        grid[ri][ci].append(w.text)
        b = boxes.get((ri, ci)); boxes[(ri, ci)] = [w.x0, w.y0, w.x1, w.y1] if not b else [min(b[0], w.x0), min(b[1], w.y0), max(b[2], w.x1), max(b[3], w.y1)]
    return [[" ".join(c) or None for c in r] for r in grid], boxes
