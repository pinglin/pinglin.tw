#!/usr/bin/env python3
"""Figures for 'The Cluster You Do Not Watch' — one per section, light and dark."""
import os

OUT = os.path.expanduser("~/Workspace/pinglin.tw/public/blog/the-cluster-you-do-not-watch")

TH = {
    "light": dict(bg="#fcfcfb", title="#0b0b0b", body="#52514e", mut="#898781",
                  panel="#f3f2ec", ln="#d8d7cd", page="#ffffff"),
    "dark": dict(bg="#1a1a2e", title="#ffffff", body="#c9c9d4", mut="#8f8f9c",
                 panel="#24243a", ln="#3a3a4e", page="#2e2e46"),
}
BLUE = "#2a78d6"
GREEN = "#1baf7a"
ORANGE = "#eb6834"
FONT = 'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;'
MONO = 'font-family: ui-monospace, SFMono-Regular, Menlo, monospace;'

ARROW = 8594   # ->
CHECK = "&#10003;"
CROSS = "&#10007;"
DOT = "&#183;"
APPROX = "&#8776;"


def head(w, h, t, c):
    mk = "".join(
        f'<marker id="{n}_{t}" markerWidth="14" markerHeight="12" refX="11" refY="5" '
        f'orient="auto" markerUnits="userSpaceOnUse">'
        f'<path d="M0,0 L12,5 L0,10 Z" fill="{col}"/></marker>'
        for n, col in (("ar", c["mut"]), ("arb", BLUE), ("aro", ORANGE), ("arg", GREEN))
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<rect width="100%" height="100%" fill="{c["bg"]}" rx="8"/>'
        f'<defs>{mk}</defs><style>'
        f'text {{ {FONT} fill: {c["body"]}; font-size: 18px; }}'
        f'.title {{ font-size: 30px; font-weight: 700; fill: {c["title"]}; }}'
        f'.subtitle {{ font-size: 18.5px; fill: {c["body"]}; }}'
        f'.lab {{ fill: {c["title"]}; font-weight: 600; }}'
        f'.small {{ font-size: 16.5px; }}'
        f'.tiny {{ font-size: 15px; fill: {c["mut"]}; }}'
        f'.mono {{ {MONO} font-size: 15px; }}'
        f'.mut {{ fill: {c["mut"]}; }}</style>'
    )


def titleblock(x, title, sub, y=44):
    return (f'<text class="title" x="{x}" y="{y}">{title}</text>'
            f'<text class="subtitle" x="{x}" y="{y + 30}">{sub}</text>')


def rect(x, y, w, h, fill, stroke=None, sw=1.4, rx=9, extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}{extra}/>'


def arrow(x1, y1, x2, y2, t, c, kind="ar", dash=None, sw=2.0, color=None):
    # "ar" is the muted arrow, whose colour is theme-dependent — hence `c`. Leaving
    # it None here paints stroke="None", which drops the shaft and keeps the head.
    col = color or {"ar": c["mut"], "arb": BLUE, "aro": ORANGE, "arg": GREEN}[kind]
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" '
            f'stroke-width="{sw}"{d} marker-end="url(#{kind}_{t})"/>')


def wrap(text, width):
    """Greedy word wrap, so a chip never splits mid-word."""
    lines, cur = [], ""
    for word in text.split(" "):
        cand = f"{cur} {word}".strip()
        if len(cand) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    if cur:
        lines.append(cur)
    return lines


