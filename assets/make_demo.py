#!/usr/bin/env python3
"""Render assets/demo.gif: type a sloppy reply, sweep an STTP scanline that flags
each offender with a status code, then compile to the blunt result.

Reproducible. Requires Pillow and a monospace TTF (Menlo on macOS by default).
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 860, 380
BG = "#0d1117"
WIN = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
DIM = "#8b949e"
GREEN = "#3fb950"
RED = "#f85149"
SCAN = "#58a6ff"
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]

FONT = "/System/Library/Fonts/Menlo.ttc"
body = ImageFont.truetype(FONT, 20)
title = ImageFont.truetype(FONT, 14)
code = ImageFont.truetype(FONT, 16)

X0 = 34
Y_LABEL = 62
Y_LINES = [98, 130, 162]
Y_CODES = 200
LINE_H = 24

LINES = [
    [("You're absolutely right! ", "flattery"), ("Great question.", None)],
    [("It's not just a bug ", "notxy"), ("—", "emdash"), (" it's", "notxy"), (" a chance to", None)],
    [("leverage", "slop"), (" a ", None), ("robust", "slop"), (", ", None), ("seamless", "slop"), (" solution.", None)],
]
LINE_GROUPS = [["flattery"], ["emdash", "notxy"], ["slop"]]
CODE_ORDER = ["flattery", "emdash", "notxy", "slop"]
CODES = {
    "flattery": "403  Flattery Opener",
    "emdash": "451  Em Dash Detected",
    "notxy": "400  Negative parallelism",
    "slop": "420  Slop: leverage, robust, seamless",
}
LINE_LENS = [sum(len(t) for t, _ in ln) for ln in LINES]
TOTAL = sum(LINE_LENS)


def chrome(d):
    d.rounded_rectangle([10, 10, W - 10, H - 10], radius=12, fill=WIN, outline=BORDER, width=1)
    d.line([10, 42, W - 10, 42], fill=BORDER, width=1)
    for i, c in enumerate(DOTS):
        d.ellipse([28 + i * 22, 20, 42 + i * 22, 34], fill=c)
    d.text((110, 18), "sttp  //  straight to the point", font=title, fill=DIM)


def draw_line(d, li, reveal, active):
    remaining = reveal
    x, y = X0, Y_LINES[li]
    consumed_all = reveal >= LINE_LENS[li]
    cursor_x = None
    for t, g in LINES[li]:
        if remaining <= 0:
            break
        seg = t if len(t) <= remaining else t[:remaining]
        col = RED if g in active else TEXT
        d.text((x, y), seg, font=body, fill=col)
        x += d.textlength(seg, font=body)
        remaining -= len(seg)
    if not consumed_all:
        cursor_x = x
    return cursor_x


def render(reveal, active, codes_shown, scan_y, cursor_line, result=False):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    chrome(d)
    if result:
        d.text((X0, Y_LABEL), "// with STTP", font=code, fill=GREEN)
        d.text((X0, 108), "Fixed. The cache was not invalidated on write.", font=body, fill=TEXT)
        d.text((X0, 168), "200 OK", font=code, fill=GREEN)
        d.text((X0 + 86, 168), "clean   answer first   no padding", font=code, fill=DIM)
        return img

    d.text((X0, Y_LABEL), "// without STTP", font=code, fill=DIM)
    consumed = 0
    for li in range(len(LINES)):
        rev = max(0, min(LINE_LENS[li], reveal - consumed))
        cx = draw_line(d, li, rev, active)
        if cursor_line == li and cx is not None:
            d.rectangle([cx, Y_LINES[li] - 2, cx + 11, Y_LINES[li] + 20], fill=TEXT)
        consumed += LINE_LENS[li]

    if scan_y is not None:
        d.rectangle([16, scan_y + 2, W - 16, scan_y + 3], fill="#1f3350")
        d.rectangle([16, scan_y, W - 16, scan_y + 1], fill=SCAN)

    cy = Y_CODES
    for g in CODE_ORDER:
        if g in codes_shown:
            d.text((X0, cy), CODES[g], font=code, fill=RED)
            cy += LINE_H
    return img


def build():
    frames, durations = [], []

    def add(img, ms):
        frames.append(img)
        durations.append(ms)

    # Phase 1: type the sloppy reply
    reveal = 0
    while reveal < TOTAL:
        reveal = min(TOTAL, reveal + 5)
        consumed = 0
        cline = 0
        for li in range(len(LINES)):
            if reveal - consumed < LINE_LENS[li]:
                cline = li
                break
            consumed += LINE_LENS[li]
            cline = li
        add(render(reveal, set(), [], None, cline), 45)
    add(render(TOTAL, set(), [], None, None), 350)

    # Phase 2: scanline sweep, flag offenders as it passes each line
    active, shown = set(), []
    top, bot = 86, 182
    steps = 16
    for s in range(steps + 1):
        y = top + (bot - top) * s / steps
        for li, yb in enumerate(Y_LINES):
            if y >= yb + 14:
                for g in LINE_GROUPS[li]:
                    active.add(g)
                    if g not in shown:
                        shown.append(g)
        add(render(TOTAL, set(active), list(shown), y, None), 70)
    add(render(TOTAL, set(active), list(shown), None, None), 900)

    # Phase 3: compile to the blunt result
    add(render(0, set(), [], None, None, result=True), 300)
    add(render(0, set(), [], None, None, result=True), 2000)

    out = os.path.join(os.path.dirname(__file__), "demo.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=False, disposal=2)
    print("wrote", out, "frames", len(frames))


if __name__ == "__main__":
    build()
