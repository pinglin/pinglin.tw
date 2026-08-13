#!/usr/bin/env python3
"""Figure: the two store architectures (file-based vs structured), boxes sized for the 18/16.5/15px type scale."""
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
      f'<defs>{mk("arc",c["mut"])}</defs><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.lab {{ fill: {c["title"]}; font-weight: 600; font-size: 16.5px; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}'
      f'.mut {{ fill: {c["mut"]}; }}</style>')
def box(s,c,x,y,w,h,stroke,lab,sub=None,sw=1.6):
    s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{c["page"]}" stroke="{stroke}" stroke-width="{sw}"/>')
    if sub:
        s.append(f'<text class="lab" x="{x+w/2}" y="{y+24}" text-anchor="middle">{lab}</text>')
        s.append(f'<text class="tiny" x="{x+w/2}" y="{y+44}" text-anchor="middle">{sub}</text>')
    else:
        s.append(f'<text class="lab" x="{x+w/2}" y="{y+h/2+6}" text-anchor="middle">{lab}</text>')
def varrow(s,c,t,x,y1,y2,lab=None):
    s.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2-5}" stroke="{c["mut"]}" stroke-width="1.8" marker-end="url(#arc_{t})"/>')
    if lab:
        s.append(f'<text class="tiny" x="{x+10}" y="{(y1+y2)/2+5}">{lab}</text>')
def fig(t,c):
    W,H=1100,660; AW,AH=480,506; gap=30; lm=(W-2*AW-gap)//2; ay=104
    ax,bx=lm,lm+AW+gap
    s=[head(W,H,t,c)]
    s.append(f'<text class="title" x="{lm}" y="44">The two store architectures</text>')
    s.append(f'<text class="subtitle" x="{lm}" y="72">Both sit beside a frozen model. They differ in how a fact gets in (write) and how it comes back (read).</text>')
    for px in (ax,bx):
        s.append(f'<rect x="{px}" y="{ay}" width="{AW}" height="{AH}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    # ---- panel A: file-based ----
    cxa=ax+AW/2
    s.append(f'<text class="lab" x="{ax+24}" y="{ay+36}" style="fill:{ORANGE}">File-based memory</text>')
    s.append(f'<text class="small mut" x="{ax+24}" y="{ay+58}">An index plus topic files. The model curates.</text>')
    box(s,c,cxa-100,ay+76,200,44,c["ln"],"New turn")
    varrow(s,c,t,cxa,ay+120,ay+150,"Model decides")
    box(s,c,cxa-125,ay+150,250,56,ORANGE,"Write / edit a file","One line to the index")
    varrow(s,c,t,cxa,ay+206,ay+236)
    box(s,c,cxa-110,ay+236,220,56,ORANGE,"MEMORY.md","Index, ~200 lines")
    tw,tg=92,16; tx0=cxa-(4*tw+3*tg)/2; ty=ay+330
    for i in range(4):
        txi=tx0+i*(tw+tg)
        s.append(f'<line x1="{cxa}" y1="{ay+292}" x2="{txi+tw/2}" y2="{ty-5}" stroke="{c["mut"]}" stroke-width="1.6" marker-end="url(#arc_{t})"/>')
        box(s,c,txi,ty,tw,42,c["ln"],"Topic",sw=1.3)
    s.append(f'<text class="tiny" x="{cxa}" y="{ay+AH-66}" text-anchor="middle">Read: index in context, then grep + read files</text>')
    s.append(f'<text class="small" x="{cxa}" y="{ay+AH-24}" text-anchor="middle" style="fill:{ORANGE}">No embeddings &#183; Literal search &#183; Model-curated</text>')
    # ---- panel B: structured ----
    cxb=bx+AW/2
    s.append(f'<text class="lab" x="{bx+24}" y="{ay+36}" style="fill:{BLUE}">Structured memory</text>')
    s.append(f'<text class="small mut" x="{bx+24}" y="{ay+58}">Atomic units in a vector store, plus a fact graph.</text>')
    box(s,c,cxb-100,ay+76,200,44,c["ln"],"New turn")
    varrow(s,c,t,cxb,ay+120,ay+150,"Auto-extract")
    box(s,c,cxb-135,ay+150,270,56,BLUE,"Mine atomic units","Embed each; no LLM write")
    vx,vw=bx+24,204; fxx,fw2=bx+24+204+14,214
    for tx,txw in ((vx,vw),(fxx,fw2)):
        s.append(f'<line x1="{cxb}" y1="{ay+206}" x2="{tx+txw/2}" y2="{ay+245}" stroke="{c["mut"]}" stroke-width="1.6" marker-end="url(#arc_{t})"/>')
    box(s,c,vx,ay+250,vw,56,BLUE,"Vector store","Dense + sparse")
    box(s,c,fxx,ay+250,fw2,56,GREEN,"Fact graph","Temporal, superseding")
    s.append(f'<line x1="{vx+vw}" y1="{ay+278}" x2="{fxx}" y2="{ay+278}" stroke="{c["mut"]}" stroke-width="1.4" stroke-dasharray="4 3"/>')
    s.append(f'<line x1="{cxb}" y1="{ay+306}" x2="{cxb}" y2="{ay+345}" stroke="{c["mut"]}" stroke-width="1.4" stroke-dasharray="4 3" marker-end="url(#arc_{t})"/>')
    s.append(f'<text class="tiny" x="{cxb+10}" y="{ay+332}">Consolidate (background)</text>')
    box(s,c,cxb-145,ay+350,290,44,BLUE,"Ranked retrieval + preload")
    s.append(f'<text class="tiny" x="{cxb}" y="{ay+AH-66}" text-anchor="middle">Read: hybrid search returns top-k; salient units preloaded</text>')
    s.append(f'<text class="small" x="{cxb}" y="{ay+AH-24}" text-anchor="middle" style="fill:{BLUE}">Embeddings &#183; Ranked recall &#183; Auto-mined</text>')
    s.append('</svg>')
    return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"architecture_{t}.svg"),"w").write(fig(t,c))
        print("wrote",t)
