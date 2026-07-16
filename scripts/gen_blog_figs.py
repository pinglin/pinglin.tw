#!/usr/bin/env python3
"""Generate light + dark figure variants for the optimizing-apple-silicon-gpu-for-transformer-inference post.

Palettes are the CVD-validated pairs from the dataviz reference palette:
light  prefill #eb6834 · decode #2a78d6 · cache #1baf7a  on #fcfcfb
dark   prefill #d95926 · decode #3987e5 · cache #199e70  on #1a1a2e
The site toggles <html data-theme="night">, so the post embeds both variants
with Tailwind `dark:hidden` / `hidden dark:block`.

Outputs into public/blog/optimizing-apple-silicon-gpu-for-transformer-inference/:
  gpu_timeline_{light,dark}.svg   chat_decode_rate_{light,dark}.svg
  kv_reread_tax_{light,dark}.svg  ttft_itl_tradeoff_{light,dark}.svg
  header.png (dark) + header_light.png

The header/OG hero is composed as SVG and rasterized at 2x with headless
Chrome (2000x1050 px from a 1000x525 canvas).
"""
import math
import os
import subprocess
import tempfile

OUT = os.path.expanduser("~/Workspace/pinglin.tw/public/blog/optimizing-apple-silicon-gpu-for-transformer-inference")
os.makedirs(OUT, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

THEMES = {
    "dark": dict(
        BG="#1a1a2e", INK="#ffffff", INK2="#c9c9d4", MUTED="#8f8f9c",
        GRID="#3a3a4e", AXIS="#55556a",
        PREFILL="#d95926", DECODE="#3987e5", CACHE="#199e70",
        WASH="rgba(217,89,38,0.16)", ON_DECODE="#ffffff", ON_PREFILL="#0b0b0b",
        HALO="#1a1a2e",
    ),
    "light": dict(
        BG="#fcfcfb", INK="#0b0b0b", INK2="#52514e", MUTED="#898781",
        GRID="#e1e0d9", AXIS="#c3c2b7",
        PREFILL="#eb6834", DECODE="#2a78d6", CACHE="#1baf7a",
        WASH="rgba(235,104,52,0.10)", ON_DECODE="#ffffff", ON_PREFILL="#0b0b0b",
        HALO="#fcfcfb",
    ),
}


def style(P):
    return f"""<style>
text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: {P['INK2']}; font-size: 16px; }}
.title {{ font-size: 30px; font-weight: 700; fill: {P['INK']}; }}
.subtitle {{ font-size: 17px; fill: {P['INK2']}; }}
.lab {{ fill: {P['INK']}; font-weight: 600; }}
.tick {{ font-size: 14.5px; fill: {P['MUTED']}; }}
.onmark {{ font-weight: 600; font-size: 15px; }}
.axis {{ stroke: {P['AXIS']}; stroke-width: 1.2; }}
.grid {{ stroke: {P['GRID']}; stroke-width: 1; }}
.leader {{ stroke: {P['MUTED']}; stroke-width: 1; }}
</style>"""


def svg_open(P, w, h, rx=8):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">\n<rect width="100%" height="100%" fill="{P["BG"]}" rx="{rx}"/>\n{style(P)}\n')


def legend(x, y, items):
    out, cx = [], x
    for color, label in items:
        out.append(f'<rect x="{cx}" y="{y - 11}" width="13" height="13" rx="3" fill="{color}"/>')
        out.append(f'<text x="{cx + 20}" y="{y}">{label}</text>')
        cx += 20 + 9.2 * len(label) + 44
    return "\n".join(out)


# ---------------------------------------------------------------- figure 1
def fig_timeline(P, path):
    W, H = 1100, 470
    L, R = 60, 1056
    T_SEC = 12.0
    pps = (R - L) / T_SEC

    def x(t):
        return L + t * pps

    s = [svg_open(P, W, H)]
    s.append(f'<text class="title" x="{L}" y="42">What the GPU is doing, second by second</text>')
    s.append(f'<text class="subtitle" x="{L}" y="68">The same 12-second window in two regimes. '
             f'A decode step is ~15 ms, so a decoding GPU reads as a continuous band.</text>')
    s.append(legend(L, 100, [(P["PREFILL"], "prefill chunk (compute-bound)"),
                             (P["DECODE"], "decode steps (bandwidth-bound)"),
                             (P["CACHE"], "prefix-cache (APC) restore")]))

    ya = 150
    s.append(f'<text class="lab" x="{L}" y="{ya - 10}">A · Chats only, warm prefix cache</text>')
    s.append(f'<text class="lab" x="{R}" y="{ya - 10}" text-anchor="end" style="fill:{P["DECODE"]}">chat decodes at 60–70 tok/s</text>')
    for t0, t1, c in [(0.0, 3.0, P["DECODE"]), (3.0, 3.7, P["CACHE"]), (3.7, 12.0, P["DECODE"])]:
        s.append(f'<rect x="{x(t0) + 1:.1f}" y="{ya}" width="{(t1 - t0) * pps - 2:.1f}" height="40" rx="4" fill="{c}"/>')
    s.append(f'<text class="onmark" x="{x(7.85):.0f}" y="{ya + 25}" text-anchor="middle" style="fill:{P["ON_DECODE"]}">'
             f'decoding: every in-flight chat advances each step</text>')
    apc_mid = x(3.35)
    s.append(f'<line class="leader" x1="{apc_mid:.0f}" y1="{ya + 42}" x2="{apc_mid:.0f}" y2="{ya + 56}"/>')
    s.append(f'<text x="{apc_mid:.0f}" y="{ya + 72}" text-anchor="middle">'
             f'new turn arrives → APC restores the ~23k-token prefix in &lt;1 s</text>')

    yb = 290
    s.append(f'<text class="lab" x="{L}" y="{yb - 10}">B · Cold 60k-token benchmark prefill in flight</text>')
    s.append(f'<text class="lab" x="{R}" y="{yb - 10}" text-anchor="end" style="fill:{P["PREFILL"]}">concurrent chat: 0.67 tok/s measured</text>')
    chunk, gap = 1.55, 0.14
    t = 0.0
    while t + chunk <= T_SEC + 0.01:
        s.append(f'<rect x="{x(t):.1f}" y="{yb}" width="{chunk * pps - 2:.1f}" height="40" rx="4" fill="{P["PREFILL"]}"/>')
        if t + chunk + gap <= T_SEC:
            gx = x(t + chunk) - 2 + gap * pps / 2
            s.append(f'<rect x="{gx - 2:.1f}" y="{yb}" width="4" height="40" rx="1.5" fill="{P["DECODE"]}"/>')
        t += chunk + gap
    s.append(f'<text class="onmark" x="{x(0.775):.0f}" y="{yb + 20}" text-anchor="middle" style="fill:{P["ON_PREFILL"]}" font-size="13">2,048-token'
             f'<tspan x="{x(0.775):.0f}" dy="16">chunk</tspan></text>')
    sliver = x(1.55) - 2 + gap * pps / 2
    s.append(f'<line class="leader" x1="{sliver:.0f}" y1="{yb + 42}" x2="{sliver:.0f}" y2="{yb + 56}"/>')
    s.append(f'<text x="{sliver + 6:.0f}" y="{yb + 72}">one decode step granted between chunks (drawn wider than its true ~15 ms);</text>')
    s.append(f'<text x="{sliver + 6:.0f}" y="{yb + 92}">the whole batch lives on these scraps</text>')

    yax = 408
    s.append(f'<line class="axis" x1="{L}" y1="{yax}" x2="{R}" y2="{yax}"/>')
    for sec in range(0, 13, 2):
        s.append(f'<line class="axis" x1="{x(sec):.0f}" y1="{yax}" x2="{x(sec):.0f}" y2="{yax + 5}"/>')
        s.append(f'<text class="tick" x="{x(sec):.0f}" y="{yax + 22}" text-anchor="middle">{sec} s</text>')
    s.append("</svg>\n")
    with open(path, "w") as f:
        f.write("\n".join(s))


# ---------------------------------------------------------------- figure 2
def fig_rate(P, path):
    W, H = 1100, 540
    L, R, T, B = 74, 1056, 110, 480
    TMAX, VMAX = 60.0, 80.0

    def x(t):
        return L + (t / TMAX) * (R - L)

    def y(v):
        return B - (v / VMAX) * (B - T)

    def rate(t):
        if 8 <= t < 52:
            return 0.67
        return 65 + 1.3 * math.sin(t * 1.7) + 0.8 * math.sin(t * 0.6)

    s = [svg_open(P, W, H)]
    s.append(f'<text class="title" x="{L}" y="42">What your chat experiences</text>')
    s.append(f'<text class="subtitle" x="{L}" y="68">Decode rate of one warm chat stream while a 60k-token '
             f'benchmark prefill arrives and completes.</text>')

    for v in range(0, 81, 20):
        cls = "axis" if v == 0 else "grid"
        s.append(f'<line class="{cls}" x1="{L}" y1="{y(v):.1f}" x2="{R}" y2="{y(v):.1f}"/>')
        s.append(f'<text class="tick" x="{L - 10}" y="{y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    s.append(f'<text class="tick" x="{L + 8}" y="{T + 16}">tok/s</text>')

    s.append(f'<rect x="{x(8):.1f}" y="{T}" width="{x(52) - x(8):.1f}" height="{B - T}" fill="{P["WASH"]}"/>')
    s.append(f'<text class="lab" x="{x(30):.0f}" y="{T + 20}" text-anchor="middle" style="fill:{P["PREFILL"]}">'
             f'benchmark prefill in flight (60k-token document, ~44 s)</text>')

    s.append(f'<line x1="{L}" y1="{y(60):.1f}" x2="{R}" y2="{y(60):.1f}" stroke="{P["MUTED"]}" '
             f'stroke-width="1" stroke-dasharray="5 4"/>')
    s.append(f'<text class="tick" x="{R}" y="{y(60) + 16:.1f}" text-anchor="end">60 tok/s target</text>')

    pts = []
    t = 0.0
    while t <= TMAX + 1e-9:
        for edge in (15.0, 40.0):
            if abs(t - edge) < 1e-9:
                pts.append((x(edge - 0.01), y(rate(edge - 0.01))))
        pts.append((x(t), y(rate(t))))
        t += 0.5
    d = "M" + " L".join(f"{px:.1f} {py:.1f}" for px, py in pts)
    s.append(f'<path d="{d}" fill="none" stroke="{P["DECODE"]}" stroke-width="2.5" stroke-linejoin="round"/>')

    s.append(f'<circle cx="{x(30):.0f}" cy="{y(0.67):.1f}" r="5" fill="{P["DECODE"]}" stroke="{P["HALO"]}" stroke-width="2"/>')
    s.append(f'<text class="lab" x="{x(30):.0f}" y="{y(0.67) - 14:.0f}" text-anchor="middle">0.67 tok/s measured</text>')

    for sec in range(0, 61, 10):
        s.append(f'<line class="axis" x1="{x(sec):.0f}" y1="{B}" x2="{x(sec):.0f}" y2="{B + 5}"/>')
        s.append(f'<text class="tick" x="{x(sec):.0f}" y="{B + 22}" text-anchor="middle">{sec} s</text>')
    s.append("</svg>\n")
    with open(path, "w") as f:
        f.write("\n".join(s))


# ---------------------------------------------------------------- figure 3
def fig_kv(P, path):
    W, H = 1100, 400
    L, R = 390, 1000
    GMAX = 6.0

    def x(gb):
        return L + (gb / GMAX) * (R - L)

    s = [svg_open(P, W, H)]
    s.append(f'<text class="title" x="60" y="42">The second-order tax: resident context fattens every step</text>')
    s.append(f'<text class="subtitle" x="60" y="68">Bytes read per decode step. A step re-reads every in-flight '
             f"sequence's KV cache (~20 KB/token) on top of the weights.</text>")
    s.append(legend(60, 100, [(P["DECODE"], "active weights re-read"), (P["PREFILL"], "resident KV re-read")]))

    for g in range(0, 7):
        s.append(f'<line class="grid" x1="{x(g):.0f}" y1="130" x2="{x(g):.0f}" y2="320"/>')

    rows = [
        ("Chats alone, short contexts", 150, [(3.0, P["DECODE"], "weights ~3.0 GB", P["ON_DECODE"])], "≈ 65 tok/s", P["DECODE"]),
        ("+ one 130k-token benchmark sequence", 240,
         [(3.0, P["DECODE"], "weights ~3.0 GB", P["ON_DECODE"]), (2.6, P["PREFILL"], "KV ~2.6 GB", P["ON_PREFILL"])],
         "≈ ½ the rate", P["PREFILL"]),
    ]
    for label, yy, segs, res, rescolor in rows:
        s.append(f'<text class="lab" x="60" y="{yy + 24}" font-size="15">{label}</text>')
        gb0 = 0.0
        for gb, color, seg_label, ink in segs:
            x0 = x(gb0) + (2 if gb0 > 0 else 0)
            wpx = x(gb0 + gb) - x0
            s.append(f'<rect x="{x0:.1f}" y="{yy}" width="{wpx:.1f}" height="38" rx="4" fill="{color}"/>')
            s.append(f'<text class="onmark" x="{x0 + wpx / 2:.0f}" y="{yy + 24}" text-anchor="middle" style="fill:{ink}">{seg_label}</text>')
            gb0 += gb
        s.append(f'<text class="lab" x="{x(gb0) + 12:.0f}" y="{yy + 24}" style="fill:{rescolor}">{res}</text>')

    yax = 320
    s.append(f'<line class="axis" x1="{L}" y1="{yax}" x2="{R}" y2="{yax}"/>')
    for g in range(0, 7):
        s.append(f'<line class="axis" x1="{x(g):.0f}" y1="{yax}" x2="{x(g):.0f}" y2="{yax + 5}"/>')
        anchor = "end" if g == 6 else "middle"
        lab = f"{g} GB" if g == 6 else str(g)
        s.append(f'<text class="tick" x="{x(g):.0f}" y="{yax + 22}" text-anchor="{anchor}">{lab}</text>')
    s.append("</svg>\n")
    with open(path, "w") as f:
        f.write("\n".join(s))


# ---------------------------------------------------------------- figure 4
def fig_tradeoff(P, path):
    """TTFT-vs-ITL trade-off as a function of prefill chunk size, log-log.
    Modeled from the post's measured rates: 2,048-token chunks take ~1.5 s at
    document scale (ITL curve), a 60k-token prompt averages ~1,365 tok/s
    (TTFT floor), decode steps ~15 ms, per-chunk overhead ~50 ms."""
    W, H = 1100, 600
    L, R, T, B = 74, 1056, 150, 490

    def x(c):
        return L + (math.log2(c) - 7) / 6 * (R - L)

    def y(v):
        return B - (math.log10(v) + 1) / 3 * (B - T)

    def itl(c):
        return c / 1365.33 + 0.015

    def ttft(c):
        return 44.0 + (60000.0 / c) * 0.065

    s = [svg_open(P, W, H)]
    s.append(f'<text class="title" x="{L}" y="42">One knob, two latencies</text>')
    s.append(f'<text class="subtitle" x="{L}" y="68">Chunk size trades a prompt\'s TTFT against every concurrent stream\'s ITL.</text>')
    s.append(f'<text class="subtitle" x="{L}" y="88">Modeled from this box\'s measured rates: ~1.5 s per 2,048-token chunk at document scale, '
             f'~15 ms decode steps,</text>')
    s.append(f'<text class="subtitle" x="{L}" y="108">~50 ms per-chunk overhead, ~1,365 tok/s average prefill.</text>')

    for v, lab in [(0.1, "0.1 s"), (1, "1 s"), (10, "10 s"), (100, "100 s")]:
        cls = "axis" if v == 0.1 else "grid"
        s.append(f'<line class="{cls}" x1="{L}" y1="{y(v):.1f}" x2="{R}" y2="{y(v):.1f}"/>')
        s.append(f'<text class="tick" x="{L - 10}" y="{y(v) + 4:.1f}" text-anchor="end">{lab}</text>')

    s.append(f'<line x1="{L}" y1="{y(44):.1f}" x2="{R}" y2="{y(44):.1f}" stroke="{P["MUTED"]}" stroke-width="1" stroke-dasharray="2 4"/>')
    s.append(f'<text class="tick" x="{R}" y="{y(44) + 16:.1f}" text-anchor="end">prefill floor: 60,000 tokens ÷ ~1,365 tok/s ≈ 44 s</text>')
    s.append(f'<rect x="{x(512):.1f}" y="{T}" width="{x(1024) - x(512):.1f}" height="{B - T}" fill="{P["CACHE"]}" fill-opacity="0.13"/>')
    s.append(f'<text class="onmark" x="{x(724):.0f}" y="{T + 18}" text-anchor="middle" style="fill:{P["CACHE"]}">sweet spot for this traffic</text>')

    s.append(f'<line x1="{x(2048):.1f}" y1="{T}" x2="{x(2048):.1f}" y2="{B}" stroke="{P["MUTED"]}" stroke-width="1" stroke-dasharray="5 4"/>')
    s.append(f'<text x="{x(2048) + 8:.0f}" y="{T + 18}">this box today: 2,048-token chunks</text>')

    for f, color in [(ttft, P["PREFILL"]), (itl, P["DECODE"])]:
        cs = [128 * 2 ** (i / 2) for i in range(13)]
        d = "M" + " L".join(f"{x(c):.1f} {y(f(c)):.1f}" for c in cs)
        s.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>')

    s.append(f'<text class="lab" x="{x(135):.0f}" y="{y(85):.0f}" style="fill:{P["PREFILL"]}">TTFT: the 60k-token prompt itself</text>')
    s.append(f'<text class="lab" x="{x(700):.0f}" y="{y(0.28):.0f}" style="fill:{P["DECODE"]}">ITL: a concurrent interactive stream, during the prefill</text>')
    for f, color in [(ttft, P["PREFILL"]), (itl, P["DECODE"])]:
        s.append(f'<circle cx="{x(2048):.1f}" cy="{y(f(2048)):.1f}" r="4.5" fill="{color}" stroke="{P["HALO"]}" stroke-width="2"/>')

    for c in [128, 256, 512, 1024, 2048, 4096, 8192]:
        s.append(f'<line class="axis" x1="{x(c):.0f}" y1="{B}" x2="{x(c):.0f}" y2="{B + 5}"/>')
        s.append(f'<text class="tick" x="{x(c):.0f}" y="{B + 22}" text-anchor="middle">{c:,}</text>')
    s.append(f'<text x="{(L + R) / 2:.0f}" y="{B + 46}" text-anchor="middle">prefill chunk size (tokens per chunk)</text>')
    s.append("</svg>\n")
    with open(path, "w") as f:
        f.write("\n".join(s))


# ------------------------------------------------------------ header / OG
def fig_header(P, path):
    """The hero card. Rasterized to PNG (2000x1050) — no rounded corners so
    it also works as an OG image."""
    # The shared stylesheet pins `text` to 14px/INK2, so every override here
    # must be an inline style= — font-size presentation attributes lose too.
    s = [svg_open(P, 1000, 525, rx=0)]
    s.append(
        f'<text x="64" y="120" style="font-size:80px;font-weight:800;fill:{P["DECODE"]}">65'
        f'<tspan style="font-size:40px;font-weight:600"> tok/s</tspan>'
        f'<tspan style="font-size:60px;font-weight:400;fill:{P["INK2"]}"> &#x2192; </tspan>'
        f'<tspan style="fill:{P["PREFILL"]}">0.67</tspan>'
        f'<tspan style="font-size:40px;font-weight:600;fill:{P["PREFILL"]}"> tok/s</tspan></text>')
    s.append(f'<text x="64" y="168" style="font-size:24px;fill:{P["INK"]}">'
             f'What one cold benchmark prefill does to every chat on a shared GPU</text>')

    s.append(f'<text x="64" y="220" style="font-size:17px;font-weight:600;fill:{P["INK"]}">Chats only, warm prefix cache</text>')
    s.append(f'<rect x="65.0" y="232" width="216.0" height="52" rx="5" fill="{P["DECODE"]}"/>')
    s.append(f'<rect x="283.0" y="232" width="48.9" height="52" rx="5" fill="{P["CACHE"]}"/>')
    s.append(f'<rect x="333.9" y="232" width="601.1" height="52" rx="5" fill="{P["DECODE"]}"/>')
    s.append(f'<text x="634" y="264" style="font-size:17px;font-weight:600;fill:{P["ON_DECODE"]}" text-anchor="middle">Decoding</text>')
    s.append(f'<line x1="307" y1="288" x2="307" y2="300" stroke="{P["MUTED"]}" stroke-width="1"/>')
    s.append(f'<text x="307" y="316" style="font-size:15px;fill:{P["INK2"]}" text-anchor="middle">'
             f'Prefix-cache restore: a new turn skips re-reading its prefix</text>')

    s.append(f'<text x="64" y="360" style="font-size:17px;font-weight:600;fill:{P["INK"]}">One cold 60k-token prefill in flight</text>')
    x, chunk_w, sliver_gap = 64.0, 110.6, 3.1
    for i in range(7):
        s.append(f'<rect x="{x:.1f}" y="372" width="{chunk_w}" height="52" rx="5" fill="{P["PREFILL"]}"/>')
        s.append(f'<rect x="{x + chunk_w + sliver_gap:.1f}" y="372" width="4" height="52" rx="2" fill="{P["DECODE"]}"/>')
        x += chunk_w + 12.2
    s.append(f'<text x="120" y="404" style="font-size:15px;font-weight:600;fill:{P["ON_PREFILL"]}" text-anchor="middle">Prefill chunk</text>')
    s.append(f'<text x="64" y="464" style="font-size:17px;fill:{P["INK2"]}">The thin blue slivers are the only decode steps anyone gets</text>')
    s.append("</svg>\n")
    with open(path, "w") as f:
        f.write("\n".join(s))


def rasterize(svg_path, png_path, w=1000, h=525, scale=2):
    # --virtual-time-budget forces Chrome to exit after rendering; without it
    # headless Chrome on macOS sometimes writes the screenshot and then hangs.
    # The timeout+existence check covers the case where it hangs anyway.
    with tempfile.TemporaryDirectory() as ud:
        try:
            subprocess.run(
                [CHROME, "--headless", f"--screenshot={png_path}",
                 f"--window-size={w},{h}", f"--force-device-scale-factor={scale}",
                 "--hide-scrollbars", "--disable-gpu", "--virtual-time-budget=2000",
                 f"--user-data-dir={ud}", f"file://{svg_path}"],
                check=True, capture_output=True, timeout=45)
        except subprocess.TimeoutExpired:
            if not os.path.exists(png_path):
                raise


with tempfile.TemporaryDirectory() as tmp:
    for theme, P in THEMES.items():
        fig_timeline(P, f"{OUT}/gpu_timeline_{theme}.svg")
        fig_rate(P, f"{OUT}/chat_decode_rate_{theme}.svg")
        fig_kv(P, f"{OUT}/kv_reread_tax_{theme}.svg")
        fig_tradeoff(P, f"{OUT}/ttft_itl_tradeoff_{theme}.svg")
        svg = f"{tmp}/header_{theme}.svg"
        fig_header(P, svg)
        png = f"{OUT}/header.png" if theme == "dark" else f"{OUT}/header_{theme}.png"
        rasterize(svg, png)
print("wrote:", sorted(os.listdir(OUT)))
