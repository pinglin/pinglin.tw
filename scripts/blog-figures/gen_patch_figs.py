#!/usr/bin/env python3
"""Hero and figures for 'The Patch You Do Not Wait For', light and dark SVGs.

Writes header.svg / header_light.svg (the hero), race_{light,dark}.svg (Figure 1)
and loop_{light,dark}.svg (Figure 2) into the post's public folder:

    python3 scripts/blog-figures/gen_patch_figs.py            # writes into public/
    python3 scripts/blog-figures/gen_patch_figs.py <out_dir>  # writes elsewhere

Not generated here:
- header_light.png, the 1200x630 social-card twin of the light hero. It is the
  light hero rendered with @resvg/resvg-js at width 1200 (the renderer the site's
  section cards use), then compressed losslessly with oxipng.
- mirror.webp (Figure 3), a supplied illustration, cropped below its banner.
"""
import math
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'public', 'blog', 'the-patch-you-do-not-wait-for')
os.makedirs(OUT, exist_ok=True)

PAL = {
    'light': dict(bg='#fcfcfb', card='#f3f2ec', border='#d8d7cd', text='#52514e', head='#0b0b0b', mut='#898781',
                  line='#b9b7ad'),
    'dark': dict(bg='#1a1a2e', card='#24243a', border='#3a3a56', text='#c9c9d4', head='#ffffff', mut='#8f8f9c',
                 line='#5a5a76'),
}
ORANGE, BLUE, GREEN, RED = '#eb6834', '#2a78d6', '#1baf7a', '#d64545'


def head(w, h, p, mode):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect width="100%" height="100%" fill="{p["bg"]}" rx="8"/>'
        '<defs>'
        + ''.join(
            f'<marker id="{n}_{mode}" markerWidth="14" markerHeight="12" refX="11" refY="5" orient="auto" '
            f'markerUnits="userSpaceOnUse"><path d="M0,0 L12,5 L0,10 Z" fill="{c}"/></marker>'
            for n, c in (('ar', p['line']), ('arg', GREEN), ('aro', ORANGE), ('arr', RED), ('arb', BLUE))
        )
        + '</defs>'
        f'<style>text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; fill: {p["text"]}; font-size: 18px; }}'
        f'.title {{ font-size: 30px; font-weight: 700; fill: {p["head"]}; }}'
        f'.subtitle {{ font-size: 18.5px; fill: {p["text"]}; }}'
        f'.lab {{ fill: {p["head"]}; font-weight: 600; }}'
        f'.small {{ font-size: 16.5px; }}'
        f'.tiny {{ font-size: 15px; fill: {p["mut"]}; }}'
        f'.mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 15px; }}'
        '</style>'
    )


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def t(x, y, s, cls='', anchor='start', style=''):
    c = f' class="{cls}"' if cls else ''
    st = f' style="{style}"' if style else ''
    return f'<text{c} x="{x}" y="{y}" text-anchor="{anchor}"{st}>{esc(s)}</text>'