def spark(x, y, w, h, vals, color, sw=2.0, op=1.0):
    n = len(vals)
    lo, hi = min(vals), max(vals)
    rng = (hi - lo) or 1
    pts = " ".join(
        f"{x + i * w / (n - 1):.1f},{y + h - (v - lo) / rng * h:.1f}" for i, v in enumerate(vals)
    )
    return (f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round" opacity="{op}"/>')


# --------------------------------------------------------------------------- 1
def fig_loop(t, c):
    W, H = 1100, 560
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "One ring, two planes",
                        "The agent reads without restriction and writes nothing directly. "
                        "Every change it wants leaves as a diff."))
    # read band
    s.append(rect(40, 96, 1020, 112, c["panel"], c["ln"], 1.2, 10))
    s.append(f'<text class="tiny" x="60" y="122" style="fill:{BLUE};font-weight:600">'
             f'READ PLANE {DOT} Live, unrestricted, no mutation</text>')
    sources = (("Metrics", "VictoriaMetrics"), ("Logs", "Loki"), ("Platform API", "Kubernetes"))
    for i, (name, prod) in enumerate(sources):
        cx = 300 + i * 230
        s.append(rect(cx, 134, 200, 60, c["page"], BLUE, 1.5, 8))
        s.append(f'<text class="small lab" x="{cx + 100}" y="{157}" text-anchor="middle">{name}</text>')
        s.append(f'<text class="tiny" x="{cx + 100}" y="{178}" text-anchor="middle">{prod}</text>')
    # the ring, in the order the prose enumerates it
    ring = [("Alerting", "Split by", "severity", c["mut"]),
            ("Chat", "Human channel,", "agent channel", c["mut"]),
            ("Agent", "No mutating", "credential", GREEN),
            ("Pull request", "A diff a human", "can read", BLUE),
            ("CI", "Gate, by", "construction", BLUE),
            ("Reconciler", "Declared", "state", BLUE),
            ("Cluster", "The thing", "being run", c["mut"])]
    BW, STEP = 120, 150
    for i, (name, l1, l2, col) in enumerate(ring):
        x = 40 + i * STEP
        s.append(rect(x, 300, BW, 104, c["page"], col, 1.8, 10))
        s.append(f'<text class="lab" x="{x + BW / 2}" y="{334}" text-anchor="middle" '
                 f'style="font-size:16.5px">{name}</text>')
        for j, line in enumerate((l1, l2)):
            s.append(f'<text x="{x + BW / 2}" y="{358 + j * 18}" text-anchor="middle" '
                     f'style="font-size:12.5px;fill:{c["mut"]}">{line}</text>')
    for i, lab in enumerate(("Routes", "Picked up", "Opens", "Must pass", "On merge", "Applies")):
        x1, x2 = 40 + i * STEP + BW, 40 + (i + 1) * STEP
        s.append(arrow(x1 + 3, 352, x2 - 3, 352, t, c, "ar", sw=2.2))
        s.append(f'<text class="tiny" x="{(x1 + x2) / 2}" y="{286}" text-anchor="middle">{lab}</text>')
    # the read plane is both the alert substrate and the agent's query surface
    s.append(arrow(100, 208, 100, 296, t, c, "ar", dash="5 5", sw=2.0))
    s.append(f'<text class="tiny" x="118" y="256">Rules fire</text>')
    s.append(arrow(400, 208, 400, 296, t, c, "arb", dash="5 5", sw=2.0))
    s.append(f'<text class="tiny" x="418" y="256" style="fill:{BLUE}">Live read</text>')
    s.append(arrow(1000, 296, 1000, 208, t, c, "ar", dash="5 5", sw=2.0))
    s.append(f'<text class="tiny" x="982" y="256" text-anchor="end">Observed by</text>')
    # the path that does not exist
    s.append(f'<path d="M400,408 L400,472 L1000,472 L1000,408" fill="none" stroke="{ORANGE}" '
             f'stroke-width="2" stroke-dasharray="7 6" opacity="0.75"/>')
    s.append(f'<circle cx="700" cy="472" r="17" fill="{c["bg"]}" stroke="{ORANGE}" stroke-width="2"/>')
    s.append(f'<path d="M693,465 L707,479 M707,465 L693,479" stroke="{ORANGE}" stroke-width="2.6" '
             f'stroke-linecap="round"/>')
    s.append(f'<text class="small" x="700" y="512" text-anchor="middle" style="fill:{ORANGE}">'
             f'There is no mode where the agent skips this. No credential exists for the direct path.</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 2
def fig_curation(t, c):
    W, H = 1100, 620
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "Curation over accumulation",
                        "Every panel on the left is individually defensible. The board is still unreadable."))
    # left: vendor board
    s.append(rect(40, 108, 490, 476, c["panel"], c["ln"], 1.2, 10))
    s.append(f'<text class="lab small" x="62" y="138">Vendor-bundled board</text>')
    s.append(f'<text class="tiny" x="62" y="159">A panel per label value, because it cannot know yours</text>')
    live = {(0, 1): [3, 5, 4, 7, 6, 9, 8], (2, 3): [8, 6, 7, 5, 6, 4, 5], (3, 0): [2, 3, 3, 5, 4, 6, 7]}
    for r in range(5):
        for col in range(5):
            x, y = 55 + col * 94, 176 + r * 78
            if (r, col) == (1, 2):
                s.append(rect(x, y, 84, 66, ORANGE, ORANGE, 1.2, 6, ' opacity="0.9"'))
                s.append(f'<text x="{x + 42}" y="{y + 30}" text-anchor="middle" '
                         f'style="font-size:16px;fill:#ffffff;font-weight:700">1.4 GiB</text>')
                s.append(f'<text x="{x + 42}" y="{y + 50}" text-anchor="middle" '
                         f'style="font-size:13px;fill:#ffffff;opacity:0.9">&#62; 80</text>')
                continue
            s.append(rect(x, y, 84, 66, c["page"], c["ln"], 1.1, 6))
            if (r, col) in live:
                s.append(spark(x + 10, y + 18, 64, 34, live[(r, col)], BLUE, 1.8))
            else:
                s.append(f'<line x1="{x + 10}" y1="{y + 46}" x2="{x + 74}" y2="{y + 46}" '
                         f'stroke="{c["ln"]}" stroke-width="1.4" stroke-dasharray="3 4"/>')
                s.append(f'<text class="tiny" x="{x + 42}" y="{y + 30}" text-anchor="middle" '
                         f'style="font-size:11.5px">No data</text>')
    s.append(f'<text class="tiny" x="62" y="{572}">25 panels {DOT} 4 carrying data {DOT} '
             f'One red on every install</text>')
    # right: curated board
    s.append(rect(570, 108, 490, 476, c["panel"], c["ln"], 1.2, 10))
    s.append(f'<text class="lab small" x="592" y="138">What replaced it</text>')
    s.append(f'<text class="tiny" x="592" y="159">Filtered to the series that carry traffic</text>')
    tiles = [("Delivery latency", [4, 5, 4, 6, 5, 7, 6, 5, 6], BLUE),
             ("Failed notifications", [1, 2, 1, 3, 2, 1, 2, 2, 1], BLUE),
             ("Queue depth", [6, 5, 6, 4, 5, 4, 3, 4, 3], GREEN),
             ("Reconcile drift", [2, 2, 3, 2, 4, 3, 2, 3, 2], GREEN)]
    for i, (name, vals, col) in enumerate(tiles):
        x = 588 + (i % 2) * 236
        y = 178 + (i // 2) * 186
        s.append(rect(x, y, 218, 166, c["page"], c["ln"], 1.2, 8))
        s.append(f'<text class="tiny" x="{x + 14}" y="{y + 26}" style="font-weight:600">{name}</text>')
        s.append(f'<line x1="{x + 14}" y1="{y + 62}" x2="{x + 204}" y2="{y + 62}" '
                 f'stroke="{ORANGE}" stroke-width="1.4" stroke-dasharray="5 4"/>')
        s.append(f'<text class="tiny" x="{x + 204}" y="{y + 55}" text-anchor="end" '
                 f'style="fill:{ORANGE};font-size:12.5px">Measured p99</text>')
        s.append(spark(x + 14, y + 74, 190, 72, vals, col, 2.2))
    s.append(f'<text class="tiny" x="592" y="{572}">4 panels {DOT} Every one with traffic {DOT} '
             f'Thresholds from a 14-day distribution</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 3
def fig_detection(t, c):
    W, H = 1100, 600
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "The conjunction a flag-based check reads as healthy",
                        "Every self-reported field is true. Together they describe a corpse."))
    L, R = 250, 1050
    for i, name in enumerate(("Has a leader", "Indices agree", "Process is up")):
        y = 108 + i * 40
        s.append(f'<text class="small" x="{L - 20}" y="{y + 22}" text-anchor="end">{name}</text>')
        s.append(rect(L, y, R - L, 30, GREEN, GREEN, 1.2, 6, ' fill-opacity="0.18"'))
        s.append(f'<text x="{L + 16}" y="{y + 22}" style="font-size:16px;fill:{GREEN};'
                 f'font-weight:700">{CHECK}</text>')
    s.append(f'<text class="tiny" x="{R}" y="{102}" text-anchor="end">Green for the entire window</text>')
    # chart
    top, bot = 280, 500
    s.append(f'<line x1="{L}" y1="{bot}" x2="{R}" y2="{bot}" stroke="{c["ln"]}" stroke-width="1.4"/>')
    s.append(f'<line x1="{L}" y1="{top}" x2="{L}" y2="{bot}" stroke="{c["ln"]}" stroke-width="1.4"/>')
    s.append(f'<text class="tiny" x="{L - 20}" y="{top + 6}" text-anchor="end">Applied index</text>')
    s.append(f'<text class="tiny" x="{R}" y="{bot + 26}" text-anchor="end">Time</text>')
    t0 = 470
    ly0, ly1 = 468, 300
    def lead_y(x):
        return ly0 + (ly1 - ly0) * (x - L) / (R - L)
    my = lead_y(t0)
    s.append(f'<path d="M{L},{ly0} L{R},{ly1} L{R},{my} L{t0},{my} Z" fill="{ORANGE}" opacity="0.13"/>')
    s.append(f'<line x1="{L}" y1="{ly0}" x2="{R}" y2="{ly1}" stroke="{GREEN}" stroke-width="3" '
             f'stroke-linecap="round"/>')
    s.append(f'<path d="M{L},{ly0} L{t0},{my} L{R},{my}" fill="none" stroke="{BLUE}" stroke-width="3" '
             f'stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<text class="small" x="{R - 8}" y="{ly1 - 14}" text-anchor="end" '
             f'style="fill:{GREEN};font-weight:600">Leader</text>')
    s.append(f'<text class="small" x="{R - 8}" y="{my + 28}" text-anchor="end" '
             f'style="fill:{BLUE};font-weight:600">Member</text>')
    s.append(f'<line x1="{t0}" y1="{top - 8}" x2="{t0}" y2="{bot}" stroke="{c["mut"]}" '
             f'stroke-width="1.4" stroke-dasharray="4 5"/>')
    s.append(f'<text class="tiny" x="{t0 + 10}" y="{top - 12}">Member stops participating</text>')
    # 30-second sample bracket
    sx1, sx2 = 800, 900
    for sx in (sx1, sx2):
        s.append(f'<line x1="{sx}" y1="{lead_y(sx)}" x2="{sx}" y2="{my}" stroke="{c["mut"]}" '
                 f'stroke-width="1.2" stroke-dasharray="3 4"/>')
    s.append(f'<text class="tiny" x="{(sx1 + sx2) / 2}" y="{bot + 26}" text-anchor="middle">'
             f'Two samples, 30 s apart</text>')
    s.append(f'<text class="small" x="{sx1 - 8}" y="{lead_y(sx1) - 16}" text-anchor="end" '
             f'style="fill:{GREEN};font-weight:600">Leader +150 entries</text>')
    s.append(f'<text class="small" x="{sx1 - 8}" y="{my + 26}" text-anchor="end" '
             f'style="fill:{BLUE};font-weight:600">Member +0</text>')
    s.append(rect(250, 536, 800, 44, ORANGE, ORANGE, 1.4, 9, ' fill-opacity="0.12"'))
    s.append(f'<text class="small" x="650" y="564" text-anchor="middle" style="fill:{ORANGE};'
             f'font-weight:600">The alert keys on the pair {DOT} Has a leader, committing nothing</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 4
def fig_layers(t, c):
    W, H = 1100, 596
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "Three layers of automatic fix",
                        "In descending order of what they are worth. The bar on the right is that order."))
    rows = [
        (230, GREEN, "Configuration that makes the failure survivable",
         "Covers: an entire class of incident, before anything has to detect it.",
         "Costs: measurement. Almost always a parameter, not a mechanism.",
         "Removes the class"),
        (150, BLUE, "Reconciliation",
         "Covers: any divergence from declared state, continuously, as a non-event.",
         "Blind to: an unhealthy component that matches its spec, and any layer applied on demand.",
         "Removes the drift"),
        (78, ORANGE, "Gated repair, for everything destructive",
         "Covers: fixes that delete data, each step preceded by a live proof of safety.",
         "Refuses: to act on anything still advancing; to claim success unverified.",
         "Removes the gamble"),
    ]
    y = 116
    for bw, col, name, l1, l2, tag in rows:
        s.append(rect(40, y, 1020, 118, c["panel"], c["ln"], 1.2, 10))
        s.append(rect(40, y, 6, 118, col, None, 0, 3))
        s.append(f'<text class="lab" x="66" y="{y + 36}">{name}</text>')
        s.append(f'<text class="small" x="66" y="{y + 65}">{l1}</text>')
        s.append(f'<text class="small mut" x="66" y="{y + 91}">{l2}</text>')
        s.append(rect(1040 - bw, y + 40, bw, 18, col, None, 0, 9, ' fill-opacity="0.85"'))
        s.append(f'<text class="tiny" x="1040" y="{y + 82}" text-anchor="end" '
                 f'style="fill:{col};font-weight:600">{tag}</text>')
        y += 144
    s.append(f'<text class="small" x="40" y="{y + 20}" style="fill:{c["title"]}">'
             f'The best automation of the incident below was a number, from the top layer.</text>')
    return "".join(s) + "</svg>"


