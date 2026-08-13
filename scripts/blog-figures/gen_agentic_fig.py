#!/usr/bin/env python3
"""Figures: agentic success rate by actor, one per benchmark (ALFWorld, WebShop)."""
import os
OUT=os.path.expanduser("~/Workspace/pinglin.tw/public/blog/the-shapes-of-agent-memory")
TH={
 "light": dict(bg="#fcfcfb", title="#0b0b0b", body="#52514e", mut="#898781",
               axis="#c3c2b7", grid="#e1e0d9", none_="#b9b7ae"),
 "dark":  dict(bg="#1a1a2e", title="#ffffff", body="#c9c9d4", mut="#8f8f9c",
               axis="#55556a", grid="#3a3a4e", none_="#5a5a70"),
}
BLUE="#2a78d6"; GREEN="#1baf7a"
FONT='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;'
def head(w,h,c):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
      f'<rect width="100%" height="100%" fill="{c["bg"]}" rx="8"/><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.tick {{ font-size: 15px; fill: {c["mut"]}; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.axis {{ stroke: {c["axis"]}; stroke-width: 1.2; }}'
      f'.grid {{ stroke: {c["grid"]}; stroke-width: 1; }}</style>')
def panel(c,title,subtitle,bars):
    W,H=1100,560; x0,x1,y0,y1=100,1030,430,130
    s=[head(W,H,c)]
    s.append(f'<text class="title" x="70" y="46">{title}</text>')
    s.append(f'<text class="subtitle" x="70" y="74">{subtitle}</text>')
    for v in range(0,101,20):
        y=y0-(y0-y1)*v/100
        s.append(f'<line class="grid" x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}"/>')
        s.append(f'<text class="tick" x="{x0-12}" y="{y+5:.1f}" text-anchor="end">{v}%</text>')
    n=len(bars); gw=(x1-x0)/n; bw=88
    for i,(lab,v,kind) in enumerate(bars):
        cx=x0+gw*(i+0.5); bx=cx-bw/2
        col={"none":c["none_"],"bank":BLUE,"trained":GREEN}[kind]
        if v is None:
            s.append(f'<rect x="{bx:.1f}" y="{y0-64}" width="{bw}" height="64" rx="3" fill="none" stroke="{col}" stroke-width="1.6" stroke-dasharray="5 4"/>')
            s.append(f'<text class="tick" x="{cx:.1f}" y="{y0-28:.1f}" text-anchor="middle">Not run</text>')
        else:
            bh=(y0-y1)*v/100
            s.append(f'<rect x="{bx:.1f}" y="{y0-bh:.1f}" width="{bw}" height="{bh:.1f}" rx="3" fill="{col}"/>')
            tcol=col if kind!="none" else c["mut"]
            s.append(f'<text class="small" x="{cx:.1f}" y="{y0-bh-8:.1f}" text-anchor="middle" style="fill:{tcol};font-weight:600">{v:g}</text>')
        s.append(f'<text class="tick" x="{cx:.1f}" y="454" text-anchor="middle">{lab}</text>')
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    s.append(f'<rect x="100" y="496" width="17" height="17" rx="3" fill="{c["none_"]}"/>')
    s.append(f'<text class="small" x="126" y="510">No memory (scaffolds kept)</text>')
    s.append(f'<rect x="400" y="496" width="17" height="17" rx="3" fill="{BLUE}"/>')
    s.append(f'<text class="small" x="426" y="510">With the experience bank</text>')
    s.append(f'<rect x="700" y="496" width="17" height="17" rx="3" fill="{GREEN}"/>')
    s.append(f'<text class="small" x="726" y="510">MemHarness, GRPO-trained</text>')
    s.append('</svg>'); return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        alf=panel(c,"Success rate by actor, ALFWorld",
          "Macro SR over 134 unseen games. Memory moves the weak actor directionally; the frontier actor saturates.",
          [("35B",60.3,"none"),("35B + bank",64.5,"bank"),("Sonnet",95.9,"none"),("Sonnet + bank",97.3,"bank"),("MemHarness (OOD)",85.9,"trained")])
        web=panel(c,"Success rate by actor, WebShop",
          "Strict SR over 500 sessions; partial-credit scores in the table. Only training reaches the bar.",
          [("35B",37.6,"none"),("35B + bank",41.8,"bank"),("Sonnet",44.4,"none"),("Sonnet + bank",45.0,"bank"),("MemHarness",75.6,"trained")])
        open(os.path.join(OUT,f"alfworld_success_{t}.svg"),"w").write(alf)
        open(os.path.join(OUT,f"webshop_success_{t}.svg"),"w").write(web)
        print("wrote",t)
