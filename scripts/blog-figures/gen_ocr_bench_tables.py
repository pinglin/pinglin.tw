#!/usr/bin/env python3
"""Regenerate Tables 2, 3 and 4 of beyond-ocr-scores.md from the evaluator's own result files and the speed bench.

Every cell comes from ~/.shubo-bench/report.py (headline, table_detail, by_attribute) — the same
functions that produce the RESULTS doc — so the article can never drift from the record. Per
column (both tables; Table 3 is transposed, readers as rows) the best value is black bold, the second-best blue bold
and the third-best green bold; ties for first are all black, and the runner-up is the next distinct value. Run after any
arm is re-scored:  python3 scripts/blog-figures/gen_ocr_bench_tables.py [--check]
"""
import os
import re
import sys

B = os.path.expanduser("~/.shubo-bench")
sys.path.insert(0, B)
os.chdir(B)
import report  # noqa: E402  (~/.shubo-bench/report.py)

ARTICLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../src/content/blog/beyond-ocr-scores.md")
BLUE = '<b class="text-blue-600 dark:text-blue-400">{}</b>'
GREEN = '<b class="text-green-600 dark:text-green-400">{}</b>'

# display label, result prefix, Table 2 label (with the control tag), Table 3 column label
#
# Every OCR-specialist row is its MAKER'S OWN pipeline, not ours (2026-09-13). The three rows this
# table carried before measured our harness: `mocrfull` pushed dots.mocr's elements through the
# composite's merge, which drops tables when no MinerU runs beside it (TEDS 0.19 against 81.34
# native); `glmfull` ran GLM-OCR's recognizer with no layout stage (13.92 against 68.15 through its
# own SDK); `unlimitedfull` ran Unlimited-OCR behind OUR layout stage without its n-gram guard.
# Swapping them is the difference between measuring a model and measuring our wiring around it.
ARMS = [
    ("Composite", "compositev6full", "Composite", "Composite"),
    ("MinerU2.5-Pro", "mineru0617", "MinerU2.5-Pro", "MinerU2.5-Pro"),
    ("dots.mocr", "mocrnative", "dots.mocr", "dots.mocr"),
    ("GLM-OCR", "glmsdk", "GLM-OCR", "GLM-OCR"),
    ("PaddleOCR-VL-1.6", "paddlevl", "PaddleOCR-VL-1.6", "PaddleOCR-VL-1.6"),
    ("Unlimited-OCR", "unlimnative", "Unlimited-OCR", "Unlimited-OCR"),
    ("RapidOCR", "rapidpipe", "RapidOCR", "RapidOCR"),
    ("Apple Vision", "applefresh", "Apple Vision (OS OCR)", "Apple Vision (OS OCR)"),
    ("Qwen 3.6", os.environ.get("QWEN_ARM", "qwenfull32"), "Qwen 3.6 (VLM)", "Qwen 3.6 (VLM)"),
    ("Claude Fable 5.1", "fablefull", "Claude Fable 5.1 (VLM)", "Claude Fable 5.1 (VLM)"),
    ("GPT-6 Astra", "astrafull", "GPT-6 Astra (VLM)", "GPT-6 Astra (VLM)"),
]
# Table 3 rows: the nine sources the article shows, in MinerU2.5-Pro's order (best to worst);
# historical_document (3 text pages) is left out, as before.
ARMS = [a for a in ARMS if report.headline(a[1])]  # an arm not yet scored is simply absent
SOURCES = ["research_report", "PPT2PDF", "magazine", "academic_literature", "book",
           "newspaper", "exam_paper", "colorful_textbook", "note"]


def rank_marks(values, lower_is_better):
    """Return per-value marker: 'first' | 'second' | 'third' | None, ties for first all 'first'."""
    distinct = sorted({v for v in values if v is not None}, reverse=not lower_is_better)
    first = distinct[0] if distinct else None
    second = distinct[1] if len(distinct) > 1 else None
    third = distinct[2] if len(distinct) > 2 else None
    return ["first" if v == first else "second" if v == second else "third" if v == third else None
            for v in values]


def mark(text, m):
    return (f"**{text}**" if m == "first" else BLUE.format(text) if m == "second"
            else GREEN.format(text) if m == "third" else text)