# --- hero: the race and the loop, one lap on the clock -----------------------------------------
def hero(mode):
    p = PAL[mode]
    W, H = 1200, 630
    s = head(W, H, p, mode).replace(' rx="8"/>', '/>', 1)
    # the circuit: a stadium, run clockwise from the start line at its left apex
    cx, cy, L, R = 670, 330, 400, 175
    x0, x1 = cx - L / 2, cx + L / 2
    ri, ro = R - 13, R + 13  # inner lane: the attacker; outer lane: our fix

    def pt(ccx, ang, r):
        a = math.radians(ang)
        return ccx + r * math.cos(a), cy + r * math.sin(a)

    def lap(r, end_ang):
        ex, ey = pt(x0, end_ang, r)
        return (f'M {x0 - r} {cy} A {r} {r} 0 0 1 {x0} {cy - r} L {x1} {cy - r} A {r} {r} 0 0 1 {x1} {cy + r} '
                f'L {x0} {cy + r} A {r} {r} 0 0 1 {ex:.1f} {ey:.1f}')

    track = (f'M {x0} {cy - R} L {x1} {cy - R} A {R} {R} 0 0 1 {x1} {cy + R} L {x0} {cy + R} '
             f'A {R} {R} 0 0 1 {x0} {cy - R} Z')
    # the band needs more lift from a dark background than the card tone gives it
    band, edge, divider_op = (p['card'], p['border'], 0.6) if mode == 'light' else ('#2e2e4a', '#60607f', 0.9)
    s += f'<path d="{track}" fill="none" stroke="{edge}" stroke-width="60"/>'
    s += f'<path d="{track}" fill="none" stroke="{band}" stroke-width="54"/>'
    s += (f'<path d="{track}" fill="none" stroke="{p["line"]}" stroke-width="1.5" stroke-dasharray="10 12" '
          f'stroke-opacity="{divider_op}"/>')
    # the patch: a diff sheet against the start line; its red and green lines run out onto the two lanes
    sx, sy, sw = 92, 265, 150
    s += t(sx + sw / 2, 248, 'The clock starts for both', 'tiny', 'middle')
    s += f'<rect x="{sx}" y="{sy}" width="{sw}" height="130" rx="12" fill="{p["card"]}" stroke="{p["border"]}" stroke-width="1.5"/>'
    # the diff itself stays neutral: red and green belong to the two runners, not to removed and added lines
    for i, w in enumerate((70, 100, 88, 96, 60, 82)):
        y = sy + 24 + i * 16
        s += f'<rect x="{sx + 18}" y="{y}" width="8" height="8" rx="2" fill="{p["mut"]}" fill-opacity="0.8"/>'
        s += f'<rect x="{sx + 34}" y="{y + 1}" width="{w}" height="6" rx="3" fill="{p["mut"]}" fill-opacity="0.45"/>'
    s += t(sx + sw / 2, 424, 'Patch published', 'lab', 'middle', 'font-size:19px')
    # start and finish: a checkered line across the band at the left apex
    ax = x0 - R
    for i in range(8):
        for j in range(2):
            col = p['head'] if (i + j) % 2 == 0 else p['bg']
            s += f'<rect x="{ax - 28 + i * 7}" y="{cy - 7 + j * 7}" width="7" height="7" fill="{col}"/>'
    # the two trajectories: the attacker races ahead on the inside and stops short; our fix crosses
    s += (f'<path d="{lap(ri, 165)}" fill="none" stroke="{RED}" stroke-width="3.5" stroke-linecap="round" '
          f'stroke-opacity="0.85"/>')
    s += (f'<path d="{lap(ro, 150)}" fill="none" stroke="{GREEN}" stroke-width="3.5" stroke-linecap="round" '
          f'stroke-opacity="0.85"/>')
    # the attacker's story, told on the inside of the track
    marks = [
        (pt(x0, 226, ri), 'Reads the diff', (386, 240), 'start'),
        ((560, cy - ri), 'Writes the exploit', (560, 206), 'middle'),
        (pt(x1, 45, ri), 'Scans for the unpatched', (915, 468), 'end'),
    ]
    for (mx, my), label, (lx, ly), anchor in marks:
        s += f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="6" fill="{RED}" stroke="{p["bg"]}" stroke-width="2"/>'
        s += t(lx, ly, label, 'tiny', anchor, f'fill:{RED}')
    ex, ey = pt(x0, 165, ri)
    s += f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="12" fill="{RED}" stroke="{p["bg"]}" stroke-width="2.5"/>'
    s += (f'<path d="M {ex - 5:.1f} {ey - 5:.1f} L {ex + 5:.1f} {ey + 5:.1f} M {ex + 5:.1f} {ey - 5:.1f} L {ex - 5:.1f} {ey + 5:.1f}" '
          f'stroke="{p["bg"]}" stroke-width="2.5" stroke-linecap="round"/>')
    s += t(340, 392, 'Window closes in a day', 'tiny', 'start', f'fill:{RED};font-weight:600')
    # the four stations of the loop, clockwise from the start, on the outside
    # one colour for all four: red and green already mean the two runners
    stations = [
        (640, cy - R, BLUE, '1', 'Scan', 'Hourly advisory watch', 'above'),
        (880, cy - R, BLUE, '2', 'Patch', 'One PR per finding', 'above'),
        (x1 + R, cy, BLUE, '3', 'Gate', 'CI, then merge', 'right'),
        (600, cy + R, BLUE, '4', 'Release', 'Clock set by severity', 'below'),
    ]
    for x, y, col, n, name, sub, side in stations:
        s += f'<circle cx="{x}" cy="{y}" r="17" fill="{col}" stroke="{p["bg"]}" stroke-width="2.5"/>'
        s += t(x, y + 6, n, 'lab', 'middle', f'fill:{p["bg"]};font-size:17px')
        if side == 'above':
            s += t(x, y - 43, name, 'lab', 'middle', 'font-size:22px')
            s += t(x, y - 67, sub, 'tiny', 'middle')
        elif side == 'below':
            s += t(x, y + 54, name, 'lab', 'middle', 'font-size:22px')
            s += t(x, y + 76, sub, 'tiny', 'middle')
        else:
            s += t(x + 34, y - 4, name, 'lab', 'start', 'font-size:22px')
            s += t(x + 34, y + 18, sub, 'tiny', 'start')
    # our fix: past every station, past the stopped exploit, across the line
    gx, gy = pt(x0, 150, ro)
    for ang, rr in ((140, 5), (131, 4), (123, 3)):
        dx, dy = pt(x0, ang, ro)
        s += f'<circle cx="{dx:.1f}" cy="{dy:.1f}" r="{rr}" fill="{GREEN}" fill-opacity="0.5"/>'
    fx, fy = pt(x0, 192, ro)
    s += (f'<path d="M {gx:.1f} {gy:.1f} A {ro} {ro} 0 0 1 {fx:.1f} {fy:.1f}" fill="none" stroke="{GREEN}" '
          f'stroke-width="3" stroke-dasharray="7 6" marker-end="url(#arg_{mode})"/>')
    s += f'<circle cx="{gx:.1f}" cy="{gy:.1f}" r="14" fill="{GREEN}" stroke="{p["bg"]}" stroke-width="2.5"/>'
    # lane names, painted on the track along the top straight
    for y, col, name in ((cy - ri, RED, 'The attacker'), (cy - ro, GREEN, 'Our fix')):
        s += t(760, y + 5, name, 'lab', 'middle',
               f'fill:{col};font-size:13px;paint-order:stroke;stroke:{band};stroke-width:6px;stroke-linejoin:round')
    # the clock in the middle of the lap
    # the needle owns the upper half; the reading sits below the pivot so nothing covers it
    cr = 112
    s += f'<rect x="{cx - 11}" y="{cy - cr - 15}" width="22" height="16" rx="3" fill="{ORANGE}"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{cr}" fill="{p["card"]}" stroke="{ORANGE}" stroke-width="3"/>'
    s += (f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - cr + 18}" stroke="{ORANGE}" stroke-width="3" '
          f'stroke-linecap="round" stroke-opacity="0.7"/>')
    s += f'<circle cx="{cx}" cy="{cy}" r="4" fill="{ORANGE}"/>'
    s += t(cx, cy + 44, '24 h', 'lab', 'middle', 'font-size:44px;font-weight:700')
    s += t(cx, cy + 66, 'One lap: Critical fix', 'small', 'middle', 'font-size:15px')
    s += t(cx, cy + 84, 'In production', 'small', 'middle', 'font-size:15px')
    return s + '</svg>'


