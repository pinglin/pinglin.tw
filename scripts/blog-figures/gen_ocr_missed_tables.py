#!/usr/bin/env python3
"""Figure 5 of the beyond-ocr-scores post: the eight gold tables the composite misses, by failure.

One panel per failure shape, each a crop of the real held-out page around the gold table (red box;
blue where a sibling table on the same page IS paired), captioned with what the reader emitted for
it. The eight are read from the evaluator's own per-table result for the composite arm — anything
scoring at or below zero — so the figure cannot drift from Table 2's "8/473". Composed at 2x
(2200 px) like the sources grid; JPEG because the content is scanned pages.

Needs ~/.shubo-bench (gold_fresh.json, fresh-in/ page images, odb-eval/result/) and Pillow.
"""
import glob
import json
import os
import re

from PIL import Image, ImageDraw, ImageFont

B = os.path.expanduser("~/.shubo-bench")
ARM = "compositev6full"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../public/blog/beyond-ocr-scores")
os.makedirs(OUT, exist_ok=True)

THEMES = {
    "dark": dict(BG="#1a1a2e", INK="#ffffff", INK2="#c9c9d4", MUTED="#8f8f9c", AXIS="#55556a"),
    "light": dict(BG="#fcfcfb", INK="#0b0b0b", INK2="#52514e", MUTED="#898781", AXIS="#c3c2b7"),
}
RED, BLUE = (214, 39, 40), (31, 119, 180)


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


def cjk_font(size):
    for path in ("/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Light.ttc"):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return font(size)


def load():
    per = json.load(open(f"{B}/odb-eval/result/{ARM}_quick_match_table_per_table_TEDS.json"))
    missed = {k: v["TEDS"] for k, v in per.items() if v["TEDS"] <= 0}
    gold = {os.path.basename(g["page_info"]["image_path"]): g for g in json.load(open(f"{B}/gold_fresh.json"))}
    return missed, gold


def box(det):
    p = det["poly"]
    return (min(p[0::2]), min(p[1::2]), max(p[0::2]), max(p[1::2]))


def page_image(page):
    stem = os.path.splitext(page)[0]
    return Image.open(glob.glob(f"{B}/fresh-in/{glob.escape(stem)}.*")[0]).convert("RGB")


def crop_with_boxes(page, boxes, pad, target_w, target_h, extra=None, upscale=False):
    """Crop the union of `boxes` (each (bbox, colour)) plus `pad` px, draw the boxes, fit to target."""
    im = page_image(page)
    xs = [b[0] for b, _ in boxes] + [b[2] for b, _ in boxes]
    ys = [b[1] for b, _ in boxes] + [b[3] for b, _ in boxes]
    x0, y0 = max(0, min(xs) - pad[0]), max(0, min(ys) - pad[1])
    x1, y1 = min(im.width, max(xs) + pad[2]), min(im.height, max(ys) + pad[3])
    if extra:  # widen to a requested aspect so short strips do not become a sliver
        ex0, ey0, ex1, ey1 = extra
        x0, y0, x1, y1 = max(0, min(x0, ex0)), max(0, min(y0, ey0)), min(im.width, max(x1, ex1)), min(im.height, max(y1, ey1))
    cr = im.crop((int(x0), int(y0), int(x1), int(y1)))
    d = ImageDraw.Draw(cr)
    lw = max(4, int(cr.width / 160))
    for b, colour in boxes:
        d.rectangle((b[0] - x0, b[1] - y0, b[2] - x0, b[3] - y0), outline=colour, width=lw)
    if upscale and cr.width < target_w and cr.height < target_h:
        k = min(target_w / cr.width, target_h / cr.height)
        cr = cr.resize((int(cr.width * k), int(cr.height * k)), Image.LANCZOS)
    else:
        cr.thumbnail((target_w, target_h), Image.LANCZOS)
    return cr


