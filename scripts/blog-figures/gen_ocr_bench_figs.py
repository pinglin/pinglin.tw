#!/usr/bin/env python3
"""Figures for the beyond-ocr-scores post.

Reads the evaluator's own result JSONs out of ~/.shubo-bench — nothing is retyped, because the
one number in this study that WAS retyped by hand turned out to be two different arms pasted into
one row. Arms whose held-out run has not landed yet are simply absent from the charts; re-run this
after the remaining evals finish and the figures fill in.

The typeset SVG hero is generated separately by gen_ocr_hero.mjs.
Chart palettes are the same CVD-validated pairs the apple-silicon post uses.
Outputs into public/blog/beyond-ocr-scores/.
"""
import json
import os
import statistics

B = os.path.expanduser("~/.shubo-bench")
R = f"{B}/odb-eval/result"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../public/blog/beyond-ocr-scores")
# The Qwen 3.6 row: the 32k re-render (qwenfull32) since 2026-09-10; QWEN_ARM=qwenfull restores the 8k render.
QWEN_ARM = os.environ.get("QWEN_ARM", "qwenfull32")
os.makedirs(OUT, exist_ok=True)

THEMES = {
    "dark": dict(BG="#1a1a2e", INK="#ffffff", INK2="#c9c9d4", MUTED="#8f8f9c",
                 GRID="#3a3a4e", AXIS="#55556a",
                 C1="#3987e5", C2="#199e70", C3="#d95926", C4="#a06be0", C5="#e0b32a", C6="#e0609a", C7="#8fa3b8", C8="#33bfb8", C9="#c98a3a", HALO="#1a1a2e"),
    "light": dict(BG="#fcfcfb", INK="#0b0b0b", INK2="#52514e", MUTED="#898781",
                  GRID="#e1e0d9", AXIS="#c3c2b7",
                  C1="#2a78d6", C2="#1baf7a", C3="#eb6834", C4="#8f5bd0", C5="#c99a06", C6="#d1417f", C7="#6b7d8f", C8="#0f8f8a", C9="#a8641c", HALO="#fcfcfb"),
}

# label -> (result prefix, palette slot, group). Order = display order: the document readers first,
# then the three controls that were never built for document parsing, set apart by a rule. The
# composite is the fixed pipeline (v3); the v1 and v2 renders are history and are never charted.
#
# Each specialist runs its MAKER'S pipeline since 2026-09-13 — see the note in
# gen_ocr_bench_tables.py. The labels lose their qualifiers with the artifact rows they described:
# "dots.mocr alone" was alone-behind-our-merge, "GLM-OCR (recognition only)" was our missing layout
# stage. Both now name the system its authors ship.
ARMS = [
    ("Composite",                       "compositev6full", "C1", "readers"),
    ("MinerU2.5-Pro alone",             "mineru0617",    "C1", "readers"),
    ("dots.mocr",                       "mocrnative",    "C4", "readers"),
    ("GLM-OCR",                         "glmsdk",        "C4", "readers"),
    ("PaddleOCR-VL-1.6",                "paddlevl",      "C4", "readers"),
    ("Unlimited-OCR",                   "unlimnative",   "C4", "readers"),
    ("RapidOCR",                        "rapidpipe",     "C4", "readers"),
    ("LiteParse",                       "liteparseocr",  "C4", "readers"),
    ("Apple Vision (OS OCR, tuned)",    "applefresh",    "C3", "controls"),
    ("Qwen 3.6 (VLM)",                  QWEN_ARM,        "C3", "controls"),
    ("Claude Fable 5.1 (VLM)",          "fablefull",     "C3", "controls"),
    ("GPT-6 Astra (VLM)",               "astrafull",     "C3", "controls"),
]
GROUP_GAP = 34   # extra vertical space between the readers and the controls


def headline(prefix):
    p = f"{R}/{prefix}_quick_match_metric_result.json"
    if not os.path.exists(p):
        return None
    m = json.load(open(p))
    return dict(
        text=m["text_block"]["all"]["Edit_dist"]["ALL_page_avg"],
        teds=m["table"]["all"]["TEDS"]["all"] * 100,
        ro=m["reading_order"]["all"]["Edit_dist"]["ALL_page_avg"],
        formula=m["display_formula"]["all"]["Edit_dist"]["ALL_page_avg"],
    )