# --- figure 1: the race after a fix is published ------------------------------------------------
def race(mode):
    p = PAL[mode]
    W, H = 1100, 600
    s = head(W, H, p, mode)
    s += t(40, 44, 'The race starts when the fix is published', 'title')
    s += t(40, 74, 'A patch is also a map to the bug, and a model reads maps quickly.', 'subtitle')
    x0, x1 = 250, 1050
    # the far end is the Verizon DBIR 2026 median: 43 days to fully remediate a CISA KEV vulnerability
    HAND = 43 * 24
    ticks = [('0', 0), ('6 h', 6), ('1 day', 24), ('3 days', 72), ('1 week', 168), ('2 weeks', 336), ('43 days', HAND)]
    lo = math.log(1 + 0)
    hi = math.log(1 + HAND)

    def X(hrs):
        return x0 + (x1 - x0) * (math.log(1 + hrs) - lo) / (hi - lo)

    axis_y = 470
    s += f'<line x1="{x0}" y1="{axis_y}" x2="{x1}" y2="{axis_y}" stroke="{p["line"]}" stroke-width="1.5"/>'
    for lab, hrs in ticks:
        x = X(hrs)
        s += f'<line x1="{x:.1f}" y1="{axis_y}" x2="{x:.1f}" y2="{axis_y + 7}" stroke="{p["line"]}" stroke-width="1.5"/>'
        s += f'<line x1="{x:.1f}" y1="118" x2="{x:.1f}" y2="{axis_y}" stroke="{p["border"]}" stroke-width="1" stroke-dasharray="3 5"/>'
        s += t(x, axis_y + 28, lab, 'tiny', 'middle')
    s += t(x0, 112, 'Fix published', 'tiny', 'middle', f'fill:{p["head"]};font-weight:600')

    # the window: from the attacker's finish to the hand patch's finish
    wx0, wx1 = X(10), X(HAND)
    s += (f'<rect x="{wx0:.1f}" y="259" width="{wx1 - wx0:.1f}" height="42" rx="6" fill="{RED}" fill-opacity="0.10" '
          f'stroke="{RED}" stroke-opacity="0.5" stroke-dasharray="5 5"/>')
    s += t((wx0 + wx1) / 2 + 60, 244, 'Exposed: the exploit exists, the fix is not running', 'tiny', 'middle',
           f'fill:{RED};font-weight:600')
    rows = [
        (170, 'Attacker with a model', 'Read the diff, write the exploit, scan', 0, 10, RED),
        (280, 'Patching by hand', 'Someone reads the news, files a ticket, waits for a release', 0, HAND, p['mut']),
        (390, 'A40 Labs, a Critical', 'PR in 4 h, staging in 12 h, production in 24 h', 0, 24, GREEN),
    ]
    for y, name, sub, a, b, col in rows:
        s += t(40, y + 6, name, 'lab', 'start', 'font-size:17px')
        bx0, bx1 = X(a), X(b)
        s += f'<rect x="{bx0:.1f}" y="{y - 14}" width="{bx1 - bx0:.1f}" height="28" rx="14" fill="{col}" fill-opacity="0.85"/>'
        s += t(bx0 + 2, y + 44, sub, 'small')
    notes = [
        'Patching by hand: a median of 43 days to fully remediate a CISA KEV vulnerability (Verizon DBIR 2026).',
        'Attacker: an average time-to-exploit of 5 days in 2023, with 12% of n-days exploited within a day (Mandiant).',
        'Log scale. The attacker row shows the fast end of that range; the A40 Labs row is our target for a Critical.',
    ]
    for i, note in enumerate(notes):
        s += t(40, 528 + i * 22, note, 'tiny')
    return s + '</svg>'


