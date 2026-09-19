#!/usr/bin/env python3
"""Render assets/demo.gif: a terminal showing STTP flagging slop, then the blunt result.

Reproducible. Requires Pillow and a monospace TTF (Menlo on macOS by default).
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 860, 360
BG = "#0d1117"
WIN = "#161b22"
BORDER = "#30363d"
TEXT = "#c9d1d9"
DIM = "#8b949e"
GREEN = "#3fb950"
RED = "#f85149"
BLUE = "#58a6ff"
DOTS = ["#ff5f56", "#ffbd2e", "#27c93f"]

FONT = "/System/Library/Fonts/Menlo.ttc"
body = ImageFont.truetype(FONT, 20)
title = ImageFont.truetype(FONT, 14)
code = ImageFont.truetype(FONT, 16)

GROUPS = ["flattery", "emdash", "notxy", "slop"]
CODES = {
    "flattery": "403  Flattery Opener",
    "emdash": "451  Em Dash Detected",
    "notxy": "400  Negative parallelism",
    "slop": "420  Slop: leverage, robust, seamless",
}
LINES = [
    [("You're absolutely right! ", "flattery"), ("Great question.", None)],
    [("It's not just a bug ", "notxy"), ("—", "emdash"), (" it's", "notxy"), (" a chance to", None)],
    [("leverage", "slop"), (" a ", None), ("robust", "slop"), (", ", None), ("seamless", "slop"), (" solution.", None)],
]


def frame(active, codes_shown, label, cursor):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, W - 10, H - 10], radius=12, fill=WIN, outline=BORDER, width=1)
    d.line([10, 42, W - 10, 42], fill=BORDER, width=1)
    for i, c in enumerate(DOTS):
        d.ellipse([28 + i * 22, 20, 42 + i * 22, 34], fill=c)
    d.text((110, 18), "sttp  //  straight to the point", font=title, fill=DIM)

    x0, y = 34, 62
    d.text((x0, y), label, font=code, fill=DIM if "without" in label else GREEN)
    y += 34
    for line in LINES:
        x = x0
        for text, grp in line:
            col = RED if (grp in active) else TEXT
            d.text((x, y), text, font=body, fill=col)
            x += d.textlength(text, font=body)
        y += 32
    if cursor:
        d.rectangle([x0, y - 30, x0 + 11, y - 8], fill=TEXT)

    cy = y + 16
    for g in codes_shown:
        d.text((x0, cy), CODES[g], font=code, fill=RED)
        cy += 24
    return img


def result_frame():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, W - 10, H - 10], radius=12, fill=WIN, outline=BORDER, width=1)
    d.line([10, 42, W - 10, 42], fill=BORDER, width=1)
    for i, c in enumerate(DOTS):
        d.ellipse([28 + i * 22, 20, 42 + i * 22, 34], fill=c)
    d.text((110, 18), "sttp  //  straight to the point", font=title, fill=DIM)
    d.text((34, 62), "// with STTP", font=code, fill=GREEN)
    d.text((34, 96), "Fixed. The cache was not invalidated on write.", font=body, fill=TEXT)
    d.text((34, 150), "200 OK", font=code, fill=GREEN)
    d.text((120, 150), "clean   answer first   no padding", font=code, fill=DIM)
    return img


def build():
    frames, durations = [], []

    def add(img, ms):
        frames.append(img)
        durations.append(ms)

    label = "// without STTP"
    for n in range(1, 4):  # reveal slop lines is implicit; show full block with growing cursor blink
        add(frame(set(), [], label, n % 2 == 0), 300)
    add(frame(set(), [], label, True), 500)

    shown = []
    active = set()
    for g in GROUPS:  # flag each offender, accumulate codes
        active.add(g)
        shown.append(g)
        add(frame(set(active), list(shown), label, False), 520)
    add(frame(set(active), list(shown), label, False), 700)

    add(result_frame(), 300)  # compile to blunt result
    add(result_frame(), 2000)

    out = os.path.join(os.path.dirname(__file__), "demo.gif")
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=False, disposal=2)
    print("wrote", out, "frames", len(frames))


if __name__ == "__main__":
    build()