def panels(missed, gold):
    """The six failure shapes, in the order the post's prose lists them. Each entry: title, the
    crops to draw (one or two, stacked), what the reader emitted, and the one-line failure."""
    def tables(page):
        return [d for d in gold[page]["layout_dets"] if d.get("category_type") == "table"]

    def key_for(fragment, idx):
        return next(k for k in missed if fragment in k and k.endswith(f"_[{idx}]"))

    def page_of(k):
        return re.match(r"^(.*)_\[\d+\]$", k).group(1)

    out = []
    # A. two one-row strips on a slide
    kA = key_for("PresentationSpecification_page_010", 0)
    pA = page_of(kA)
    tA = tables(pA)
    out.append(dict(
        title="A · One-row strips on a slide (2 of 8)",
        crops=[crop_with_boxes(pA, [(box(tA[0]), RED), (box(tA[1]), RED)], (90, 250, 90, 90), 640, 430)],
        emitted='"- 1. A short video summary in 1 min PLUS a classroom live…"',
        why="A single row of three cells reads as a sentence to this layout head; dots.mocr, GLM-OCR, PaddleOCR-VL-1.6 and both hosted VLMs read both as tables."))
    # B. a grid of short tokens
    kB = key_for("Language_Change_page_021", 0)
    pB = page_of(kB)
    out.append(dict(
        title="B · A grid of short tokens (1)",
        crops=[crop_with_boxes(pB, [(box(tables(pB)[0]), RED)], (80, 240, 380, 60), 640, 430)],
        emitted='"VO Pr NG RelN" … six lines',
        why="Six rows of four tokens come out as six lines — the layout stage calls it a list; eight other readers get the grid."))
    # C. an infographic on a photograph
    kC = key_for("magazinesclubnew_page_031", 0)
    pC = page_of(kC)
    out.append(dict(
        title="C · An infographic on a photograph (1)",
        crops=[crop_with_boxes(pC, [(box(tables(pC)[0]), RED)], (40, 40, 40, 40), 640, 430)],
        emitted='"How budget will affect labour costs" — the title only',
        why="The figures sit on artwork rather than in a grid; nothing below the title survives here, though eight other readers read it."))
    # D. two stacked panels merged into one grid
    kD = key_for("c7771a62", 1)
    pD = page_of(kD)
    tD = tables(pD)
    out.append(dict(
        title="D · Two stacked panels merged (1)",
        crops=[crop_with_boxes(pD, [(box(tD[0]), BLUE), (box(tD[1]), RED)], (40, 60, 40, 40), 640, 430)],
        emitted='one <table> headed "Country group 1 | Country group 2"',
        why="The upper panel (blue) pairs with its gold; the lower (red) has no partner left."))
    # E. a signature block
    kE = key_for("d5a3ea83", 1)
    pE = page_of(kE)
    tE = tables(pE)
    out.append(dict(
        title="E · A signature block (1)",
        crops=[crop_with_boxes(pE, [(box(tE[1]), RED)], (60, 230, 60, 110), 640, 430)],
        emitted="four titles and four names, as headings",
        why="Two rows of four cells with no rules between them read as a run of headings; GLM-OCR's SDK reads it at 0.99."))
    # F. two schedule lines on the 96-table scoreboard page
    kF3, kF25 = key_for("magazinesclubnew_page_025", 3), key_for("magazinesclubnew_page_025", 25)
    pF = page_of(kF3)
    tF = tables(pF)
    out.append(dict(
        title="F · Schedule lines on a 96-table page (2)",
        crops=[crop_with_boxes(pF, [(box(tF[3]), RED)], (60, 110, 60, 110), 640, 205, upscale=True),
               crop_with_boxes(pF, [(box(tF[25]), RED)], (30, 110, 30, 110), 640, 205, upscale=True)],
        emitted='"8:30 p.m. USC at Maryland" — as text',
        why=f"The scorer pairs it with a transactions fragment: TEDS {missed[kF3]:.2f}, the miss recorded below zero."))
    return out


def compose(theme, P, items):
    W, cols = 2200, 3
    cell = 700
    left = (W - cols * cell) // 2
    crop_h, label_h = 440, 290
    row_h = crop_h + label_h
    top = 230
    H = top + 2 * row_h + 20
    im = Image.new("RGB", (W, H), P["BG"])
    d = ImageDraw.Draw(im)
    d.text((120, 40), "Where the eight missing tables are", font=font(60, bold=True), fill=P["INK"])
    d.text((120, 118), "Composite reader, held-out set: the 8 of 473 gold tables that score at or below zero, by failure. "
                       "Red: the gold table. Blue: a sibling table the scorer did pair.", font=font(32), fill=P["INK2"])
    f_title, f_emit, f_why = font(30, bold=True), font(25, mono=True), font(25)
    for i, it in enumerate(items):
        r, c = divmod(i, cols)
        x0 = left + c * cell + 20
        y0 = top + r * row_h
        y = y0
        for cr in it["crops"]:
            px = x0 + (660 - cr.width) // 2
            im.paste(cr, (px, y))
            d.rectangle([px - 1, y - 1, px + cr.width, y + cr.height], outline=P["AXIS"], width=2)
            y += cr.height + 14
        ty = y0 + crop_h + 18
        d.text((x0, ty), it["title"], font=f_title, fill=P["INK"])
        def wrap(text, f, width=660):
            words, lines, cur = text.split(), [], ""
            for w in words:
                t = (cur + " " + w).strip()
                if d.textlength(t, font=f) > width:
                    lines.append(cur)
                    cur = w
                else:
                    cur = t
            lines.append(cur)
            return lines
        y = ty + 46
        for line in wrap("emitted: " + it["emitted"], f_emit)[:2]:
            d.text((x0, y), line, font=f_emit, fill=P["INK2"])
            y += 32
        y += 10
        for line in wrap(it["why"], f_why)[:3]:
            d.text((x0, y), line, font=f_why, fill=P["MUTED"])
            y += 34
    out = f"{OUT}/missed_tables_{theme}.jpg"
    im.save(out, "JPEG", quality=90, optimize=True)
    return out


missed, gold = load()
assert len(missed) == 8, f"expected 8 missed tables in {ARM}, found {len(missed)}"
items = panels(missed, gold)
for theme, P in THEMES.items():
    out = compose(theme, P, items)
    print("wrote", out, f"{os.path.getsize(out)/1024:.0f} KB")
