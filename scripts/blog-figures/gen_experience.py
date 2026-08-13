#!/usr/bin/env python3
"""Figure: the experience architecture (MemHarness) — bank + trained five-stage policy."""
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
      f'<defs>{mk("exm",c["mut"])}{mk("exg",GREEN)}</defs><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}'
      f'.mut {{ fill: {c["mut"]}; }}</style>')
def fig(t,c):
    W,H=1100,640; lm=55; ay=104; AW=990; AH=496
    s=[head(W,H,t,c)]
    s.append(f'<text class="title" x="{lm}" y="44">The experience architecture</text>')
    s.append(f'<text class="subtitle" x="{lm}" y="72">The bank looks like a structured store; the use of it is a policy trained end-to-end.</text>')
    s.append(f'<rect x="{lm}" y="{ay}" width="{AW}" height="{AH}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    # training bracket over trained stages
    stages=[("Observe","Current state",False),("Retrieve","Top-k + sources",True),
            ("Critique","Does it apply here?",True),("Reconstruct","Rewrite into guidance",True),
            ("Act","In the environment",True)]
    SW,SH,sy,sgap=168,66,236,32
    sxs=[66+i*(SW+sgap) for i in range(5)]
    bl,br=sxs[1]-12,sxs[4]+SW+12
    s.append(f'<path d="M {br-60},{sy-12} L {br-60},{sy-56} L {bl+60},{sy-56} L {bl+60},{sy-16}" fill="none" stroke="{GREEN}" stroke-width="2" stroke-dasharray="7 6" marker-end="url(#exg_{t})"/>')
    s.append(f'<text class="small" x="{(bl+br)/2}" y="{sy-84}" text-anchor="middle" style="fill:{GREEN};font-weight:600">Trained end-to-end with reinforcement learning (GRPO)</text>')
    s.append(f'<text class="tiny" x="{(bl+br)/2}" y="{sy-66}" text-anchor="middle">Reward flows back through every stage; format rewards keep retrieval and reconstruction alive</text>')
    for (name,sub,trained),sx in zip(stages,sxs):
        col=GREEN if trained else c["ln"]
        s.append(f'<rect x="{sx}" y="{sy}" width="{SW}" height="{SH}" rx="8" fill="{c["page"]}" stroke="{col}" stroke-width="{1.8 if trained else 1.4}"/>')
        s.append(f'<text class="small" x="{sx+SW/2}" y="{sy+27}" text-anchor="middle" style="fill:{c["title"]};font-weight:600">{name}</text>')
        s.append(f'<text class="tiny" x="{sx+SW/2}" y="{sy+47}" text-anchor="middle">{sub}</text>')
    for a,b in zip(sxs,sxs[1:]):
        s.append(f'<line x1="{a+SW+3}" y1="{sy+SH/2}" x2="{b-6}" y2="{sy+SH/2}" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#exm_{t})"/>')
    # reject fallback: critique -> act, dashed under the row
    cx_,ax_=sxs[2]+SW/2,sxs[4]+SW/2
    s.append(f'<path d="M {cx_},{sy+SH+4} Q {(cx_+ax_)/2},{sy+SH+52} {ax_-14},{sy+SH+8}" fill="none" stroke="{c["mut"]}" stroke-width="1.6" stroke-dasharray="5 5" marker-end="url(#exm_{t})"/>')
    s.append(f'<text class="tiny" x="{(cx_+ax_)/2}" y="{sy+SH+52}" text-anchor="middle">Reject: fall back to self-reasoning</text>')
    # episode bank
    ex,ey,ew,eh=470,436,360,120
    s.append(f'<rect x="{ex}" y="{ey}" width="{ew}" height="{eh}" rx="10" fill="{c["page"]}" stroke="{GREEN}" stroke-width="1.8"/>')
    s.append(f'<text class="small" x="{ex+24}" y="{ey+30}" style="fill:{c["title"]};font-weight:600">Episode bank</text>')
    s.append(f'<text class="tiny" x="{ex+24}" y="{ey+50}">Summarize &#183; deduplicate &#183; prune by utility</text>')
    for j in range(2):
        ys=[ey+78+j*22,ey+70+j*22,ey+82+j*22,ey+72+j*22,ey+80+j*22]
        pts=" ".join(f"{ex+108+i*36},{y}" for i,y in enumerate(ys))
        op=0.95 if j==0 else 0.4
        s.append(f'<polyline points="{pts}" fill="none" stroke="{GREEN}" stroke-width="2" opacity="{op}"/>')
        for i,y in enumerate(ys):
            s.append(f'<circle cx="{ex+108+i*36}" cy="{y}" r="3.5" fill="{GREEN}" opacity="{op}"/>')
    # bank <-> stage arrows
    rx_=sxs[1]+SW/2
    s.append(f'<path d="M {ex},{ey+eh/2} L {rx_},{ey+eh/2} L {rx_},{sy+SH+8}" fill="none" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#exm_{t})"/>')
    s.append(f'<text class="tiny" x="{ex-10}" y="{ey+eh/2+26}" text-anchor="end">Experiences out</text>')
    s.append(f'<path d="M {sxs[4]+SW/2},{sy+SH+4} L {sxs[4]+SW/2},{ey+eh/2} L {ex+ew+6},{ey+eh/2}" fill="none" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#exm_{t})"/>')
    s.append(f'<text class="tiny" x="{ex+ew+10}" y="{ey+eh/2+26}" text-anchor="start">Episode written back</text>')
    s.append(f'<text class="small" x="{lm+AW/2}" y="{ay+AH-16}" text-anchor="middle" style="fill:{GREEN}">The store is inspectable; the memory behavior lives in the weights</text>')
    s.append('</svg>')
    return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"experience_{t}.svg"),"w").write(fig(t,c))
        print("wrote",t)
