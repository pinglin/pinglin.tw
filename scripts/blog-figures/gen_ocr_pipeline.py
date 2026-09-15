#!/usr/bin/env python3
"""Figure 1 of the beyond-ocr-scores post: where OCR sits in a RAG or agent system.
Ingestion runs left to right along the top panel; serving runs back along the bottom panel. The
reader (this post's subject) is the highlighted box; the dashed arrow is an agent reading a page on
demand.

Same palette and type scale as gen_architecture.py, outputs into public/blog/beyond-ocr-scores/.
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../public/blog/beyond-ocr-scores")
TH = {
    "light": dict(bg="#fcfcfb", title="#0b0b0b", body="#52514e", mut="#898781",
                  panel="#f3f2ec", ln="#d8d7cd", page="#ffffff"),
    "dark":  dict(bg="#1a1a2e", title="#ffffff", body="#c9c9d4", mut="#8f8f9c",
                  panel="#24243a", ln="#3a3a4e", page="#2e2e46"),
}
BLUE = "#2a78d6"; ORANGE = "#eb6834"
FONT = 'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;'


def head(w, h, t, c):
    mk = lambda mid, col: (f'<marker id="{mid}_{t}" markerWidth="14" markerHeight="12" refX="11" refY="5" orient="auto" '
                           f'markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="{col}"/></marker>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="100%" height="100%" fill="{c["bg"]}" rx="8"/>'
            f'<defs>{mk("arc", c["mut"])}{mk("aro", ORANGE)}</defs><style>'
            f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
            f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
            f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
            f'.lab {{ fill: {c["title"]}; font-weight: 600; font-size: 16.5px; }}'
            f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}'
            f'.band {{ font-size: 15px; font-weight: 600; letter-spacing: 0.04em; fill: {c["mut"]}; }}</style>')


def box(s, c, x, y, w, h, stroke, lab, sub=None, sw=1.6):
    s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{c["page"]}" stroke="{stroke}" stroke-width="{sw}"/>')
    if sub:
        s.append(f'<text class="lab" x="{x+w/2}" y="{y+24}" text-anchor="middle">{lab}</text>')
        s.append(f'<text class="tiny" x="{x+w/2}" y="{y+44}" text-anchor="middle">{sub}</text>')
    else:
        s.append(f'<text class="lab" x="{x+w/2}" y="{y+h/2+6}" text-anchor="middle">{lab}</text>')


def arrow(s, c, t, pts, col=None, dashed=False):
    """Polyline with an arrowhead on its last segment; end points sit 5px short so the head lands on the box."""
    col = col or c["mut"]
    mid = "aro" if col == ORANGE else "arc"
    d = " ".join(f"{x},{y}" for x, y in pts)
    dash = ' stroke-dasharray="6 4"' if dashed else ""
    s.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="1.8"{dash} marker-end="url(#{mid}_{t})"/>')


def panel(s, c, y0, y1, label):
    s.append(f'<rect x="40" y="{y0}" width="1120" height="{y1-y0}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    s.append(f'<text class="band" x="58" y="{y0+27}">{label}</text>')


def fig(t, c):
    W, H = 1200, 690
    s = [head(W, H, t, c)]
    s.append('<text class="title" x="40" y="44">Where the reader sits</text>')
    s.append('<text class="subtitle" x="40" y="72">Ingestion runs along the top, serving along the bottom.</text>')
    s.append('<text class="subtitle" x="40" y="96">Nothing on the serving side sees the page — only the text that was read off it.</text>')

    # ---- ingest panel: centre lines of the middle boxes and of the two branches ----
    r1 = 258
    up, lo = r1 - 60, r1 + 60
    panel(s, c, 134, lo + 50, "INGEST")
    box(s, c, 70, r1-28, 170, 56, c["ln"], "Documents", "PDFs, scans, photos")
    box(s, c, 270, r1-28, 150, 56, c["ln"], "Text layer?", "Check the PDF")
    box(s, c, 465, up-28, 230, 56, c["ln"], "Extract text layer", "Born-digital · no OCR")
    s.append(f'<text class="tiny" x="580" y="{lo-38}" text-anchor="middle" style="fill:{ORANGE}">The eleven readers in this post</text>')
    box(s, c, 465, lo-28, 230, 56, ORANGE, "Read the page", "Scan, photo · layout + OCR", sw=2.2)
    box(s, c, 735, r1-28, 210, 56, c["ln"], "Structured text", "Blocks, tables, formulas")
    box(s, c, 980, r1-28, 150, 56, BLUE, "Index", "Chunk · embed")
    arrow(s, c, t, [(240, r1), (265, r1)])
    arrow(s, c, t, [(420, r1-8), (460, up)])
    arrow(s, c, t, [(420, r1+8), (460, lo)])
    s.append(f'<text class="tiny" x="421" y="{up+16}">Yes</text>')
    s.append(f'<text class="tiny" x="423" y="{lo-2}">No</text>')
    arrow(s, c, t, [(695, up), (730, r1-8)])
    arrow(s, c, t, [(695, lo), (730, r1+8)])
    arrow(s, c, t, [(945, r1), (975, r1)])

    # ---- serve panel, right to left ----
    r2 = 528
    panel(s, c, 440, r2 + 128, "SERVE")
    box(s, c, 980, r2-28, 150, 56, BLUE, "Retrieve", "Top-k chunks")
    box(s, c, 570, r2-28, 220, 56, c["ln"], "LLM or agent", "Reasons over the chunks")
    box(s, c, 230, r2-28, 220, 56, c["ln"], "Answer or action", "Only as good as the read")
    box(s, c, 570, r2+62, 220, 44, c["ln"], "Question or task")
    arrow(s, c, t, [(1055, r1+28), (1055, r2-33)])                   # the index feeds retrieval
    arrow(s, c, t, [(980, r2), (795, r2)])
    arrow(s, c, t, [(570, r2), (455, r2)])
    arrow(s, c, t, [(680, r2+62), (680, r2+33)])
    # an agent reading a page on demand: back up into the reader, dashed, crossing the panel gap
    arrow(s, c, t, [(630, r2-28), (630, lo+76), (580, lo+76), (580, lo+33)], col=ORANGE, dashed=True)
    s.append(f'<text class="tiny" x="642" y="{lo+100}" style="fill:{ORANGE}">Read a page on demand (tool call)</text>')
    s.append('</svg>')
    return "".join(s)


if __name__ == "__main__":
    for t, c in TH.items():
        open(os.path.join(OUT, f"pipeline_{t}.svg"), "w").write(fig(t, c))
        print("wrote", t)
