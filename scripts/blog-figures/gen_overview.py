#!/usr/bin/env python3
"""Figure: overview — where agent memory lives (store-based vs experience-based)."""
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
      f'<defs>{mk("ovm",c["mut"])}{mk("ovg",GREEN)}</defs><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.lab {{ fill: {c["title"]}; font-weight: 600; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}'
      f'.mut {{ fill: {c["mut"]}; }}</style>')
def fig(t,c):
    W,H=1100,560; AW,AH=480,396; gap=30; lm=(W-2*AW-gap)//2; ay=104
    ax,bx=lm,lm+AW+gap
    s=[head(W,H,t,c)]
    s.append(f'<text class="title" x="{lm}" y="44">Where agent memory lives</text>')
    s.append(f'<text class="subtitle" x="{lm}" y="72">Beside the model as a store, or inside the model as trained behavior. Both keep data; they differ in who learns.</text>')
    for px in (ax,bx):
        s.append(f'<rect x="{px}" y="{ay}" width="{AW}" height="{AH}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    # ---- panel A: store-based ----
    s.append(f'<text class="lab" x="{ax+24}" y="{ay+36}">Store-based</text>')
    s.append(f'<text class="small mut" x="{ax+24}" y="{ay+58}">The model stays frozen; the store gets smarter.</text>')
    mx,my,mw,mh=ax+30,ay+140,150,84
    s.append(f'<rect x="{mx}" y="{my}" width="{mw}" height="{mh}" rx="8" fill="{c["page"]}" stroke="{c["ln"]}" stroke-width="1.5"/>')
    s.append(f'<text class="small" x="{mx+mw/2}" y="{my+38}" text-anchor="middle" style="fill:{c["title"]};font-weight:600">Model</text>')
    s.append(f'<text class="tiny" x="{mx+mw/2}" y="{my+58}" text-anchor="middle">Frozen</text>')
    stx,sty,stw,sth=ax+280,ay+96,170,178
    s.append(f'<rect x="{stx}" y="{sty}" width="{stw}" height="{sth}" rx="8" fill="{c["page"]}" stroke="{c["ln"]}" stroke-width="1.5"/>')
    s.append(f'<text class="small" x="{stx+stw/2}" y="{sty+24}" text-anchor="middle" style="fill:{c["title"]};font-weight:600">Store</text>')
    for i,w in enumerate((92,108,80)):
        s.append(f'<rect x="{stx+18}" y="{sty+40+i*13}" width="{w}" height="7" rx="3.5" fill="{ORANGE}" opacity="0.6"/>')
    s.append(f'<text class="tiny" x="{stx+18}" y="{sty+94}" style="fill:{ORANGE}">Files</text>')
    for j in range(2):
        for i in range(5):
            s.append(f'<circle cx="{stx+24+i*26}" cy="{sty+112+j*20}" r="6" fill="{BLUE}" opacity="0.75"/>')
    s.append(f'<text class="tiny" x="{stx+18}" y="{sty+160}" style="fill:{BLUE}">Structured</text>')
    s.append(f'<line x1="{mx+mw}" y1="{my+18}" x2="{stx-6}" y2="{my+18}" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#ovm_{t})"/>')
    s.append(f'<text class="tiny" x="{(mx+mw+stx)/2}" y="{my+8}" text-anchor="middle" style="font-weight:600">Write</text>')
    s.append(f'<line x1="{stx}" y1="{my+62}" x2="{mx+mw+6}" y2="{my+62}" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#ovm_{t})"/>')
    s.append(f'<text class="tiny" x="{(mx+mw+stx)/2}" y="{my+82}" text-anchor="middle" style="font-weight:600">Read</text>')
    s.append(f'<text class="tiny" x="{ax+AW/2}" y="{ay+AH-64}" text-anchor="middle">Write: the model curates, or an embedder files</text>')
    s.append(f'<text class="tiny" x="{ax+AW/2}" y="{ay+AH-45}" text-anchor="middle">Read: grep, or ranked recall</text>')
    s.append(f'<text class="small" x="{ax+AW/2}" y="{ay+AH-20}" text-anchor="middle">Bolts onto any model &#183; Paid at write and read time</text>')
    # ---- panel B: experience-based ----
    s.append(f'<text class="lab" x="{bx+24}" y="{ay+36}">Experience-based</text>')
    s.append(f'<text class="small mut" x="{bx+24}" y="{ay+58}">The bank stays simple; the model learns to use it.</text>')
    px,py2,pw,ph=bx+30,ay+140,170,84
    s.append(f'<rect x="{px-10}" y="{py2-26}" width="{pw+20}" height="{ph+38}" rx="10" fill="none" stroke="{GREEN}" stroke-width="1.8" stroke-dasharray="7 6"/>')
    s.append(f'<text class="tiny" x="{px+pw/2}" y="{py2-8}" text-anchor="middle" style="fill:{GREEN};font-weight:600">Trained (RL)</text>')
    s.append(f'<rect x="{px}" y="{py2}" width="{pw}" height="{ph}" rx="8" fill="{c["page"]}" stroke="{GREEN}" stroke-width="1.7"/>')
    s.append(f'<text class="small" x="{px+pw/2}" y="{py2+34}" text-anchor="middle" style="fill:{c["title"]};font-weight:600">Actor</text>')
    s.append(f'<text class="tiny" x="{px+pw/2}" y="{py2+52}" text-anchor="middle">Retrieve &#183; critique</text>')
    s.append(f'<text class="tiny" x="{px+pw/2}" y="{py2+68}" text-anchor="middle">Rewrite &#183; act</text>')
    ex,ey,ew,eh=bx+300,ay+96,150,178
    s.append(f'<rect x="{ex}" y="{ey}" width="{ew}" height="{eh}" rx="8" fill="{c["page"]}" stroke="{GREEN}" stroke-width="1.5"/>')
    s.append(f'<text class="small" x="{ex+ew/2}" y="{ey+24}" text-anchor="middle" style="fill:{c["title"]};font-weight:600">Episode bank</text>')
    for j in range(3):
        ys=[ey+56+j*38,ey+46+j*38,ey+60+j*38,ey+48+j*38]
        pts=" ".join(f"{ex+22+i*38},{y}" for i,y in enumerate(ys))
        op=0.95 if j==1 else 0.4
        s.append(f'<polyline points="{pts}" fill="none" stroke="{GREEN}" stroke-width="2" opacity="{op}"/>')
        for i,y in enumerate(ys):
            s.append(f'<circle cx="{ex+22+i*38}" cy="{y}" r="3.5" fill="{GREEN}" opacity="{op}"/>')
    s.append(f'<line x1="{px+pw+16}" y1="{py2+18}" x2="{ex-6}" y2="{py2+18}" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#ovm_{t})"/>')
    s.append(f'<text class="tiny" x="{(px+pw+16+ex)/2}" y="{py2+2}" text-anchor="middle" style="font-weight:600">Write</text>')
    s.append(f'<line x1="{ex}" y1="{py2+62}" x2="{px+pw+22}" y2="{py2+62}" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#ovm_{t})"/>')
    s.append(f'<text class="tiny" x="{(px+pw+16+ex)/2}" y="{py2+84}" text-anchor="middle" style="font-weight:600">Retrieve</text>')
    s.append(f'<text class="small" x="{bx+AW/2}" y="{ay+AH-20}" text-anchor="middle">One model, inseparable &#183; Paid in training compute</text>')
    s.append('</svg>')
    return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"overview_{t}.svg"),"w").write(fig(t,c))
        print("wrote",t)