def by_layout(prefix):
    p = f"{R}/{prefix}_quick_match_text_block_per_page_edit.json"
    if not os.path.exists(p):
        return None
    per = json.load(open(p))
    gold = {}
    for g in json.load(open(f"{B}/gold_fresh.json")):
        stem = os.path.splitext(os.path.basename(g["page_info"].get("image_path", "")))[0]
        gold[stem] = g["page_info"].get("page_attribute", {}).get("layout", "unknown")
    buckets = {}
    for page, v in per.items():
        lay = gold.get(os.path.splitext(page)[0])
        if lay:
            buckets.setdefault(lay, []).append(v)
    return {k: statistics.mean(v) for k, v in buckets.items()}


def style(P):
    return f"""<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: {P['INK2']}; font-size: 16px; }}
.title {{ font-size: 30px; font-weight: 700; fill: {P['INK']}; }}
.subtitle {{ font-size: 17px; fill: {P['INK2']}; }}
.lab {{ fill: {P['INK']}; font-weight: 600; }}
.tick {{ font-size: 14.5px; fill: {P['MUTED']}; }}
.val {{ font-weight: 600; font-size: 15px; fill: {P['INK']}; }}
.axis {{ stroke: {P['AXIS']}; stroke-width: 1.2; }}
.grid {{ stroke: {P['GRID']}; stroke-width: 1; }}
</style>"""


def table_detail(prefix):
    """Found-only TEDS and missed-table count from the per-table file (a missed table is scored 0)."""
    p = f"{R}/{prefix}_quick_match_table_per_table_TEDS.json"
    if not os.path.exists(p):
        return None
    vals = [v["TEDS"] for v in json.load(open(p)).values()]
    found = [v for v in vals if v > 0]
    return dict(found_only=statistics.mean(found) if found else 0.0, missed=len(vals) - len(found), gold=len(vals))


# The six columns of Table 2, one panel each: key, header, lower-is-better, value format, axis max
# (None = 1.15 x the largest value).
METRICS = [("text", "Text edit ↓", True, "{:.4f}", None),
           ("teds", "Table TEDS ↑", False, "{:.2f}", 100.0),
           ("ro", "Reading order ↓", True, "{:.4f}", None),
           ("formula", "Formula ↓", True, "{:.4f}", None),
           ("found_only", "Found-only TEDS ↑", False, "{:.3f}", 1.0),
           ("missed", "Missed tables (of 473) ↓", True, "{:d}", None)]


