#!/usr/bin/env python3
"""Figure: consolidation (dreaming) in both store shapes: promote upward vs merge sideways."""
import os
OUT=os.path.expanduser("~/Workspace/pinglin.tw/public/blog/the-shapes-of-agent-memory")
TH={
 "light": dict(bg="#fcfcfb", title="#0b0b0b", body="#52514e", mut="#898781",
               panel="#f3f2ec", ln="#d8d7cd", page="#ffffff"),
 "dark":  dict(bg="#1a1a2e", title="#ffffff", body="#c9c9d4", mut="#8f8f9c",
               panel="#24243a", ln="#3a3a4e", page="#2e2e46"),
}
BLUE="#2a78d6"; GREEN="#1baf7a"; ORANGE="#eb6834"
FONT='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;'
def head(w,h,t,c):
    mk=lambda mid,col:(f'<marker id="{mid}_{t}" markerWidth="14" markerHeight="12" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse">'
                       f'<path d="M0,0 L12,5 L0,10 Z" fill="{col}"/></marker>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
      f'<rect width="100%" height="100%" fill="{c["bg"]}" rx="8"/>'
      f'<defs>{mk("dro",ORANGE)}{mk("drb",BLUE)}{mk("drm",c["mut"])}</defs><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.lab {{ fill: {c["title"]}; font-weight: 600; font-size: 16.5px; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}')
