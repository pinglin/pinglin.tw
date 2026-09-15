#!/usr/bin/env python3
"""Figure 1 of the beyond-ocr-scores post: one real held-out page per OmniDocBench source.

The example for each source is chosen mechanically, not by eye: the source's most common layout and
language, then the median page by text-block count. That makes each thumbnail a typical page for its
source rather than the prettiest one. Composed at 2x (2200 px wide) so it stays crisp in the post's
1100 px column; saved as JPEG because the content is scanned pages.

Needs the benchmark checkout at ~/.shubo-bench (gold_fresh.json + fresh-in/ page images) and Pillow.
Run once; unlike gen_ocr_bench_figs.py nothing here changes as evaluation arms land.
"""
import glob
import json
import os
from collections import Counter, defaultdict

from PIL import Image, ImageDraw, ImageFont

B = os.path.expanduser("~/.shubo-bench")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../public/blog/beyond-ocr-scores")
os.makedirs(OUT, exist_ok=True)

THEMES = {
    "dark": dict(BG="#1a1a2e", INK="#ffffff", INK2="#c9c9d4", MUTED="#8f8f9c", AXIS="#55556a"),
    "light": dict(BG="#fcfcfb", INK="#0b0b0b", INK2="#52514e", MUTED="#898781", AXIS="#c3c2b7"),
}
LANG = {"english": "English", "simplified_chinese": "Simplified Chinese",
        "traditional_chinese": "Traditional Chinese", "en_ch_mixed": "mixed EN/ZH", "other": "other"}
LAYOUT = {"single_column": "single column", "double_column": "double column", "three_column": "three column",
          "1andmore_column": "mixed columns", "other_layout": "other layout"}


def pick_examples():
    gold = json.load(open(f"{B}/gold_fresh.json"))
    by = defaultdict(list)
    for g in gold:
        a = g["page_info"]["page_attribute"]
        stem = os.path.splitext(os.path.basename(g["page_info"]["image_path"]))[0]
        ntext = sum(1 for d in g["layout_dets"] if d.get("category_type") == "text_block")
        by[a["data_source"]].append((stem, a["layout"], a["language"], ntext))
    picks = []
    for src, rows in sorted(by.items(), key=lambda kv: -len(kv[1])):   # Table 1 order: by page count
        lay = Counter(r[1] for r in rows).most_common(1)[0][0]
        lang = Counter(r[2] for r in rows).most_common(1)[0][0]
        cand = sorted([r for r in rows if r[1] == lay and r[2] == lang] or rows, key=lambda r: r[3])
        stem, lay, lang, _ = cand[len(cand) // 2]
        hits = glob.glob(f"{B}/fresh-in/{glob.escape(stem)}.*")
        if not hits:
            raise SystemExit(f"no page image for {src}: {stem}")
        picks.append((src, len(rows), hits[0], lay, lang))
    return picks


def font(size, bold=False, mono=False):
    path = "/System/Library/Fonts/SFNSMono.ttf" if mono else "/System/Library/Fonts/SFNS.ttf"
    try:
        f = ImageFont.truetype(path, size)
        try:
            f.set_variation_by_name("Bold" if bold else "Regular")
        except Exception:
            pass
        return f
    except Exception:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size, index=1 if bold else 0)


def compose(theme, P, picks):
    W = 2200
    cols, cell = 5, 400
    left = (W - cols * cell) // 2
    box_w, box_h = 336, 470
    row_h = box_h + 180
    top = 220
    H = top + 2 * row_h + 10
    im = Image.new("RGB", (W, H), P["BG"])
    d = ImageDraw.Draw(im)
    d.text((120, 40), "Ten sources, one held-out page each", font=font(60, bold=True), fill=P["INK"])
    d.text((120, 118), "OmniDocBench v1.6, held-out 1,250. Each example is the median page of its source's "
                       "most common layout and language.", font=font(34), fill=P["INK2"])
    f_name, f_count, f_sub = font(29, mono=True), font(28), font(26)
    for i, (src, n, path, lay, lang) in enumerate(picks):
        r, c = divmod(i, cols)
        x0 = left + c * cell + (cell - box_w) // 2
        y0 = top + r * row_h
        page = Image.open(path).convert("RGB")
        page.thumbnail((box_w, box_h), Image.LANCZOS)
        px = x0 + (box_w - page.width) // 2
        py = y0 + (box_h - page.height) // 2
        im.paste(page, (px, py))
        d.rectangle([px - 1, py - 1, px + page.width, py + page.height], outline=P["AXIS"], width=2)
        # Three short lines: long names such as historical_document overflow a 400 px cell otherwise.
        ty = y0 + box_h + 24
        d.text((x0, ty), src, font=f_name, fill=P["INK"])
        d.text((x0, ty + 42), f"{n} pages", font=f_count, fill=P["INK2"])
        d.text((x0, ty + 82), f"{LANG[lang]} · {LAYOUT[lay]}", font=f_sub, fill=P["MUTED"])
    out = f"{OUT}/sources_{theme}.jpg"
    im.save(out, "JPEG", quality=90, optimize=True)
    return out


picks = pick_examples()
for src, n, path, lay, lang in picks:
    print(f"  {src:<20} {n:>3}  {LANG[lang]:<19} {LAYOUT[lay]:<14} {os.path.basename(path)[:60]}")
for theme, P in THEMES.items():
    out = compose(theme, P, picks)
    print("wrote", out, f"{os.path.getsize(out)/1024:.0f} KB")