def bars_figure(theme, P):
    """Six panels, the six metrics of Table 2, in two rows of three; nine readers per panel."""
    data = []
    for label, prefix, slot, grp in ARMS:
        h, t = headline(prefix), table_detail(prefix)
        if h and t:
            data.append((label, {**h, **t}, P[slot], grp))
    ROW_H, PANEL_W, GAP = 30, 200, 60          # bar pitch; bar span; room for the value label
    LABEL_X, PX = 60, [300, 300 + PANEL_W + GAP + 10, 300 + 2 * (PANEL_W + GAP + 10)]
    first_control = next((i for i, d in enumerate(data) if d[3] == "controls"), None)
    block = len(data) * ROW_H + (GROUP_GAP if first_control is not None else 0)
    TOP0, ROW_GAP = 150, 60
    W, H = 1100, TOP0 + 2 * block + ROW_GAP + 40
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            f'<rect width="100%" height="100%" fill="{P["BG"]}" rx="8"/>', style(P),
            f'<text class="title" x="60" y="42">One page set, nine readers, six metrics</text>',
            f'<text class="subtitle" x="60" y="68">OmniDocBench v1.6, the 1,250 held-out pages: the six columns of Table 2, one panel each.</text>',
            f'<text class="subtitle" x="60" y="92">Arrows give the direction of better. Document readers first; the four controls set apart below the dashed rule.</text>']
    for r, row_metrics in enumerate((METRICS[:3], METRICS[3:])):
        top = TOP0 + r * (block + ROW_GAP)
        for c, (key, header, lower, fmt, vmax) in enumerate(row_metrics):
            x0 = PX[c]
            vals = [h[key] for _, h, _, _ in data]
            scale = vmax if vmax else max(vals) * 1.15 or 1.0
            rows.append(f'<text class="tick" x="{x0}" y="{top-14}">{header}</text>')
            for i, (label, h, color, grp) in enumerate(data):
                y = top + i * ROW_H + (GROUP_GAP if grp == "controls" else 0)
                if c == 0:
                    if i == first_control:
                        ys = top + i * ROW_H + 10
                        rows.append(f'<text class="tick" x="{LABEL_X}" y="{ys-4}">Controls — not built for document parsing</text>')
                        rows.append(f'<line class="grid" x1="{LABEL_X}" y1="{ys}" x2="{W-60}" y2="{ys}" stroke-dasharray="4 4"/>')
                    rows.append(f'<text class="lab" x="{LABEL_X}" y="{y+15}" font-size="14.5">{label}</text>')
                bw = min(h[key] / scale, 1.0) * PANEL_W
                rows.append(f'<rect x="{x0}" y="{y+2}" width="{bw:.1f}" height="18" rx="3" fill="{color}" opacity="{0.85 if not lower else 1}"/>')
                rows.append(f'<text class="val" x="{x0+bw+6:.1f}" y="{y+15}" font-size="13.5">{fmt.format(h[key])}</text>')
            # the axis stops at the group gap and resumes below it
            if first_control is None:
                rows.append(f'<line class="axis" x1="{x0}" y1="{top-6}" x2="{x0}" y2="{top + len(data)*ROW_H - 8}"/>')
            else:
                rows.append(f'<line class="axis" x1="{x0}" y1="{top-6}" x2="{x0}" y2="{top + first_control*ROW_H - 8}"/>')
                rows.append(f'<line class="axis" x1="{x0}" y1="{top + first_control*ROW_H + GROUP_GAP - 6}" x2="{x0}" '
                            f'y2="{top + len(data)*ROW_H + GROUP_GAP - 8}"/>')
    rows.append("</svg>")
    open(f"{OUT}/headline_bars_{theme}.svg", "w").write("\n".join(rows))


LAYOUTS = ["single_column", "double_column", "three_column", "1andmore_column", "other_layout"]
LAYOUT_LABELS = {"single_column": "single column", "double_column": "double column",
                 "three_column": "three column", "1andmore_column": "mixed columns",
                 "other_layout": "other layout"}

# Same order as ARMS: readers, then the controls. Every series needs its own colour here, and the
# palette holds exactly nine CVD-validated pairs — so this figure charts nine of the twelve readers.
# PaddleOCR-VL-1.6, RapidOCR and LiteParse are the three it leaves out, and they are NOT omitted for being
# inconvenient: both appear in Tables 2/3 and Figures 3/4/6. Inventing two unvalidated colours to
# fit them here (done once on 2026-09-15 and reverted the same day) would trade a real accessibility property for a cosmetic one; revisit by extending
# the validated palette, not by guessing hex values.
#
# The three specialist series are their makers' own pipelines now (see ARMS above). This changes what
# the figure argues for dots.mocr: behind its own one-shot protocol it is no longer the layout-flat
# no-layout-stage series it was as `mocrfull`.
LAYOUT_ARMS = [("Composite", "compositev6full", "C1"),
               ("MinerU2.5-Pro", "mineru0617", "C5"),
               ("dots.mocr", "mocrnative", "C6"),
               ("GLM-OCR", "glmsdk", "C7"),
               ("Unlimited-OCR", "unlimnative", "C4"),
               ("Apple Vision", "applefresh", "C3"),
               ("Qwen 3.6", QWEN_ARM, "C2"),
               ("Claude Fable 5.1", "fablefull", "C9"),
               ("GPT-6 Astra", "astrafull", "C8")]

# Table 3 drawn to scale: one panel per page source, in Table 3's order (MinerU2.5-Pro's best to
# worst), nine readers each. Each panel has its own scale — the point is the ranking within a
# source, and newspaper's 0.60 would flatten every other panel — so the numbers, not the bar
# lengths, are what compare across panels.
SOURCES = [("research_report", "Research report"), ("PPT2PDF", "Slides (PPT2PDF)"), ("magazine", "Magazine"),
           ("academic_literature", "Academic paper"), ("book", "Book"), ("newspaper", "Newspaper"),
           ("exam_paper", "Exam paper"), ("colorful_textbook", "Textbook"), ("note", "Handwritten notes")]


