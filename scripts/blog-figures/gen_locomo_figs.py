#!/usr/bin/env python3
"""Figures: LoCoMo accuracy by category + LoCoMo token cost (mirrors the LongMemEval pair)."""
import os
OUT=os.path.expanduser("~/Workspace/pinglin.tw/public/blog/the-shapes-of-agent-memory")
TH={
 "light": dict(bg="#fcfcfb", title="#0b0b0b", body="#52514e", mut="#898781",
               axis="#c3c2b7", grid="#e1e0d9"),
 "dark":  dict(bg="#1a1a2e", title="#ffffff", body="#c9c9d4", mut="#8f8f9c",
               axis="#55556a", grid="#3a3a4e"),
}
BLUE="#2a78d6"; ORANGE="#eb6834"
FONT='font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;'
def head(w,h,c):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
      f'<rect width="100%" height="100%" fill="{c["bg"]}" rx="8"/><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.tick {{ font-size: 16px; fill: {c["mut"]}; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.axis {{ stroke: {c["axis"]}; stroke-width: 1.2; }}'
      f'.grid {{ stroke: {c["grid"]}; stroke-width: 1; }}</style>')
def grid(s,c,x0,x1,y0,y1,vmax,step,fmt):
    v=0
    while v<=vmax:
        y=y0-(y0-y1)*v/vmax
        s.append(f'<line class="grid" x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}"/>')
        s.append(f'<text class="tick" x="{x0-12}" y="{y+5:.1f}" text-anchor="end">{fmt(v)}</text>')
        v+=step
def acc(t,c):
    W,H=1100,580; x0,x1,y0,y1=100,1030,450,130
    s=[head(W,H,c)]
    s.append(f'<text class="title" x="70" y="46">Accuracy by question type, LoCoMo</text>')
    s.append(f'<text class="subtitle" x="70" y="74">Same arms, same judge, n=300 stratified. Structured wins every memory category; file-based wins two.</text>')
    grid(s,c,x0,x1,y0,y1,100,20,lambda v:f"{v}%")
    cats=[("Temporal",69,31),("Temporal-inf.",52,26),("Open-domain",66,41),("Single-hop",37,44),("Adversarial",25,51)]
    gw=(x1-x0)/5
    for i,(name,pv,mv) in enumerate(cats):
        cx=x0+gw*(i+0.5); bw=46
        for dx,v,col in ((-bw-3,pv,BLUE),(3,mv,ORANGE)):
            bh=(y0-y1)*v/100
            s.append(f'<rect x="{cx+dx:.1f}" y="{y0-bh:.1f}" width="{bw}" height="{bh:.1f}" rx="3" fill="{col}"/>')
            s.append(f'<text class="small" x="{cx+dx+bw/2:.1f}" y="{y0-bh-8:.1f}" text-anchor="middle" style="fill:{col};font-weight:600">{v}</text>')
        s.append(f'<text class="tick" x="{cx:.1f}" y="474" text-anchor="middle">{name}</text>')
        if mv>pv:
            s.append(f'<text class="small" x="{cx:.1f}" y="{y0-(y0-y1)*mv/100-34:.1f}" text-anchor="middle" style="fill:{ORANGE};font-weight:600">File-based wins</text>')
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    s.append(f'<rect x="100" y="506" width="17" height="17" rx="3" fill="{BLUE}"/>')
    s.append(f'<text class="small" x="126" y="520">Structured (0.497 all / 0.561 excl-adversarial)</text>')
    s.append(f'<rect x="530" y="506" width="17" height="17" rx="3" fill="{ORANGE}"/>')
    s.append(f'<text class="small" x="556" y="520">File-based (0.387 / 0.356)</text>')
    s.append(f'<text class="small" x="100" y="548" style="fill:{c["mut"]}">No-memory floor: 0.217. Nearly all its wins are adversarial refusals</text>')
    s.append('</svg>'); return "".join(s)
def cost(t,c):
    W,H=1100,560; x0,x1,y0,y1=110,1030,440,130
    s=[head(W,H,c)]
    s.append(f'<text class="title" x="70" y="46">The cost of an answer, LoCoMo</text>')
    s.append(f'<text class="subtitle" x="70" y="74">Model-reasoning tokens, ingest amortized per question. Shorter histories shrink the bill; the ordering holds.</text>')
    grid(s,c,x0,x1,y0,y1,60,20,lambda v:f"{v}k")
    groups=[("Reasoning tokens per question",22.4,11.6),("Reasoning tokens per correct answer",58.0,23.3)]
    gw=(x1-x0)/2
    for i,(name,mv,pv) in enumerate(groups):
        cx=x0+gw*(i+0.5); bw=64
        for dx,v,col,lab in ((-bw-8,mv,ORANGE,f"{mv:.0f}k"),(8,pv,BLUE,f"{pv:.0f}k")):
            bh=(y0-y1)*v/60
            s.append(f'<rect x="{cx+dx:.1f}" y="{y0-bh:.1f}" width="{bw}" height="{bh:.1f}" rx="3" fill="{col}"/>')
            s.append(f'<text class="small" x="{cx+dx+bw/2:.1f}" y="{y0-bh-8:.1f}" text-anchor="middle" style="fill:{col};font-weight:600">{lab}</text>')
        s.append(f'<text class="tick" x="{cx:.1f}" y="464" text-anchor="middle">{name}</text>')
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    s.append(f'<rect x="110" y="496" width="17" height="17" rx="3" fill="{ORANGE}"/>')
    s.append(f'<text class="small" x="136" y="510">File-based: the model reasons at ingest and over a longer read path</text>')
    s.append(f'<rect x="110" y="524" width="17" height="17" rx="3" fill="{BLUE}"/>')
    s.append(f'<text class="small" x="136" y="538">Structured: zero ingest LLM spend, verified (plus ~0.8k embedder tokens/question, a different currency)</text>')
    s.append('</svg>'); return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"locomo_accuracy_{t}.svg"),"w").write(acc(t,c))
        open(os.path.join(OUT,f"locomo_token_cost_{t}.svg"),"w").write(cost(t,c))
        print("wrote",t)