def table2():
    gold = report.gold_index("gold_fresh.json")
    rows = []
    for label, prefix, t2label, _ in ARMS:
        h = report.headline(prefix)
        t = report.table_detail(prefix, gold)
        rows.append((t2label, h["text_edit"], h["TEDS"] * 100, h["reading_order"], h["formula_edit"],
                     t["found_only_TEDS"], t["missed"], t["gold_tables"]))
    cols = [  # (index, lower_is_better, formatter)
        (1, True, lambda v: f"{v:.4f}"), (2, False, lambda v: f"{v:.2f}"), (3, True, lambda v: f"{v:.4f}"),
        (4, True, lambda v: f"{v:.4f}"), (5, False, lambda v: f"{v:.3f}"), (6, True, lambda v: f"{v}"),
    ]
    marks = {i: rank_marks([r[i] for r in rows], lower) for i, lower, _ in cols}
    out = ["| Reader | Text edit ↓ | TEDS ↑ | Order ↓ | Formula ↓ | Found-only TEDS ↑ | Missed ↓ |",
           "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for k, r in enumerate(rows):
        cells = [f'<span style="white-space: nowrap">{r[0]}</span>']
        for i, _, fmt in cols:
            text = fmt(r[i]) + (f"/{r[7]}" if i == 6 else "")
            if i == 6:
                text = mark(fmt(r[i]), marks[i][k]) + f"/{r[7]}"
                cells.append(text)
            else:
                cells.append(mark(text, marks[i][k]))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def table3():
    """Transposed: one row per reader, one column per source; best per COLUMN black, second blue."""
    gold = report.gold_index("gold_fresh.json")
    by = {label: report.by_attribute(prefix, gold, "data_source") for label, prefix, _, _ in ARMS}
    counts = {src: by[ARMS[0][0]][src][1] for src in SOURCES}
    head = "| Reader | " + " | ".join(f"{src} ({counts[src]})" for src in SOURCES) + " |"
    out = [head, "| --- | " + " | ".join("---:" for _ in SOURCES) + " |"]
    marks = {src: rank_marks([by[label][src][0] for label, _, _, _ in ARMS], True) for src in SOURCES}
    for k, (label, _, _, t3label) in enumerate(ARMS):
        cells = [mark(f"{by[label][src][0]:.4f}", marks[src][k]) for src in SOURCES]
        out.append(f'| <span style="white-space: nowrap">{t3label}</span> | ' + " | ".join(cells) + " |")
    return "\n".join(out)


def splice(article, figure_id, new_table):
    """Replace the markdown table inside <figure id="figure_id"> (header line through last row)."""
    start = article.index(f'<figure id="{figure_id}"')
    t0 = article.index("\n| ", start) + 1
    t1 = article.index("\n\n", t0)
    return article[:t0] + new_table + article[t1:]


# Table 4 — reader speed, from speed_bench.sh's results (the same rows speed_report.py prints for the report).
# Local readers only, in Table 2's order; the withdrawn GLM whole-page arm and the OS-default Apple row are
# not readers in Table 2 and get no row. Hosted readers get no row: their latency is the operator's.
SPEED = [("Composite", "composite", "fleet M3 Max, 1 page at a time", "5.81 GB"),
         ("MinerU2.5-Pro", "mineru", "M4 Max laptop, GPU", "2.33 GB"),
         ("dots.mocr", "mocrnative", "M4 Max laptop, GPU", "3.48 GB"),
         ("GLM-OCR", "glmsdk", "M4 Max laptop, GPU + CPU layout", "2.35 GB"),
         ("PaddleOCR-VL-1.6", "paddlevl", "M4 Max laptop, GPU + CPU layout", "1.95 GB"),
         ("Unlimited-OCR", "unlimnative", "M4 Max laptop, GPU", "3.84 GB"),
         ("RapidOCR", "rapidpipe", "M4 Max laptop, CPU", "349 MB"),
         ("Apple Vision (OS OCR)", "apple", "M4 Max laptop, Neural Engine", "0"),
         ("Qwen 3.6 (VLM)", "qwenlocal", "M4 Max laptop, GPU", "19.35 GB")]


def table4():
    import json
    rows = {}
    for line in open(f"{B}/speed/results.jsonl"):
        if line.strip():
            r = json.loads(line)
            rows[r["arm"]] = r  # a re-timed arm replaces its earlier row
    out = ["| Reader | Runs on | Seconds per page ↓ | Pages per hour ↑ | Weights on disk |",
           "| --- | --- | ---: | ---: | ---: |"]
    for label, arm, where, disk in SPEED:
        per = (rows.get(arm) or {}).get("s_per_page_load_excluded")
        if not per:
            continue
        out.append(f'| <span style="white-space: nowrap">{label}</span> | {where} | {per:.1f} | {3600 / per:,.0f} | {disk} |')
    return "\n".join(out)


def main():
    check = "--check" in sys.argv
    t2, t3, t4 = table2(), table3(), table4()
    s = open(ARTICLE, encoding="utf-8").read()
    new = splice(splice(s, "table-2", t2), "table-3", t3)
    if '<figure id="table-4"' in new:
        new = splice(new, "table-4", t4)
    if check:
        print("Table 2:\n" + t2 + "\n\nTable 3:\n" + t3 + "\n\nTable 4:\n" + t4)
        print("\narticle would change:", new != s)
        return
    open(ARTICLE, "w", encoding="utf-8").write(new)
    print("Tables 2, 3 and 4 rewritten from the result files:", "changed" if new != s else "no change")


if __name__ == "__main__":
    main()