# --- figure 2: the loop ------------------------------------------------------------------------
def loop(mode):
    p = PAL[mode]
    W, H = 1100, 530
    s = head(W, H, p, mode)
    s += t(40, 44, 'The CVE loop: scan, patch, gate, release', 'title')
    s += t(40, 74, 'Every step leaves a pull request or a line in the daily digest. Nothing touches production directly.',
           'subtitle')
    cards = [
        ('1  Scan', BLUE, ['Hourly advisory watch', 'Daily sweep with trivy,', 'govulncheck and gitleaks'],
         'Exploited: seen in 1 h'),
        ('2  Patch', GREEN, ['In each repo, on a match', 'Bumps with its own tool', 'Runs the repo’s checks'],
         'One PR per finding'),
        ('3  Gate', GREEN, ['Same-major bump:', 'merges itself on green', 'Major bump: a person'],
         'CI gates every merge'),
        ('4  Release', ORANGE, ['Staging: automatic', 'Production: a person', 'Paged for a Critical'],
         'Critical ≤ 24 h'),
    ]
    cw, gap, y0, ch = 222, 42, 120, 250
    xs = [40 + i * (cw + gap) for i in range(4)]
    for x, (name, col, lines, foot) in zip(xs, cards):
        s += f'<rect x="{x}" y="{y0}" width="{cw}" height="{ch}" rx="12" fill="{p["card"]}" stroke="{p["border"]}" stroke-width="1.2"/>'
        s += f'<rect x="{x}" y="{y0}" width="{cw}" height="6" rx="3" fill="{col}"/>'
        s += t(x + 20, y0 + 44, name, 'lab', 'start', 'font-size:22px')
        for i, ln in enumerate(lines):
            s += t(x + 20, y0 + 88 + i * 30, ln, 'small')
        s += f'<line x1="{x + 20}" y1="{y0 + 196}" x2="{x + cw - 20}" y2="{y0 + 196}" stroke="{p["border"]}"/>'
        s += t(x + 20, y0 + 228, foot, 'small', 'start', f'fill:{col};font-weight:600')
    for i in range(3):
        ax = xs[i] + cw + 4
        s += f'<line x1="{ax}" y1="{y0 + ch / 2}" x2="{ax + gap - 8}" y2="{y0 + ch / 2}" stroke="{p["line"]}" stroke-width="3" marker-end="url(#ar_{mode})"/>'
    # feedback: the next scan reads where the fix is
    fy = y0 + ch + 44
    lx, rx_ = xs[0] + cw / 2, xs[3] + cw / 2
    s += (f'<path d="M {rx_} {y0 + ch + 4} L {rx_} {fy} L {lx} {fy} L {lx} {y0 + ch + 14}" fill="none" '
          f'stroke="{BLUE}" stroke-width="2.5" stroke-dasharray="7 6" marker-end="url(#arb_{mode})"/>')
    s += f'<rect x="{(lx + rx_) / 2 - 245}" y="{fy - 17}" width="490" height="34" rx="17" fill="{p["bg"]}"/>'
    s += t((lx + rx_) / 2, fy + 6, 'Next scan: is the fix on main, in staging, in production?', 'small', 'middle',
           f'fill:{BLUE};font-weight:600')
    s += t(40, 488, 'A fix that cannot be a PR goes in the daily digest, and the owner runs it as one script.', 'tiny')
    s += t(40, 510, 'A finding is silenced only in one ledger, with a reason and an expiry of at most 90 days.', 'tiny')
    return s + '</svg>'

