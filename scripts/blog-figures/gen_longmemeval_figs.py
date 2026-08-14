#!/usr/bin/env python3
"""Figures: LongMemEval accuracy by category, token cost, and write path (same engine as the LoCoMo pair)."""
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
      f'.tick {{ font-size: 15px; fill: {c["mut"]}; }}'
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
    s.append(f'<text class="title" x="70" y="46">Accuracy by question type, LongMemEval-S</text>')
    s.append(f'<text class="subtitle" x="70" y="74">Held-out set, same model, same judge; only the memory layer differs. Structured wins every category but one.</text>')
    grid(s,c,x0,x1,y0,y1,100,20,lambda v:f"{v}%")
    cats=[("Temporal",80,41),("Multi-session",61,33),("Knowledge-upd.",83,53),("Single-user",92,67),
          ("Single-asst.",57,27),("Preference",61,33),("Abstention",78,89)]
    gw=(x1-x0)/len(cats)
    for i,(name,pv,mv) in enumerate(cats):
        cx=x0+gw*(i+0.5); bw=40
        for dx,v,col in ((-bw-3,pv,BLUE),(3,mv,ORANGE)):
            bh=(y0-y1)*v/100
            s.append(f'<rect x="{cx+dx:.1f}" y="{y0-bh:.1f}" width="{bw}" height="{bh:.1f}" rx="3" fill="{col}"/>')
            s.append(f'<text class="small" x="{cx+dx+bw/2:.1f}" y="{y0-bh-8:.1f}" text-anchor="middle" style="fill:{col};font-weight:600">{v}</text>')
        s.append(f'<text class="tick" x="{cx:.1f}" y="474" text-anchor="middle">{name}</text>')
        if mv>pv:
            s.append(f'<text class="small" x="{cx:.1f}" y="{y0-(y0-y1)*mv/100-34:.1f}" text-anchor="middle" style="fill:{ORANGE};font-weight:600">File-based wins</text>')
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    s.append(f'<rect x="100" y="506" width="17" height="17" rx="3" fill="{BLUE}"/>')
    s.append(f'<text class="small" x="126" y="520">Structured (73.6% overall)</text>')
    s.append(f'<rect x="470" y="506" width="17" height="17" rx="3" fill="{ORANGE}"/>')
    s.append(f'<text class="small" x="496" y="520">File-based (44.9% overall)</text>')
    s.append(f'<text class="small" x="1030" y="520" text-anchor="end" style="fill:{c["mut"]}">No-memory floor: 9.8%</text>')
    s.append('</svg>'); return "".join(s)
def cost(t,c):
    W,H=1100,560; x0,x1,y0,y1=110,1030,440,130
    s=[head(W,H,c)]
    s.append(f'<text class="title" x="70" y="46">The cost of an answer, LongMemEval-S</text>')
    s.append(f'<text class="subtitle" x="70" y="74">Model tokens (prompt+completion), ingest amortized per question. The write path dominates.</text>')
    grid(s,c,x0,x1,y0,y1,700,100,lambda v:f"{v}k")
    groups=[("Reasoning tokens per question",287,19),("Reasoning tokens per correct answer",665,27)]
    gw=(x1-x0)/2
    for i,(name,mv,pv) in enumerate(groups):
        cx=x0+gw*(i+0.5); bw=64
        for dx,v,col in ((-bw-8,mv,ORANGE),(8,pv,BLUE)):
            bh=(y0-y1)*v/700
            s.append(f'<rect x="{cx+dx:.1f}" y="{y0-bh:.1f}" width="{bw}" height="{bh:.1f}" rx="3" fill="{col}"/>')
            s.append(f'<text class="small" x="{cx+dx+bw/2:.1f}" y="{y0-bh-8:.1f}" text-anchor="middle" style="fill:{col};font-weight:600">{v}k</text>')
        s.append(f'<text class="tick" x="{cx:.1f}" y="464" text-anchor="middle">{name}</text>')
    s.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}"/>')
    s.append(f'<rect x="110" y="496" width="17" height="17" rx="3" fill="{ORANGE}"/>')
    s.append(f'<text class="small" x="136" y="510">File-based: the model reasons on every write</text>')
    s.append(f'<rect x="110" y="524" width="17" height="17" rx="3" fill="{BLUE}"/>')
    s.append(f'<text class="small" x="136" y="538">Structured: no model on the write path (plus ~108k embedder tokens/question, a different currency)</text>')
    s.append('</svg>'); return "".join(s)
def write_path(t,c):
    W,H=1100,520; bx=340
    s=[head(W,H,c)]
    s.append(f'<text class="title" x="70" y="46">The write path is where they diverge, LongMemEval-S</text>')
    s.append(f'<text class="subtitle" x="70" y="74">Ingesting one ~50-session history. File-based spends a reasoning call per session; structured just embeds.</text>')
    s.append(f'<text class="small" x="70" y="166" style="fill:{ORANGE};font-weight:600">File-based</text>')
    s.append(f'<rect x="{bx}" y="140" width="540" height="36" rx="7" fill="{ORANGE}"/>')
    # one divider per curation call; the bar is 50 sessions wide, drawn every other session
    for i in range(1,25):
        s.append(f'<line x1="{bx+i*21.6}" y1="140" x2="{bx+i*21.6}" y2="176" stroke="#ffffff" stroke-width="1.4" opacity="0.55"/>')
    s.append(f'<text class="small" x="{bx+556}" y="163">~35 min, ~246k tokens</text>')
    s.append(f'<text class="tiny" x="{bx}" y="198" style="fill:{c["mut"]}">Each division is one LLM curation call: read the index, decide what to keep, rewrite a line.</text>')
    s.append(f'<text class="small" x="70" y="246" style="fill:{BLUE};font-weight:600">Structured</text>')
    s.append(f'<rect x="{bx}" y="220" width="128" height="36" rx="7" fill="{BLUE}"/>')
    s.append(f'<text class="small" x="{bx+144}" y="243">~5 minutes, embeddings only</text>')
    s.append(f'<text class="small" x="{bx}" y="320" style="fill:{c["mut"]}">The structured bar has no divisions: every write is a vector write, no model reasons,</text>')
    s.append(f'<text class="small" x="{bx}" y="344" style="fill:{c["mut"]}">so the same history ingests roughly 7&#215; faster.</text>')
    s.append(f'<text class="small" x="70" y="404" style="fill:{c["mut"]}">Read paths differ too: file-based greps and reads files over several rounds; structured issues one ranked query.</text>')
    s.append('</svg>'); return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"accuracy_by_category_{t}.svg"),"w").write(acc(t,c))
        open(os.path.join(OUT,f"token_cost_{t}.svg"),"w").write(cost(t,c))
        open(os.path.join(OUT,f"write_path_{t}.svg"),"w").write(write_path(t,c))
        print("wrote",t)
