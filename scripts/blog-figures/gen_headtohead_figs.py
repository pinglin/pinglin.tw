#!/usr/bin/env python3
"""Figures: lineage head-to-head accuracy (LoCoMo + LME-S rank flip) and retrieval-context cost."""
import os
OUT=os.path.expanduser("~/Workspace/pinglin.tw/public/blog/the-shapes-of-agent-memory")
TH={
 "light": dict(bg="#fcfcfb", title="#0b0b0b", body="#52514e", mut="#898781",
               axis="#c3c2b7", grid="#e1e0d9"),
 "dark":  dict(bg="#1a1a2e", title="#ffffff", body="#c9c9d4", mut="#8f8f9c",
               axis="#55556a", grid="#3a3a4e"),
}
BLUE="#2a78d6"; GREEN="#1baf7a"; ORANGE="#eb6834"
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
def bars(s,c,x0,x1,y0,y1,vmax,data,fmt="{:g}"):
    n=len(data); gw=(x1-x0)/n; bw=min(88,gw*0.62)
    for i,(lab,v,col,op) in enumerate(data):
        cx=x0+gw*(i+0.5); bh=(y0-y1)*v/vmax
        s.append(f'<rect x="{cx-bw/2:.1f}" y="{y0-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{col}" opacity="{op}"/>')
        s.append(f'<text class="small" x="{cx:.1f}" y="{y0-bh-8:.1f}" text-anchor="middle" style="fill:{col};font-weight:600">{fmt.format(v)}</text>')
        for j,part in enumerate(lab.split("\\n")):
            s.append(f'<text class="tick" x="{cx:.1f}" y="{y0+24+j*17}" text-anchor="middle">{part}</text>')
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
def acc(t,c):
    W,H=1100,600
    s=[head(W,H,c)]
    s.append(f'<text class="title" x="70" y="46">Store accuracy, one reader and one judge</text>')
    s.append(f'<text class="subtitle" x="70" y="74">Each store contributes only its top-20 retrieval; LoCoMo evaluated by gpt-4o-mini, LongMemEval-S by the local 35B (official rubric).</text>')
    ay0,ay1=430,140
    for v in range(0,101,25):
        y=ay0-(ay0-ay1)*v/100
        s.append(f'<line class="grid" x1="100" y1="{y:.1f}" x2="620" y2="{y:.1f}"/>')
        s.append(f'<line class="grid" x1="700" y1="{y:.1f}" x2="1030" y2="{y:.1f}"/>')
        s.append(f'<text class="tick" x="88" y="{y+5:.1f}" text-anchor="end">{v}</text>')
    bars(s,c,100,620,ay0,ay1,100,[
        ("Hybrid",78.3,BLUE,1),("Place\\n(MemPalace)",77.9,BLUE,0.55),("Zep Cloud",74.6,GREEN,1),
        ("Graphiti\\nOSS",53.4,GREEN,0.55),("Graphiti\\nbge-m3",52.9,GREEN,0.35)],"{:.1f}")
    bars(s,c,700,1030,ay0,ay1,100,[
        ("Hybrid",80,BLUE,1),("Place\\n(MemPalace)",60,BLUE,0.55),("Graphiti\\nOSS",35,GREEN,0.55)])
    s.append(f'<text class="small" x="360" y="516" text-anchor="middle" style="font-weight:600;fill:{c["title"]}">LoCoMo (n=1,540)</text>')
    s.append(f'<text class="small" x="865" y="516" text-anchor="middle" style="font-weight:600;fill:{c["title"]}">LongMemEval-S (n=100, official rubric)</text>')
    s.append(f'<text class="small" x="100" y="556" style="fill:{c["mut"]}">Blue: raw dated facts, ranked recall &#183; Green: LLM-distilled graph. The ranking does not transfer across benchmarks.</text>')
    s.append('</svg>'); return "".join(s)
def cost(t,c):
    W,H=1100,560
    s=[head(W,H,c)]
    s.append(f'<text class="title" x="70" y="46">The cost of a retrieval, head-to-head</text>')
    s.append(f'<text class="subtitle" x="70" y="74">Median context handed to the reader per question. The hosted graph spends six times the context and still scores lower.</text>')
    ay0,ay1=430,140
    for v in range(0,26,5):
        y=ay0-(ay0-ay1)*v/25
        s.append(f'<line class="grid" x1="110" y1="{y:.1f}" x2="1030" y2="{y:.1f}"/>')
        s.append(f'<text class="tick" x="98" y="{y+5:.1f}" text-anchor="end">{v}k</text>')
    bars(s,c,110,1030,ay0,ay1,25,[
        ("Hybrid",4.0,BLUE,1),("Place (MemPalace)",3.5,BLUE,0.55),
        ("Zep Cloud",21.5,GREEN,1),("Graphiti OSS",7.9,GREEN,0.55)],"{:.1f}k")
    s.append(f'<text class="small" x="110" y="496" style="fill:{c["mut"]}">Chars of retrieved context per question. The other cost sits at ingest: raw-turn stores embed, the graphs reason per message,</text>')
    s.append(f'<text class="small" x="110" y="520" style="fill:{c["mut"]}">roughly twelve days of GPU time per run at LongMemEval-M scale, against hours for the embedding-only stores.</text>')
    s.append('</svg>'); return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"h2h_accuracy_{t}.svg"),"w").write(acc(t,c))
        open(os.path.join(OUT,f"h2h_context_cost_{t}.svg"),"w").write(cost(t,c))
        print("wrote",t)