def by_source(prefix):
    p = f"{R}/{prefix}_quick_match_text_block_per_page_edit.json"
    if not os.path.exists(p):
        return None
    per = json.load(open(p))
    gold = {}
    for g in json.load(open(f"{B}/gold_fresh.json")):
        stem = os.path.splitext(os.path.basename(g["page_info"].get("image_path", "")))[0]
        gold[stem] = g["page_info"].get("page_attribute", {}).get("data_source", "unknown")
    buckets = {}
    for page, v in per.items():
        src = gold.get(os.path.splitext(page)[0])
        if src:
            buckets.setdefault(src, []).append(v)
    return {k: (statistics.mean(v), len(v)) for k, v in buckets.items()}


def source_figure(theme, P):
    """Nine panels (3 x 3), one per source, nine readers each; best per source in bold."""
    data = [(label, by_source(prefix), P[slot], grp) for label, prefix, slot, grp in ARMS]
    data = [(l, d, c, g) for l, d, c, g in data if d]
    ROW_H, PANEL_W, GAP = 26, 170, 66
    LABEL_X, PX = 60, [300, 300 + PANEL_W + GAP + 10, 300 + 2 * (PANEL_W + GAP + 10)]
    first_control = next((i for i, d in enumerate(data) if d[3] == "controls"), None)
    block = len(data) * ROW_H + (GROUP_GAP if first_control is not None else 0)
    TOP0, ROW_GAP = 150, 56
    W, H = 1100, TOP0 + 3 * block + 2 * ROW_GAP + 30
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            f'<rect width="100%" height="100%" fill="{P["BG"]}" rx="8"/>', style(P),
            f'<text class="title" x="60" y="42">Every source, every reader</text>',
            f'<text class="subtitle" x="60" y="68">Table 3 drawn to scale: mean text edit distance by page source, held-out 1,250, lower is better.</text>',
            f'<text class="subtitle" x="60" y="92">One panel per source in Table 3\u2019s order; each panel on its own scale, best reader in bold.</text>']
    for r in range(3):
        top = TOP0 + r * (block + ROW_GAP)
        for c in range(3):
            key, name = SOURCES[r * 3 + c]
            x0 = PX[c]
            vals = [d[key][0] for _, d, _, _ in data if key in d]
            if not vals:
                continue
            n_pages = next(d[key][1] for _, d, _, _ in data if key in d)
            scale = max(vals) * 1.18
            best = min(vals)
            rows.append(f'<text class="tick" x="{x0}" y="{top-14}">{name} ({n_pages}) \u2193</text>')
            for i, (label, d, color, grp) in enumerate(data):
                y = top + i * ROW_H + (GROUP_GAP if grp == "controls" else 0)
                if c == 0:
                    if i == first_control:
                        ys = top + i * ROW_H + 10
                        rows.append(f'<text class="tick" x="{LABEL_X}" y="{ys-4}">Controls</text>')
                        rows.append(f'<line class="grid" x1="{LABEL_X}" y1="{ys}" x2="{W-60}" y2="{ys}" stroke-dasharray="4 4"/>')
                    rows.append(f'<text class="lab" x="{LABEL_X}" y="{y+14}" font-size="13.5">{label}</text>')
                v = d.get(key, (None, 0))[0]
                if v is None:
                    continue
                bw = min(v / scale, 1.0) * PANEL_W
                rows.append(f'<rect x="{x0}" y="{y+2}" width="{bw:.1f}" height="16" rx="3" fill="{color}"/>')
                mark = ' font-weight="800"' if abs(v - best) < 5e-5 else f' font-weight="500" fill="{P["INK2"]}"'
                rows.append(f'<text class="val" x="{x0+bw+6:.1f}" y="{y+14}" font-size="12.5"{mark}>{v:.4f}</text>')
            if first_control is None:
                rows.append(f'<line class="axis" x1="{x0}" y1="{top-6}" x2="{x0}" y2="{top + len(data)*ROW_H - 8}"/>')
            else:
                rows.append(f'<line class="axis" x1="{x0}" y1="{top-6}" x2="{x0}" y2="{top + first_control*ROW_H - 8}"/>')
                rows.append(f'<line class="axis" x1="{x0}" y1="{top + first_control*ROW_H + GROUP_GAP - 6}" x2="{x0}" '
                            f'y2="{top + len(data)*ROW_H + GROUP_GAP - 8}"/>')
    rows.append("</svg>")
    open(f"{OUT}/source_bars_{theme}.svg", "w").write("\n".join(rows))