def fig(t,c):
    W,H=1100,620; AW,AH=480,456; gap=30; lm=(W-2*AW-gap)//2; ay=104
    ax,bx=lm,lm+AW+gap
    s=[head(W,H,t,c)+'</style>']
    s.append(f'<text class="title" x="{lm}" y="44">Consolidation runs between sessions</text>')
    s.append(f'<text class="subtitle" x="{lm}" y="72">Same instinct, opposite geometry: one promotes what gets used, the other merges what repeats.</text>')
    for px in (ax,bx):
        s.append(f'<rect x="{px}" y="{ay}" width="{AW}" height="{AH}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    # ---------- A: file shape, promote upward ----------
    s.append(f'<text class="lab" x="{ax+24}" y="{ay+34}" style="fill:{ORANGE}">File-based: promote upward</text>')
    s.append(f'<text class="tiny" x="{ax+24}" y="{ay+56}">Earn a place in the always-loaded index.</text>')
    # index box at top
    ix,iy,iw,ih=ax+130,ay+80,220,56
    s.append(f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" rx="8" fill="{c["page"]}" stroke="{ORANGE}" stroke-width="1.8"/>')
    s.append(f'<text class="lab" x="{ix+iw/2}" y="{iy+25}" text-anchor="middle">MEMORY.md</text>')
    s.append(f'<text class="tiny" x="{ix+iw/2}" y="{iy+44}" text-anchor="middle">Loaded every session</text>')
    # buffer items below
    by=ay+216
    items=[("Recalled 5x",True),("Recalled 4x",True),("Recalled 1x",False),("Recalled 0x",False)]
    for i,(lab,promoted) in enumerate(items):
        cx=ax+38+i*106
        col=ORANGE if promoted else c["ln"]
        op='1' if promoted else '0.5'
        s.append(f'<g opacity="{op}"><rect x="{cx}" y="{by}" width="92" height="40" rx="7" fill="{c["page"]}" stroke="{col}" stroke-width="1.5"/>')
        s.append(f'<text class="tiny" x="{cx+46}" y="{by+25}" text-anchor="middle">{lab}</text></g>')
        if promoted:
            s.append(f'<line x1="{cx+46}" y1="{by-8}" x2="{ix+52+i*56}" y2="{iy+ih+10}" stroke="{ORANGE}" stroke-width="2" marker-end="url(#dro_{t})"/>')
    s.append(f'<text class="tiny" x="{ax+AW/2}" y="{ay+284}" text-anchor="middle">Short-term buffer, deduplicated first</text>')
    s.append(f'<text class="tiny" x="{ax+AW/2}" y="{ay+310}" text-anchor="middle" style="fill:{ORANGE};font-weight:600">Gate: score, recall count, distinct queries</text>')
    s.append(f'<text class="tiny" x="{ax+AW/2}" y="{ay+346}" text-anchor="middle" style="fill:{c["mut"]}">Runs nightly in three phases, a model doing the judging</text>')
    s.append(f'<text class="small" x="{ax+AW/2}" y="{ay+AH-20}" text-anchor="middle" style="fill:{ORANGE}">Usage decides what is always known</text>')
    # ---------- B: structured shape, merge sideways ----------
    s.append(f'<text class="lab" x="{bx+24}" y="{ay+34}" style="fill:{BLUE}">Structured: merge sideways</text>')
    s.append(f'<text class="tiny" x="{bx+24}" y="{ay+56}">Collapse restatements into one canonical unit.</text>')
    # before: three near-dupes
    fy=ay+96
    dupes=["Bought the blue mug","Got a blue mug","Blue mug purchased"]
    for i,d in enumerate(dupes):
        s.append(f'<rect x="{bx+30}" y="{fy+i*46}" width="200" height="34" rx="7" fill="{c["page"]}" stroke="{BLUE}" stroke-width="1.4" opacity="0.75"/>')
        s.append(f'<text class="tiny" x="{bx+40}" y="{fy+i*46+22}">{d}</text>')
    s.append(f'<text class="tiny" x="{bx+30}" y="{fy-10}">Three sessions, one fact</text>')
    # arrow to merged
    mx=bx+268
    s.append(f'<line x1="{bx+238}" y1="{fy+62}" x2="{mx-6}" y2="{fy+62}" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#drm_{t})"/>')
    s.append(f'<text class="tiny" x="{bx+30}" y="{ay+248}" style="fill:{BLUE};font-weight:600">Cosine &#8805; 0.92, on vectors the store already has</text>')
    s.append(f'<text class="tiny" x="{bx+30}" y="{ay+272}">Longest phrasing wins, provenance kept, no model calls</text>')
    s.append(f'<rect x="{mx}" y="{fy+40}" width="184" height="46" rx="7" fill="{c["page"]}" stroke="{BLUE}" stroke-width="2"/>')
    s.append(f'<text class="tiny" x="{mx+90}" y="{fy+60}" text-anchor="middle" style="font-weight:600">Bought the blue mug</text>')
    s.append(f'<text class="tiny" x="{mx+90}" y="{fy+78}" text-anchor="middle">Provenance x3</text>')
    # miss case
    my=ay+346
    s.append(f'<rect x="{bx+24}" y="{my}" width="{AW-48}" height="56" rx="8" fill="none" stroke="{c["mut"]}" stroke-width="1.4" stroke-dasharray="6 5"/>')
    s.append(f'<text class="tiny" x="{bx+38}" y="{my+22}" style="fill:{c["mut"]}">Missed: "picked up a cobalt cup", the same event</text>')
    s.append(f'<text class="tiny" x="{bx+38}" y="{my+42}" style="fill:{c["mut"]}">in other words. Catching it needs a model per pair.</text>')
    s.append(f'<text class="tiny" x="{bx+30}" y="{ay+300}" style="fill:{c["mut"]}">Tiers: exact dedup on write, per chat when idle,</text>')
    s.append(f'<text class="tiny" x="{bx+30}" y="{ay+322}" style="fill:{c["mut"]}">then the whole store daily</text>')
    s.append(f'<text class="small" x="{bx+AW/2}" y="{ay+AH-20}" text-anchor="middle" style="fill:{BLUE}">Similarity catches restatements, not paraphrase</text>')
    s.append('</svg>')
    return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"dreaming_{t}.svg"),"w").write(fig(t,c))
        print("wrote",t)