# --- figure 3: the same model, both directions -------------------------------------------------
def mirror(mode):
    p = PAL[mode]
    W, H = 1100, 590
    s = head(W, H, p, mode)
    s += t(40, 44, 'The same model, both directions', 'title')
    s += t(40, 74, 'Both sides start from a diff. The only variable is who reads it first.', 'subtitle')
    cols = [
        (40, RED, 'The attacker’s model', [
            ('Reads the published patch', ['The vendor’s own diff,', 'with the bug circled']),
            ('Writes the exploit', ['Hours of model time where it', 'took a skilled person days']),
            ('Scans for the unpatched', ['Every instance still running', 'the old version']),
        ]),
        (630, GREEN, 'The same model, on our side', [
            ('Reads our pull request', ['The diff before it ships, or the', 'whole repository in a full read']),
            ('Finds what a scanner cannot', ['The known CVEs, and the access-control', 'mistakes we wrote ourselves']),
            ('The fix goes in first', ['Before the diff reaches main,', 'and before a patch note exists']),
        ]),
    ]
    cw, ch, y0, gap = 430, 104, 150, 30
    cx = W / 2
    # the mirror axis, drawn first so the circle sits on it
    s += (f'<line x1="{cx}" y1="112" x2="{cx}" y2="{y0 + 3 * ch + 2 * gap}" stroke="{p["border"]}" '
          f'stroke-width="1.5" stroke-dasharray="6 6"/>')
    for x, col, header, cards in cols:
        mid = x + cw / 2
        s += t(mid, 128, header, 'lab', 'middle', f'font-size:20px;fill:{col}')
        for i, (name, lines) in enumerate(cards):
            y = y0 + i * (ch + gap)
            s += (f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="12" fill="{p["card"]}" '
                  f'stroke="{p["border"]}" stroke-width="1.2"/>')
            s += f'<rect x="{x}" y="{y}" width="{cw}" height="6" rx="3" fill="{col}"/>'
            s += t(x + 20, y + 40, name, 'lab', 'start', 'font-size:20px')
            for j, ln in enumerate(lines):
                s += t(x + 20, y + 66 + j * 22, ln, 'small')
            if i < 2:
                s += (f'<line x1="{mid}" y1="{y + ch + 4}" x2="{mid}" y2="{y + ch + gap - 8}" stroke="{p["line"]}" '
                      f'stroke-width="3" marker-end="url(#ar_{mode})"/>')
    # the shared piece
    cy = y0 + ch + gap + ch / 2
    s += f'<circle cx="{cx}" cy="{cy}" r="60" fill="{p["card"]}" stroke="{BLUE}" stroke-width="3"/>'
    s += t(cx, cy - 4, 'Same', 'lab', 'middle', 'font-size:26px')
    s += t(cx, cy + 26, 'model', 'lab', 'middle', 'font-size:26px')
    s += t(40, 562, 'On a pull request the model reads only the diff; a full read of one repository is about 25 minutes and 119 million tokens.',
           'tiny')
    return s + '</svg>'


for mode in ('light', 'dark'):
    suffix = '_light' if mode == 'light' else ''
    open(f'{OUT}/header{suffix}.svg', 'w').write(hero(mode))
    open(f'{OUT}/race_{mode}.svg', 'w').write(race(mode))
    open(f'{OUT}/loop_{mode}.svg', 'w').write(loop(mode))
print('wrote 6 SVGs to', os.path.normpath(OUT))