def layout_figure(theme, P):
    series = [(label, by_layout(prefix), P[slot]) for label, prefix, slot in LAYOUT_ARMS]
    series = [s for s in series if s[1] is not None]  # an arm not yet scored is simply absent
    series = [(l, d, c) for l, d, c in series if d]
    # The exact values live in a data strip under the axis (one row per reader, aligned under each
    # layout group) instead of on the bars: five series per group left no room for 25 labels, and
    # the strip doubles as the legend.
    STRIP_ROW = 24
    W, H = 1100, 470 + 24 + STRIP_ROW * len(series)
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            f'<rect width="100%" height="100%" fill="{P["BG"]}" rx="8"/>', style(P),
            '<text class="title" x="60" y="42">Three readers fall apart on layout; six stay flat</text>',
            f'<text class="subtitle" x="60" y="68">Apple Vision and Unlimited-OCR degrade with column count; '
            f'GLM-OCR collapses on dense mixed layouts.</text>',
            f'<text class="subtitle" x="60" y="92">Mean text edit distance by page layout, held-out 1,250. '
            f'Lower is better.</text>']
    top, bot, lx = 130, 400, 170
    span = 900
    vmax = max(v for _, d, _ in series for v in d.values()) * 1.15
    for g in (0.1, 0.2, 0.3):
        if g < vmax:
            y = bot - g / vmax * (bot - top)
            rows.append(f'<line class="grid" x1="{lx}" y1="{y:.0f}" x2="{lx+span}" y2="{y:.0f}"/>')
            rows.append(f'<text class="tick" x="{lx-38}" y="{y+5:.0f}">{g:.1f}</text>')
    gw = span / len(LAYOUTS)
    bw = min(46, (gw - 40) / len(series))
    for j, lay in enumerate(LAYOUTS):
        gx = lx + j * gw
        for k, (label, d, color) in enumerate(series):
            v = d.get(lay)
            if v is None:
                continue
            h = v / vmax * (bot - top)
            bx = gx + (gw - bw * len(series)) / 2 + k * bw
            rows.append(f'<rect x="{bx:.1f}" y="{bot-h:.1f}" width="{bw-4:.1f}" height="{h:.1f}" rx="4" fill="{color}"/>')
        rows.append(f'<text class="tick" x="{gx+gw/2:.1f}" y="{bot+26}" text-anchor="middle">{LAYOUT_LABELS[lay]}</text>')
    rows.append(f'<line class="axis" x1="{lx}" y1="{bot}" x2="{lx+span}" y2="{bot}"/>')
    # data strip: swatch + reader on the left, one value under each group
    y0 = bot + 60
    rows.append(f'<line class="grid" x1="60" y1="{y0-18}" x2="{lx+span}" y2="{y0-18}"/>')
    # the best (lowest) reader in each layout is set in bold ink, like the tables' best-per-column;
    # judged at the three decimals shown, so two readers that print the same value are both bold
    best = {lay: min(round(d[lay], 3) for _, d, _ in series if lay in d) for lay in LAYOUTS}
    for k, (label, d, color) in enumerate(series):
        y = y0 + k * STRIP_ROW
        rows.append(f'<rect x="60" y="{y-11}" width="12" height="12" rx="3" fill="{color}"/>')
        rows.append(f'<text class="tick" x="80" y="{y}">{label}</text>')
        for j, lay in enumerate(LAYOUTS):
            v = d.get(lay)
            if v is not None:
                cls = "val" if round(v, 3) == best[lay] else "tick"
                rows.append(f'<text class="{cls}" x="{lx + j*gw + gw/2:.1f}" y="{y}" text-anchor="middle">{v:.3f}</text>')
    rows.append("</svg>")
    open(f"{OUT}/layout_collapse_{theme}.svg", "w").write("\n".join(rows))



