#!/usr/bin/env python3
"""Figure: two lineages inside the structured shape (place vs entity-and-time). v3 polished."""
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
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
      f'<rect width="100%" height="100%" fill="{c["bg"]}" rx="8"/>'
      f'<defs><marker id="ar2_{t}" markerWidth="14" markerHeight="12" refX="11" refY="5" orient="auto" markerUnits="userSpaceOnUse">'
      f'<path d="M0,0 L12,5 L0,10 Z" fill="{c["mut"]}"/></marker></defs><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.lab {{ fill: {c["title"]}; font-weight: 600; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}'
      f'.mut {{ fill: {c["mut"]}; }}</style>')
def fig(t,c):
    W,H=1100,660; AW,AH=480,510; gap=30; lm=(W-2*AW-gap)//2; ay=104
    ax=lm; bx=lm+AW+gap
    s=[head(W,H,t,c)]
    s.append(f'<text class="title" x="{lm}" y="44">Two lineages inside the structured store</text>')
    s.append(f'<text class="subtitle" x="{lm}" y="72">Both mine facts automatically. One organizes them by place, the other by entity and time.</text>')
    s.append(f'<rect x="{ax}" y="{ay}" width="{AW}" height="{AH}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    s.append(f'<text class="lab" x="{ax+24}" y="{ay+36}" style="fill:{BLUE}">Place-organized</text>')
    s.append(f'<text class="small mut" x="{ax+24}" y="{ay+58}">A spatial hierarchy with a layered load policy.</text>')
    ty=ay+78
    s.append(f'<rect x="{ax+24}" y="{ty}" width="{AW-48}" height="52" rx="8" fill="{c["page"]}" stroke="{BLUE}" stroke-width="1.6"/>')
    s.append(f'<text class="small" x="{ax+40}" y="{ty+22}" style="fill:{BLUE};font-weight:600">Always loaded</text>')
    s.append(f'<text class="tiny" x="{ax+40}" y="{ty+40}">Identity + the most salient facts</text>')
    for i in range(3):
        s.append(f'<rect x="{ax+AW-168+i*44}" y="{ty+21}" width="32" height="10" rx="5" fill="{BLUE}" opacity="{0.85-0.25*i}"/>')
    RW=AW-190
    rooms=[("Room: Project",4),("Room: Health",3),("Room: Travel",3)]
    ry=ty+76; rh=90; rgap=20; ycs=[]
    for ri,(rn,nch) in enumerate(rooms):
        y=ry+ri*(rh+rgap); ycs.append(y+rh/2)
        hl=ri==0
        s.append(f'<rect x="{ax+24}" y="{y}" width="{RW}" height="{rh}" rx="8" fill="{c["page"]}" stroke="{BLUE if hl else c["ln"]}" stroke-width="{1.8 if hl else 1.3}"/>')
        s.append(f'<text class="tiny" x="{ax+40}" y="{y+24}" style="font-weight:600">{rn}</text>')
        for k in range(nch):
            s.append(f'<rect x="{ax+40+k*62}" y="{y+42}" width="50" height="22" rx="11" fill="{BLUE}" opacity="{0.5 if hl else 0.32}"/>')
    room_r=ax+24+RW
    s.append(f'<text class="tiny" x="{room_r+22}" y="{ycs[0]-16}" style="font-weight:600">Scoped recall</text>')
    s.append(f'<line x1="{room_r+118}" y1="{ycs[0]-2}" x2="{room_r+8}" y2="{ycs[0]-2}" stroke="{c["mut"]}" stroke-width="2" marker-end="url(#ar2_{t})"/>')
    busx=room_r+118
    s.append(f'<line x1="{busx}" y1="{ycs[0]+18}" x2="{busx}" y2="{ycs[2]+18}" stroke="{c["mut"]}" stroke-width="1.4" stroke-dasharray="4 4"/>')
    for yc in ycs:
        s.append(f'<line x1="{busx}" y1="{yc+18}" x2="{room_r+8}" y2="{yc+18}" stroke="{c["mut"]}" stroke-width="1.4" stroke-dasharray="4 4" marker-end="url(#ar2_{t})"/>')
    bmid=(ycs[1]+ycs[2])/2+18
    s.append(f'<text class="tiny" x="{busx-10}" y="{bmid-4}" text-anchor="end" style="font-weight:600">Broad search</text>')
    s.append(f'<text class="tiny" x="{busx-10}" y="{bmid+12}" text-anchor="end">(fallback)</text>')
    s.append(f'<text class="small" x="{ax+AW/2}" y="{ay+AH-20}" text-anchor="middle" style="fill:{BLUE}">Cheap writes &#183; No entity merge &#183; Freshness by ranking</text>')
    s.append(f'<rect x="{bx}" y="{ay}" width="{AW}" height="{AH}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    s.append(f'<text class="lab" x="{bx+24}" y="{ay+36}" style="fill:{GREEN}">Entity-and-time</text>')
    s.append(f'<text class="small mut" x="{bx+24}" y="{ay+58}">A knowledge graph keyed to who, linked to when.</text>')
    FW,FH=170,44; fx=bx+AW-24-FW
    fys=[ay+96, ay+166, ay+236, ay+306]; hx,hy=bx+120,ay+214
    labels=[("Fact A","2023-03 &#8594;",False),("Fact B","2023-05 &#8594;",False),
            ("Fact C","2023-08 &#8594;",False),("Fact D","2022-01 &#8594; 2023-04",True)]
    for (fn,dr,closed),fy in zip(labels,fys):
        dash=' stroke-dasharray="6 5" opacity="0.5"' if closed else ''
        s.append(f'<line x1="{hx}" y1="{hy}" x2="{fx}" y2="{fy+FH/2}" stroke="{GREEN}" stroke-width="2.4"{dash}/>')
    s.append(f'<circle cx="{hx}" cy="{hy}" r="36" fill="{GREEN}" opacity="0.14"/>')
    s.append(f'<circle cx="{hx}" cy="{hy}" r="27" fill="{GREEN}"/>')
    s.append(f'<text x="{hx}" y="{hy+6}" text-anchor="middle" style="font-size:16px;fill:#ffffff;font-weight:700">E</text>')
    s.append(f'<text class="tiny" x="{hx}" y="{hy-52}" text-anchor="middle" style="font-weight:600">One resolved entity</text>')
    for (fn,dr,closed),fy in zip(labels,fys):
        op='0.55' if closed else '1'
        s.append(f'<g opacity="{op}"><rect x="{fx}" y="{fy}" width="{FW}" height="{FH}" rx="7" fill="{c["page"]}" stroke="{GREEN}" stroke-width="1.6"/>')
        s.append(f'<text class="tiny" x="{fx+12}" y="{fy+16}" style="font-weight:600">{fn}</text>')
        s.append(f'<text class="tiny" x="{fx+12}" y="{fy+31}">{dr}</text></g>')
    s.append(f'<text class="tiny" x="{fx+FW}" y="{fys[3]+FH+20}" text-anchor="end" style="fill:{ORANGE}">Superseded: window closed</text>')
    tly=ay+424
    s.append(f'<line x1="{bx+40}" y1="{tly}" x2="{bx+AW-40}" y2="{tly}" stroke="{c["ln"]}" stroke-width="1.5"/>')
    s.append(f'<rect x="{bx+60}" y="{tly-17}" width="145" height="10" rx="5" fill="{GREEN}" opacity="0.45"/>')
    s.append(f'<rect x="{bx+205}" y="{tly-17}" width="195" height="10" rx="5" fill="{GREEN}"/>')
    s.append(f'<line x1="{bx+205}" y1="{tly-26}" x2="{bx+205}" y2="{tly+7}" stroke="{ORANGE}" stroke-width="2.5"/>')
    s.append(f'<text class="tiny" x="{bx+60}" y="{tly+24}">Old fact</text>')
    s.append(f'<text class="tiny" x="{bx+209}" y="{tly+24}">New fact closes the old window</text>')
    s.append(f'<text class="small" x="{bx+AW/2}" y="{ay+AH-20}" text-anchor="middle" style="fill:{GREEN}">Entity aggregation &#183; Validity windows &#183; LLM at ingest</text>')
    s.append('</svg>')
    return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"two_lineages_{t}.svg"),"w").write(fig(t,c))
        print("wrote",t)