def fig_selfheal(t, c):
    W, H = 1100, 520
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "Three seconds of drift",
                        "One live edit against a pinned manifest, recorded verbatim as the reconciler answered it."))
    # Terminal card — deliberately dark in both themes; a terminal is a terminal.
    TBG, TLINE = "#191927", "#33334a"
    INK, MUT = "#e8e8f0", "#8f8f9c"
    s.append(rect(40, 100, 1020, 296, TBG, TLINE, 1.4, 12))
    for i, col in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        s.append(f'<circle cx="{68 + i * 26}" cy="126" r="7" fill="{col}"/>')
    lines = [
        (GREEN, "$ ", INK, "kubectl -n observability scale deployment/backup-canary-exporter --replicas=2"),
        (None, "", MUT, "deployment.apps/backup-canary-exporter scaled"),
        (None, "", MUT, ""),
        (None, "", MUT, "# watcher: poll every 3 s, print on change   (git pins replicas: 1)"),
        (None, "", MUT, "12:08:24Z  spec.replicas=1  ready=1  app/exporters: Synced     op=Succeeded"),
        (ORANGE, "", ORANGE, "12:14:47Z  spec.replicas=2  ready=1  app/exporters: OutOfSync  op=Running"),
        (GREEN, "", GREEN, "12:14:50Z  spec.replicas=1  ready=1  app/exporters: Synced     op=Running"),
        (None, "", MUT, "12:14:50Z  reverted &#8212; watcher exiting"),
    ]
    y = 168
    for pcol, prompt, col, text in lines:
        if prompt:
            s.append(f'<text class="mono" x="66" y="{y}" style="fill:{pcol}">{prompt}</text>')
        s.append(f'<text class="mono" x="{66 + (20 if prompt else 0)}" y="{y}" style="fill:{col}">{text}</text>')
        y += 27
    # bracket marking the three seconds between the two key lines
    y1, y2 = 168 + 5 * 27 - 5, 168 + 6 * 27 + 2
    bx = 812
    s.append(f'<path d="M{bx},{y1} L{bx + 12},{y1} L{bx + 12},{y2} L{bx},{y2}" fill="none" '
             f'stroke="{ORANGE}" stroke-width="1.8"/>')
    s.append(f'<text class="small" x="{bx + 24}" y="{(y1 + y2) / 2 - 4}" style="fill:{ORANGE};font-weight:600">3 s</text>')
    s.append(f'<text class="tiny" x="{bx + 24}" y="{(y1 + y2) / 2 + 14}">Already syncing</text>')
    s.append(f'<text class="tiny" x="{bx + 24}" y="{(y1 + y2) / 2 + 32}">at first sight</text>')
    s.append(rect(40, 426, 1020, 54, c["panel"], c["ln"], 1.2, 9))
    s.append(f'<text class="mono" x="60" y="{458}">Drift lifetime: &#8804;3 s {DOT} Sustained-drift alert '
             f'threshold: 1 h {DOT} Messages produced: 0 {DOT} Humans interrupted: 0</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 5
def fig_drift(t, c):
    W, H = 1100, 540
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "Two regimes of declared state",
                        "The same repository. Only one of them notices when reality stops matching it."))

    def panel(px, title, sub, col, on_demand):
        g = [rect(px, 108, 490, 320, c["panel"], c["ln"], 1.2, 10)]
        g.append(f'<text class="lab small" x="{px + 22}" y="{138}" style="fill:{col}">{title}</text>')
        g.append(f'<text class="tiny" x="{px + 22}" y="{159}">{sub}</text>')
        ax, ay, base = px + 74, 186, 356          # chart box: top, and the zero line
        g.append(f'<text class="tiny" x="{ax - 12}" y="{ay + 6}" text-anchor="end" '
                 f'style="font-size:13px">Drift</text>')
        g.append(f'<text class="tiny" x="{ax - 12}" y="{base + 5}" text-anchor="end" '
                 f'style="font-size:13px">None</text>')
        g.append(f'<line x1="{ax}" y1="{base}" x2="{px + 466}" y2="{base}" stroke="{c["ln"]}" stroke-width="1.4"/>')
        g.append(f'<line x1="{ax}" y1="{ay}" x2="{ax}" y2="{base}" stroke="{c["ln"]}" stroke-width="1.4"/>')
        w = px + 460 - ax

        def X(f):
            return ax + w * f

        if not on_demand:
            pts = [(0.0, 0)]
            for f in (0.16, 0.40, 0.63, 0.85):    # each divergence pulled straight back
                pts += [(f, 0), (f + 0.03, 22), (f + 0.07, 0)]
            pts.append((1.0, 0))
            d = " ".join(f"{'M' if i == 0 else 'L'}{X(f):.1f},{base - v:.1f}"
                         for i, (f, v) in enumerate(pts))
            g.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
            g.append(f'<text class="tiny" x="{X(0.5)}" y="{base - 62}" text-anchor="middle" '
                     f'style="fill:{col};font-weight:600">Corrected before anyone could look</text>')
            g.append(f'<text class="tiny" x="{X(0.5)}" y="{base + 44}" text-anchor="middle">'
                     f'The reconciler is its own detector</text>')
        else:
            # drift steps up and stays up; the shaded window is the part nobody is watching
            g.append(rect(X(0.30), ay + 6, X(0.66) - X(0.30), base - ay - 6, ORANGE, None, 0, 4,
                          ' opacity="0.12"'))
            g.append(f'<text class="tiny" x="{X(0.48)}" y="{ay + 24}" text-anchor="middle" '
                     f'style="fill:{ORANGE}">Silent: nothing is watching</text>')
            steps = [(0.0, 0), (0.30, 0), (0.30, 34), (0.46, 34), (0.46, 68), (0.66, 68)]
            d = " ".join(f"{'M' if i == 0 else 'L'}{X(f):.1f},{base - v:.1f}"
                         for i, (f, v) in enumerate(steps))
            g.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="3" '
                     f'stroke-linejoin="round" stroke-linecap="round"/>')
            # what happens with no scheduled plan
            g.append(f'<path d="M{X(0.66):.1f},{base - 68} L{X(1.0):.1f},{ay + 10}" fill="none" '
                     f'stroke="{c["mut"]}" stroke-width="2" stroke-dasharray="6 5"/>')
            g.append(f'<text class="tiny" x="{px + 460}" y="{ay + 4}" text-anchor="end">'
                     f'Without a scheduled plan</text>')
            # the probe that catches it, and the apply that clears it
            g.append(f'<path d="M{X(0.66):.1f},{base - 68} L{X(0.74):.1f},{base - 68} '
                     f'L{X(0.74):.1f},{base} L{X(1.0):.1f},{base}" fill="none" stroke="{col}" '
                     f'stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
            g.append(f'<line x1="{X(0.66)}" y1="{base - 92}" x2="{X(0.66)}" y2="{base}" '
                     f'stroke="{ORANGE}" stroke-width="1.6" stroke-dasharray="4 4"/>')
            g.append(f'<text class="tiny" x="{X(0.66) - 10}" y="{base - 104}" text-anchor="end" '
                     f'style="fill:{ORANGE};font-weight:600">Plan returns non-empty</text>')
            g.append(f'<text class="tiny" x="{X(0.76)}" y="{base - 14}" '
                     f'style="font-size:13px">Apply</text>')
            for f in (0.12, 0.39, 0.66, 0.93):    # the scheduled probes themselves
                g.append(f'<path d="M{X(f) - 6:.1f},{base + 14} L{X(f) + 6:.1f},{base + 14} '
                         f'L{X(f):.1f},{base + 4} Z" fill="{c["mut"]}"/>')
            g.append(f'<text class="tiny" x="{X(0.5)}" y="{base + 44}" text-anchor="middle">'
                     f'Scheduled plans are the only detector</text>')
        return "".join(g)

    s.append(panel(40, "Continuously reconciled", "Cluster objects, dashboards, alert rules", GREEN, False))
    s.append(panel(570, "Applied on demand", "DNS, repositories, buckets, projects", ORANGE, True))
    s.append(rect(40, 448, 1020, 60, c["panel"], c["ln"], 1.2, 9))
    s.append(f'<text class="small" x="550" y="484" text-anchor="middle" style="fill:{c["title"]}">'
             f'In one regime the absence of drift is a property. In the other it is a claim, and a claim has to be checked.</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 6
def fig_verification(t, c):
    W, H = 590, 300
    W, H = 1100, 580
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "A check that cannot fail is not a check",
                        "A broken check and a passing check produce identical output: silence, and a green mark."))
    def panel(x, title, col, flat):
        g = [rect(x, 110, 490, 282, c["panel"], c["ln"], 1.2, 10)]
        g.append(f'<text class="lab small" x="{x + 22}" y="{140}" style="fill:{col}">{title}</text>')
        ax, ay0, ay1 = x + 90, 178, 348
        g.append(rect(x + 290, ay0, 178, ay1 - ay0, ORANGE, None, 0, 6, ' opacity="0.10"'))
        g.append(f'<text class="tiny" x="{x + 379}" y="{ay0 + 18}" text-anchor="middle" '
                 f'style="fill:{ORANGE}">Actually broken</text>')
        g.append(f'<line x1="{ax}" y1="{ay1}" x2="{x + 468}" y2="{ay1}" stroke="{c["ln"]}" stroke-width="1.3"/>')
        g.append(f'<line x1="{ax}" y1="{ay0 + 30}" x2="{ax}" y2="{ay1}" stroke="{c["ln"]}" stroke-width="1.3"/>')
        pass_y, fail_y = ay0 + 52, ay1 - 26
        for lab, yy in (("Pass", pass_y), ("Fail", fail_y)):
            g.append(f'<text class="tiny" x="{ax - 12}" y="{yy + 5}" text-anchor="end">{lab}</text>')
            g.append(f'<line x1="{ax}" y1="{yy}" x2="{x + 468}" y2="{yy}" stroke="{c["ln"]}" '
                     f'stroke-width="1" stroke-dasharray="3 5"/>')
        if flat:
            g.append(f'<line x1="{ax + 6}" y1="{pass_y}" x2="{x + 460}" y2="{pass_y}" stroke="{col}" '
                     f'stroke-width="3.4" stroke-linecap="round"/>')
            g.append(f'<text class="small" x="{x + 379}" y="{pass_y + 30}" text-anchor="middle" '
                     f'style="fill:{col};font-weight:600">Still passing</text>')
        else:
            g.append(f'<path d="M{ax + 6},{pass_y} L{x + 290},{pass_y} L{x + 290},{fail_y} '
                     f'L{x + 460},{fail_y}" fill="none" stroke="{col}" stroke-width="3.4" '
                     f'stroke-linecap="round" stroke-linejoin="round"/>')
            g.append(f'<text class="small" x="{x + 379}" y="{fail_y - 16}" text-anchor="middle" '
                     f'style="fill:{col};font-weight:600">Goes red</text>')
        g.append(f'<text class="tiny" x="{x + 90}" y="{ay1 + 24}">Healthy</text>')
        g.append(f'<text class="tiny" x="{x + 468}" y="{ay1 + 24}" text-anchor="end">Broken</text>')
        return "".join(g)
    s.append(panel(40, "An honest check", GREEN, False))
    s.append(panel(570, "A check that cannot fail", ORANGE, True))
    chips = [("Privilege mismatch",
              "An existence test run as the wrong user returns false either way"),
             ("Operator precedence",
              "The threshold filters the join key rather than the value you meant"),
             ("Reading the wrong instance",
              "Oldest-first ordering reports a value from a previous boot")]
    for i, (name, body) in enumerate(chips):
        x = 40 + i * 348
        s.append(rect(x, 424, 324, 82, c["page"], c["ln"], 1.2, 9))
        s.append(f'<text class="tiny" x="{x + 16}" y="{450}" style="font-weight:600;'
                 f'fill:{c["title"]}">{name}</text>')
        for j, line in enumerate(wrap(body, 43)):
            s.append(f'<text class="tiny" x="{x + 16}" y="{472 + j * 20}">{line}</text>')
    s.append(f'<text class="small" x="550" y="546" text-anchor="middle" style="fill:{c["title"]}">'
             f'The rule: mutate the input until it goes red. A guard never observed refusing is not a guard.</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 6
def fig_digest(t, c):
    W, H = 1100, 660
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "A report that states what it could not see",
                        "Absence of evidence is evidence of absence only once you have shown you would have seen it."))
    # left: the indistinguishable pair
    s.append(rect(40, 108, 500, 358, c["panel"], c["ln"], 1.2, 10))
    s.append(f'<text class="lab small" x="62" y="138">Two inputs, one output</text>')
    for i, (src, col) in enumerate((("Healthy system", GREEN), ("Dead collector", ORANGE))):
        y = 166 + i * 74
        s.append(rect(62, y, 190, 54, c["page"], col, 1.5, 8))
        s.append(f'<text class="tiny" x="157" y="{y + 32}" text-anchor="middle" '
                 f'style="font-weight:600;fill:{col}">{src}</text>')
        s.append(arrow(258, y + 27, 300, y + 27, t, c, "ar", sw=1.8))
    s.append(rect(306, 166, 212, 128, c["page"], c["ln"], 1.4, 8))
    s.append(f'<text class="small" x="412" y="{222}" text-anchor="middle" '
             f'style="fill:{c["title"]};font-weight:600">"No problems</text>')
    s.append(f'<text class="small" x="412" y="{246}" text-anchor="middle" '
             f'style="fill:{c["title"]};font-weight:600">found"</text>')
    s.append(f'<text class="tiny" x="412" y="{316}" text-anchor="middle">Indistinguishable</text>')
    s.append(rect(62, 336, 456, 106, ORANGE, ORANGE, 1.5, 9, ' fill-opacity="0.10"'))
    s.append(f'<text class="small" x="82" y="{366}" style="fill:{ORANGE};font-weight:600">'
             f'So the digest proves its source first</text>')
    s.append(f'<text class="tiny" x="82" y="{392}">It says so in the report, every day, before any</text>')
    s.append(f'<text class="tiny" x="82" y="{414}">claim about the fleet is allowed to appear.</text>')
    # right: the digest itself
    s.append(rect(570, 108, 490, 358, c["panel"], c["ln"], 1.2, 10))
    s.append(f'<text class="lab small" x="592" y="138">What it ships, every morning</text>')
    lines = [(GREEN, CHECK, "Source live: 42 samples in the last 5 min"),
             (BLUE, CHECK, "Tier 1 healthy &#8212; 0 restarts / 24 h"),
             (BLUE, CHECK, "Tier 2 healthy &#8212; p99 lag 240 ms"),
             (BLUE, CHECK, "Backups current &#8212; 28 GiB, 3 h old"),
             (ORANGE, "!", "Could not see: RBAC gap on one resource type")]
    for i, (col, gl, txt) in enumerate(lines):
        y = 164 + i * 44
        s.append(rect(592, y, 446, 36, c["page"], c["ln"], 1.1, 7))
        s.append(f'<text x="610" y="{y + 25}" style="font-size:15px;fill:{col};font-weight:700">{gl}</text>')
        s.append(f'<text class="mono" x="634" y="{y + 24}" style="fill:{c["body"]}">{txt}</text>')
    s.append(f'<text class="tiny" x="592" y="{404}" style="fill:{ORANGE}">'
             f'The gap is reported daily, beside the proxy signals used instead</text>')
    s.append(f'<text class="tiny" x="592" y="{430}">Lands as a pull request {DOT} '
             f'CI posts the summary to the channel</text>')
    s.append(f'<text class="tiny" x="592" y="{452}">A human merges it to keep the history, or closes it</text>')
    # correction banner
    s.append(rect(40, 496, 1020, 122, c["page"], c["ln"], 1.2, 10))
    s.append(rect(40, 496, 6, 122, ORANGE, None, 0, 3))
    s.append(f'<text class="lab small" x="70" y="{526}" style="fill:{ORANGE}">'
             f'Correction {DOT} Added four days later</text>')
    s.append(f'<text class="small" x="70" y="{556}">The first diagnosis blamed the network. '
             f'It was wrong, and it stays on the page.</text>')
    s.append(f'<text class="small mut" x="70" y="{584}">The reasoning that produced a confident wrong answer '
             f'is the most reusable artifact an incident generates;</text>')
    s.append(f'<text class="small mut" x="70" y="{606}">deleting it guarantees somebody rediscovers it.</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 7
def fig_substrate(t, c):
    W, H = 1100, 596
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "The properties are portable; the components are not",
                        "Managed or self-managed, the same three properties have to hold. Only the parts change."))
    cols = [(360, 340, "Self-managed (ours)", GREEN), (720, 340, "Managed control plane", BLUE)]
    for x, w, name, col in cols:
        s.append(f'<text class="lab small" x="{x + w / 2}" y="{132}" text-anchor="middle" '
                 f'style="fill:{col}">{name}</text>')
    rows = [(("No listening", "surface"), "Outbound tunnel only; nothing to scan",
             "Private cluster, managed ingress"),
            (("Authorization that is", "not membership"), "Tag-scoped mesh ACLs, not network reach",
             "IAM and service controls"),
            (("State that survives", "the cluster"), "Off-host object storage, same egress path",
             "Managed snapshots and backups")]
    for i, (prop, selfimpl, mgd) in enumerate(rows):
        y = 152 + i * 100
        s.append(rect(40, y, 300, 84, c["panel"], c["ln"], 1.2, 9))
        s.append(f'<text class="small lab" x="60" y="{y + 36}">{prop[0]}</text>')
        s.append(f'<text class="small lab" x="60" y="{y + 60}">{prop[1]}</text>')
        for x, w, txt, col in ((360, 340, selfimpl, GREEN), (720, 340, mgd, BLUE)):
            s.append(rect(x, y, w, 84, c["page"], col, 1.5, 9))
            s.append(f'<text class="tiny" x="{x + w / 2}" y="{y + 48}" text-anchor="middle">{txt}</text>')
    # failure distribution band
    y = 484
    s.append(f'<text class="small" x="40" y="{y - 10}" style="fill:{c["title"]}">'
             f'What actually differs is the failure distribution, and therefore how much repair machinery you build:</text>')
    s.append(rect(360, y + 12, 340, 56, GREEN, GREEN, 1.4, 9, ' fill-opacity="0.14"'))
    s.append(f'<text class="tiny" x="530" y="{y + 38}" text-anchor="middle" style="fill:{GREEN};'
             f'font-weight:600">Consensus and member failures</text>')
    s.append(f'<text class="tiny" x="530" y="{y + 58}" text-anchor="middle">Yours to diagnose</text>')
    s.append(rect(720, y + 12, 340, 56, c["panel"], c["ln"], 1.4, 9))
    s.append(f'<text class="tiny" x="890" y="{y + 46}" text-anchor="middle">'
             f'Somebody else&#8217;s pager {DOT} Skip a chapter</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 8
def fig_retention(t, c):
    W, H = 1100, 574
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "The default was not wrong. It was wrong here.",
                        "How long a member may stall and still catch up incrementally, at our measured throughput."))
    L, R = 300, 1050
    span = 120.0
    def xf(m):
        return L + (R - L) * m / span
    bands = [(196, "Retention 5,000 entries", "The shipped default", 9.2, "9 min"),
             (324, "Retention 50,000 entries", "Measured against our rate", 92.0, "92 min")]
    for y, name, sub, cliff, lab in bands:
        s.append(f'<text class="small lab" x="{L - 24}" y="{y + 28}" text-anchor="end">{name}</text>')
        s.append(f'<text class="tiny" x="{L - 24}" y="{y + 52}" text-anchor="end">{sub}</text>')
        cx = xf(cliff)
        s.append(rect(L, y, cx - L, 66, GREEN, GREEN, 1.4, 8, ' fill-opacity="0.20"'))
        s.append(rect(cx, y, R - cx, 66, ORANGE, ORANGE, 1.4, 8, ' fill-opacity="0.16"'))
        s.append(f'<line x1="{cx}" y1="{y - 14}" x2="{cx}" y2="{y + 80}" stroke="{c["title"]}" '
                 f'stroke-width="2"/>')
        s.append(f'<text class="tiny" x="{cx}" y="{y - 22}" text-anchor="middle" '
                 f'style="font-weight:600;fill:{c["title"]}">{lab}</text>')
        if cliff < 40:
            s.append(f'<text class="tiny" x="{(cx + R) / 2}" y="{y + 40}" text-anchor="middle" '
                     f'style="fill:{ORANGE}">A transient blip becomes a dead member, deterministically</text>')
        else:
            s.append(f'<text class="tiny" x="{(L + cx) / 2}" y="{y + 40}" text-anchor="middle" '
                     f'style="fill:{GREEN}">The same class of event now resolves itself</text>')
    # axis
    ay = 424
    s.append(f'<line x1="{L}" y1="{ay}" x2="{R}" y2="{ay}" stroke="{c["ln"]}" stroke-width="1.4"/>')
    for m in range(0, 121, 15):
        s.append(f'<line x1="{xf(m)}" y1="{ay}" x2="{xf(m)}" y2="{ay + 7}" stroke="{c["ln"]}" stroke-width="1.4"/>')
        s.append(f'<text class="tiny" x="{xf(m)}" y="{ay + 26}" text-anchor="middle">{m}</text>')
    s.append(f'<text class="tiny" x="{R}" y="{ay + 48}" text-anchor="end">Minutes a member is stalled</text>')
    s.append(f'<text class="tiny" x="{L}" y="{140}" style="fill:{GREEN};font-weight:600">'
             f'Catches up incrementally</text>')
    s.append(f'<text class="tiny" x="{R}" y="{140}" text-anchor="end" style="fill:{ORANGE};font-weight:600">'
             f'Needs a full snapshot &#8212; which frequently failed on our network</text>')
    s.append(rect(40, 498, 1020, 54, c["panel"], c["ln"], 1.2, 9))
    s.append(f'<text class="mono" x="60" y="{530}">543 entries/min applied {DOT} 5,000 &#247; 543 '
             f'{APPROX} 9 min {DOT} 50,000 &#247; 543 {APPROX} 92 min {DOT} '
             f'Cost of the fix: a few hundred MiB</text>')
    return "".join(s) + "</svg>"