# ── Empty pages per reader ───────────────────────────────────────────────────────────────────
# A page a reader left empty is a total loss on every metric it carries. Counted from the arm's
# prediction directory (an empty or missing file), split by whether the evaluator scores that
# page on text at all — the union of pages carrying a text score across the arms, i.e. pages
# with ground-truth text blocks. The rest are figure-only pages where an empty read costs nothing.
import yaml as _yaml

def pred_dir(prefix):
    cfg = _yaml.safe_load(open(f"{B}/odb-eval/configs/{prefix}.yaml"))
    return cfg["end2end_eval"]["dataset"]["prediction"]["data_path"]

def text_pages():
    pages = set()
    for label, prefix, _, _ in ARMS:
        p = f"{R}/{prefix}_quick_match_text_block_per_page_edit.json"
        if os.path.exists(p):
            pages |= {os.path.splitext(k)[0] for k in json.load(open(p))}
    return pages

def empties(prefix, tpages):
    d = pred_dir(prefix)
    stems = [os.path.splitext(os.path.basename(g["page_info"]["image_path"]))[0] for g in json.load(open(f"{B}/gold_fresh.json"))]
    empty = []
    for s in stems:
        p = os.path.join(d, s + ".md")
        if not os.path.exists(p) or len(open(p, encoding="utf-8", errors="ignore").read().strip()) == 0:
            empty.append(s)
    return len(empty), sum(1 for s in empty if s in tpages)

def empties_chart(theme):
    P = THEMES[theme]
    tpages = text_pages()
    rows_data = [(label, *empties(prefix, tpages), grp) for label, prefix, _, grp in ARMS if headline(prefix)]
    W = 1100; top = 136; rh = 44; first_control = next((i for i, d in enumerate(rows_data) if d[3] == "controls"), None)
    H = top + rh * len(rows_data) + (GROUP_GAP if first_control is not None else 0) + 60
    vmax = max(d[1] for d in rows_data) or 1; x0, span = 330, 640
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
            f'<rect width="100%" height="100%" fill="{P["BG"]}" rx="8"/>', style(P),
            '<text class="title" x="60" y="42">Pages a reader left empty</text>',
            '<text class="subtitle" x="60" y="68">Of the 1,250 held-out pages. The orange part had ground-truth text and counts as a total loss;</text>',
            '<text class="subtitle" x="60" y="92">the grey part is figure-only pages, where an empty read costs nothing.</text>']
    for i, (label, total, with_text, grp) in enumerate(rows_data):
        y = top + i * rh + (GROUP_GAP if grp == "controls" else 0)
        if i == first_control:
            rows.append(f'<line class="grid" x1="{x0-270}" y1="{y-GROUP_GAP//2-8}" x2="{x0+span}" y2="{y-GROUP_GAP//2-8}" stroke-dasharray="4 4"/>')
        rows.append(f'<text x="{x0-12}" y="{y+18}" text-anchor="end">{label}</text>')
        w_all = total / vmax * span; w_text = with_text / vmax * span
        rows.append(f'<rect x="{x0}" y="{y}" width="{max(w_all,1):.1f}" height="26" fill="{P["C7"]}" opacity="0.45"/>')
        rows.append(f'<rect x="{x0}" y="{y}" width="{max(w_text,0):.1f}" height="26" fill="{P["C3"]}"/>')
        rows.append(f'<text x="{x0 + w_all + 10:.1f}" y="{y+18}" class="tick">{total}' + (f' ({with_text} with text)' if total else '') + '</text>')
    rows.append("</svg>")
    open(f"{OUT}/empty_pages_{theme}.svg", "w").write("\n".join(rows))
    return rows_data

if __name__ == "__main__":
    for theme, P in THEMES.items():
        bars_figure(theme, P)
        source_figure(theme, P)
        layout_figure(theme, P)
        empty_rows = empties_chart(theme)
    print("empties (total, with gold text):", [(l, t, w) for l, t, w, _ in empty_rows])
    print("wrote:", sorted(os.listdir(OUT)))
