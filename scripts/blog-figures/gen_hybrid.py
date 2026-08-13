#!/usr/bin/env python3
"""Figure: the hybrid (place core + temporal layer + associative graph, anchor-expand-fuse recall)."""
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
      f'<defs>{mk("hb",BLUE)}{mk("ho",ORANGE)}{mk("hm",c["mut"])}</defs><style>'
      f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
      f'.title {{ font-size: 31px; font-weight: 700; fill: {c["title"]}; }}'
      f'.subtitle {{ font-size: 19px; fill: {c["body"]}; }}'
      f'.lab {{ fill: {c["title"]}; font-weight: 600; }}'
      f'.small {{ font-size: 16.5px; fill: {c["body"]}; }}'
      f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}'
      f'.mut {{ fill: {c["mut"]}; }}</style>')
def fig(t,c):
    W,H=1100,650; lm=55; ay=104; AW=990; AH=496
    s=[head(W,H,t,c)]
    s.append(f'<text class="title" x="{lm}" y="44">The hybrid: place plus time</text>')
    s.append(f'<text class="subtitle" x="{lm}" y="72">Raw dated facts filed by place; validity windows borrowed from the time lineage; recall runs anchor, expand, fuse.</text>')
    s.append(f'<rect x="{lm}" y="{ay}" width="{AW}" height="{AH}" rx="10" fill="{c["panel"]}" stroke="{c["ln"]}" stroke-width="1.2"/>')
    # rooms
    RW,RH=300,110; ry=222; rxs=[85,400,715]
    # association arc between room A and room C (learned link + expand step)
    ax_,cx_=rxs[0]+RW/2, rxs[2]+RW/2
    s.append(f'<path d="M {ax_+60},{ry} Q {(ax_+cx_)/2},128 {cx_-64},{ry-4}" fill="none" stroke="{ORANGE}" stroke-width="2.4" stroke-dasharray="7 6" marker-end="url(#ho_{t})"/>')
    s.append(f'<text class="small" x="{(ax_+cx_)/2}" y="{ry-88}" text-anchor="middle" style="fill:{ORANGE};font-weight:600">2 &#183; Expand along a learned association</text>')
    s.append(f'<text class="tiny" x="{(ax_+cx_)/2}" y="{ry-70}" text-anchor="middle">Places that co-occur in retrievals beyond chance get linked</text>')
    rooms=[("Room: Project",BLUE,"Anchor hit"),("Room: Health",None,None),("Room: Travel",ORANGE,"Never ranked, still reached")]
    for (rn,hl,note),rx in zip(rooms,rxs):
        stroke=hl if hl else c["ln"]
        s.append(f'<rect x="{rx}" y="{ry}" width="{RW}" height="{RH}" rx="8" fill="{c["page"]}" stroke="{stroke}" stroke-width="{1.9 if hl else 1.3}"/>')
        s.append(f'<text class="tiny" x="{rx+18}" y="{ry+24}" style="font-weight:600">{rn}</text>')
        if note:
            ny=ry+24 if len(note)<12 else ry+96
            s.append(f'<text class="tiny" x="{rx+RW-16}" y="{ny}" text-anchor="end" style="fill:{hl}">{note}</text>')
    # dated chips: rooms A and C (place core, blue)
    for rx in (rxs[0],rxs[2]):
        for k,dt in enumerate(("Fact &#183; Mar 2023","Fact &#183; Jul 2023")):
            cxp=rx+16+k*136
            s.append(f'<rect x="{cxp}" y="{ry+44}" width="132" height="26" rx="13" fill="{BLUE}" opacity="0.16"/>')
            s.append(f'<rect x="{cxp}" y="{ry+44}" width="132" height="26" rx="13" fill="none" stroke="{BLUE}" stroke-width="1.4"/>')
            s.append(f'<text class="tiny" x="{cxp+66}" y="{ry+61}" text-anchor="middle" style="fill:{c["body"]}">{dt}</text>')
    # room B: temporal layer, one current fact + one superseded fact (green)
    bx=rxs[1]
    s.append(f'<rect x="{bx+20}" y="{ry+36}" width="260" height="26" rx="13" fill="none" stroke="{GREEN}" stroke-width="1.7"/>')
    s.append(f'<text class="tiny" x="{bx+150}" y="{ry+53}" text-anchor="middle" style="fill:{c["body"]}">Works at Acme &#183; Aug 2023 &#8594;</text>')
    s.append(f'<g opacity="0.55"><rect x="{bx+20}" y="{ry+72}" width="260" height="26" rx="13" fill="none" stroke="{GREEN}" stroke-width="1.5" stroke-dasharray="6 5"/>')
    s.append(f'<text class="tiny" x="{bx+150}" y="{ry+89}" text-anchor="middle" style="fill:{c["body"]}">Works at Beta &#183; 2022 &#8594; Aug 2023</text></g>')
    s.append(f'<text class="tiny" x="{bx+RW/2}" y="{ry+RH+22}" text-anchor="middle" style="fill:{GREEN}">A new fact closes the old fact&#8217;s window</text>')
    # recall flow: query -> anchor -> rooms -> fuse
    qx,qy,qw,qh=85,478,140,46
    s.append(f'<rect x="{qx}" y="{qy}" width="{qw}" height="{qh}" rx="8" fill="{c["page"]}" stroke="{BLUE}" stroke-width="1.7"/>')
    s.append(f'<text class="small" x="{qx+qw/2}" y="{qy+28}" text-anchor="middle" style="fill:{BLUE};font-weight:600">Query</text>')
    s.append(f'<line x1="{qx+82}" y1="{qy}" x2="{rxs[0]+120}" y2="{ry+RH+6}" stroke="{BLUE}" stroke-width="2.2" marker-end="url(#hb_{t})"/>')
    s.append(f'<text class="small" x="{qx+152}" y="{qy-44}" style="fill:{BLUE};font-weight:600">1 &#183; Anchor</text>')
    s.append(f'<text class="tiny" x="{qx+152}" y="{qy-27}">Ranked hybrid search</text>')
    fx,fy,fw,fh=430,478,360,54
    s.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="8" fill="{c["page"]}" stroke="{c["mut"]}" stroke-width="1.5"/>')
    s.append(f'<text class="small" x="{fx+fw/2}" y="{fy+22}" text-anchor="middle" style="fill:{c["title"]};font-weight:600">3 &#183; Fuse, capped</text>')
    s.append(f'<text class="tiny" x="{fx+fw/2}" y="{fy+40}" text-anchor="middle">The graph augments recall, never swamps it</text>')
    s.append(f'<line x1="{rxs[0]+225}" y1="{ry+RH+4}" x2="{fx+62}" y2="{fy-4}" stroke="{c["mut"]}" stroke-width="1.8" marker-end="url(#hm_{t})"/>')
    s.append(f'<line x1="{rxs[2]+100}" y1="{ry+RH+4}" x2="{fx+fw-62}" y2="{fy-4}" stroke="{c["mut"]}" stroke-width="1.8" marker-end="url(#hm_{t})"/>')
    s.append(f'<text class="small" x="{lm+AW/2}" y="{ay+AH-18}" text-anchor="middle" style="fill:{ORANGE}">Embedder-cheap writes &#183; Dated, supersedable facts &#183; The graph adds recall, never subtracts it</text>')
    s.append('</svg>')
    return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,f"hybrid_{t}.svg"),"w").write(fig(t,c))
        print("wrote",t)
