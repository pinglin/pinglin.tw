#!/usr/bin/env python3
"""Hero: three shapes of agent memory (Files / Vectors + Graph / Experience). 1200x630 OG."""
import os
OUT=os.path.expanduser("~/Workspace/pinglin.tw/public/blog/the-shapes-of-agent-memory")
TH={
 "light": dict(bg="#fcfcfb", title="#0b0b0b", body="#52514e", panel="#f3f2ec", file="header_light.svg"),
 "dark":  dict(bg="#1a1a2e", title="#ffffff", body="#c9c9d4", panel="#24243a", file="header.svg"),
}
BLUE="#2a78d6"; GREEN="#1baf7a"; ORANGE="#eb6834"
def fig(c):
    W,H=1200,630; PW,PH,py=330,360,200; xs=[64,435,806]
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       f'<rect width="100%" height="100%" fill="{c["bg"]}"/>'
       '<style>text{font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;}</style>'
       f'<text x="64" y="106" style="font-size:44px;font-weight:700;fill:{c["title"]}">The shapes of agent memory</text>'
       f'<text x="66" y="148" style="font-size:20px;fill:{c["body"]}">Files, structured stores, and experience</text>']
    for px,col in zip(xs,(ORANGE,BLUE,GREEN)):
        s.append(f'<rect x="{px}" y="{py}" width="{PW}" height="{PH}" rx="14" fill="{c["panel"]}" stroke="{col}" stroke-width="2.5"/>')
    # panel 1: Files (index lines, one emphasized)
    px=xs[0]
    for i,w in enumerate((176,196,158,188,214,200,164,182,192,170)):
        op=0.95 if i==4 else 0.42
        s.append(f'<rect x="{px+40}" y="{py+34+i*27}" width="{w}" height="13" rx="6" fill="{ORANGE}" opacity="{op}"/>')
    s.append(f'<text x="{px+PW/2}" y="{py+PH-26}" text-anchor="middle" style="font-size:22px;font-weight:600;fill:{ORANGE}">Files</text>')
    # panel 2: Vectors + Graph (5x6 dot grid, green nodes linked)
    px=xs[1]
    cols=[px+45+i*60 for i in range(5)]; rows=[py+38+j*48 for j in range(6)]
    greens={(2,0),(0,1),(4,1),(2,2),(1,3),(4,3),(3,4),(1,5)}
    order=sorted(greens,key=lambda g:(g[1],g[0]))
    for (a,b),(d,e) in zip(order,order[1:]):
        s.append(f'<line x1="{cols[a]}" y1="{rows[b]}" x2="{cols[d]}" y2="{rows[e]}" stroke="{GREEN}" stroke-width="1.6" opacity="0.55"/>')
    for j in range(6):
        for i in range(5):
            col=GREEN if (i,j) in greens else BLUE
            s.append(f'<circle cx="{cols[i]}" cy="{rows[j]}" r="10" fill="{col}" opacity="0.8"/>')
    s.append(f'<text x="{px+PW/2}" y="{py+PH-26}" text-anchor="middle" style="font-size:22px;font-weight:600;fill:{BLUE}">Vectors + Graph</text>')
    # panel 3: Experience (episode trajectories, one successful run emphasized)
    px=xs[2]
    txs=[px+40,px+102,px+165,px+227,px+290]
    trails=[((255,235,260,240,256),0.35),((320,298,325,300,318),0.95),((385,365,390,368,384),0.35),((450,430,455,432,448),0.35)]
    for ys,op in trails:
        pts=" ".join(f"{x},{py+y-160}" for x,y in zip(txs,ys))
        bold=op>0.5
        s.append(f'<polyline points="{pts}" fill="none" stroke="{GREEN}" stroke-width="{3 if bold else 2.4}" opacity="{op}"/>')
        for x,y in zip(txs,ys):
            s.append(f'<circle cx="{x}" cy="{py+y-160}" r="{6.5 if bold else 5.5}" fill="{GREEN}" opacity="{op}"/>')
        if bold:
            s.append(f'<circle cx="{txs[-1]}" cy="{py+ys[-1]-160}" r="9" fill="{GREEN}"/>')
            s.append(f'<circle cx="{txs[-1]}" cy="{py+ys[-1]-160}" r="16" fill="none" stroke="{GREEN}" stroke-width="2.5" opacity="0.9"/>')
    s.append(f'<text x="{px+PW/2}" y="{py+PH-26}" text-anchor="middle" style="font-size:22px;font-weight:600;fill:{GREEN}">Experience</text>')
    s.append('</svg>')
    return "".join(s)
if __name__=="__main__":
    for t,c in TH.items():
        open(os.path.join(OUT,c["file"]),"w").write(fig(c))
        print("wrote",c["file"])