# --------------------------------------------------------------------------- 9
def fig_cost(t, c):
    W, H = 1100, 470
    s = [head(W, H, t, c)]
    s.append(titleblock(40, "Where the money actually goes",
                        "The same tooling, priced on the two plans a reader might plausibly be on."))
    L, R = 250, 960
    top = 215.0
    def xf(v):
        return L + (R - L) * v / top
    segs = [("Infrastructure tooling", GREEN), ("The operator, agent subscription", ORANGE)]
    bars = [(150, "Lower bound", [8, 20], "US$28"), (270, "Upper bound", [8, 200], "US$208")]
    for y, name, vals, total in bars:
        s.append(f'<text class="small lab" x="{L - 24}" y="{y + 34}" text-anchor="end">{name}</text>')
        s.append(rect(L, y, R - L, 76, c["panel"], c["ln"], 1.1, 8))
        x = L
        for v, (_, col) in zip(vals, segs):
            w = xf(v) - L
            s.append(rect(x, y, w, 76, col, None, 0, 4, ' fill-opacity="0.85"'))
            if w > 52:
                s.append(f'<text x="{x + w / 2}" y="{y + 45}" text-anchor="middle" '
                         f'style="font-size:16px;fill:#ffffff;font-weight:700">US${v}</text>')
            x += w
        s.append(f'<text class="small lab" x="{x + 16}" y="{y + 45}">{total}</text>')
    # pointer at the headline slice
    hx = (L + xf(8)) / 2
    s.append(f'<path d="M{hx},{126} L{hx},{102} L{hx + 150},{102}" fill="none" stroke="{GREEN}" '
             f'stroke-width="1.6"/>')
    s.append(f'<text class="tiny" x="{hx + 158}" y="{107}" style="fill:{GREEN};font-weight:600">'
             f'US$8 {DOT} What the description calls under US$10 {DOT} The only row nobody argues about</text>')
    y = 386
    for i, (name, col) in enumerate(segs):
        x = 250 + i * 320
        s.append(rect(x, y, 16, 16, col, None, 0, 4))
        s.append(f'<text class="tiny" x="{x + 26}" y="{y + 14}">{name}</text>')
    s.append(f'<text class="small mut" x="250" y="{y + 52}">'
             f'The cluster itself and the domains that point at it are not in this chart.</text>')
    return "".join(s) + "</svg>"


FIGS = [("loop", fig_loop), ("curation", fig_curation), ("detection", fig_detection),
        ("layers", fig_layers), ("selfheal", fig_selfheal), ("drift", fig_drift), ("verification", fig_verification), ("digest", fig_digest),
        ("substrate", fig_substrate), ("retention", fig_retention), ("cost", fig_cost)]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in FIGS:
        for theme, c in TH.items():
            path = os.path.join(OUT, f"{name}_{theme}.svg")
            with open(path, "w") as f:
                f.write(fn(theme, c))
            print("wrote", path)
