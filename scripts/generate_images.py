"""Generate the generic plant illustrations in custom_components/plant_watering/images.

Run from the repository root: python scripts/generate_images.py
Each plant type in data/plants.json points at one of these archetypes.
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "custom_components" / "plant_watering" / "images"

BG = "#eaf3e6"
POT = "#c96f4a"
POT_RIM = "#b15c3a"
SOIL = "#5b4031"
GREEN = "#3f8f4f"
GREEN_DARK = "#2e6e3c"
GREEN_LIGHT = "#6cb36a"
BASE = (128, 170)


def leaf(x, y, length, width, angle, fill, rib=True, rib_color="#ffffff55"):
    """A pointed leaf whose base sits at (x, y), rotated by angle degrees from vertical."""
    w, l = width, length
    path = f"M0,0 C{w},{-l * 0.25} {w * 0.9},{-l * 0.8} 0,{-l} C{-w * 0.9},{-l * 0.8} {-w},{-l * 0.25} 0,0 Z"
    out = f'<g transform="translate({x:.1f},{y:.1f}) rotate({angle:.1f})"><path d="{path}" fill="{fill}"/>'
    if rib:
        out += f'<path d="M0,0 L0,{-l * 0.92}" stroke="{rib_color}" stroke-width="2" fill="none"/>'
    return out + "</g>"


def stem(x1, y1, x2, y2, color=GREEN_DARK, width=3, bend=0):
    mx, my = (x1 + x2) / 2 + bend, (y1 + y2) / 2
    return f'<path d="M{x1:.1f},{y1:.1f} Q{mx:.1f},{my:.1f} {x2:.1f},{y2:.1f}" stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round"/>'


def tip(angle, length, origin=BASE):
    a = math.radians(angle)
    return origin[0] + math.sin(a) * length, origin[1] - math.cos(a) * length


def pot():
    return (
        '<polygon points="86,178 170,178 160,236 96,236" fill="%s"/>'
        '<rect x="78" y="164" width="100" height="18" rx="4" fill="%s"/>'
        '<ellipse cx="128" cy="166" rx="46" ry="4" fill="%s"/>' % (POT, POT_RIM, SOIL)
    )


def svg(body, front=""):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">'
        f'<circle cx="128" cy="128" r="126" fill="{BG}"/>{body}{pot()}{front}</svg>\n'
    )


def leafy():
    parts = []
    for i, (ang, ln) in enumerate([(-62, 72), (-38, 92), (-14, 104), (12, 100), (36, 90), (60, 70)]):
        x, y = tip(ang, ln * 0.45)
        parts.append(stem(128, 168, x, y))
        parts.append(leaf(x, y, ln * 0.7, 20, ang, GREEN if i % 2 else GREEN_DARK))
    return svg("".join(parts))


def monstera():
    parts = []
    for i, (ang, ln) in enumerate([(-50, 110), (-15, 130), (25, 120), (55, 95)]):
        x, y = tip(ang, ln * 0.55)
        parts.append(stem(128, 168, x, y, width=4, bend=ang / 4))
        parts.append(leaf(x, y, 62, 36, ang, GREEN_DARK if i % 2 else GREEN, rib=True))
        # split-leaf notches
        for j in range(1, 4):
            d = 62 * j / 4.2
            for side in (-1, 1):
                parts.append(
                    f'<g transform="translate({x:.1f},{y:.1f}) rotate({ang:.1f})">'
                    f'<path d="M{side * 34},{-d - 4} L{side * 12},{-d - 1}" stroke="{BG}" stroke-width="4" stroke-linecap="round"/></g>'
                )
    return svg("".join(parts))


def trailing():
    parts = []
    vines = [(-1, 60, 228), (-1, 30, 210), (1, 62, 226), (1, 34, 205), (-1, 8, 150), (1, 10, 140)]
    for side, spread, drop in vines:
        x0 = 128 + side * 30
        x1 = 128 + side * (40 + spread)
        path = f"M{x0},168 C{x0 + side * 30},150 {x1},160 {x1},{drop}"
        parts.append(f'<path d="{path}" stroke="{GREEN_DARK}" stroke-width="2.5" fill="none"/>')
        for k in range(1, 6):
            t = k / 6
            # cubic bezier point
            px = (1 - t) ** 3 * x0 + 3 * (1 - t) ** 2 * t * (x0 + side * 30) + 3 * (1 - t) * t ** 2 * x1 + t ** 3 * x1
            py = (1 - t) ** 3 * 168 + 3 * (1 - t) ** 2 * t * 150 + 3 * (1 - t) * t ** 2 * 160 + t ** 3 * drop
            parts.append(leaf(px, py, 18, 10, side * (70 + k * 15), GREEN_LIGHT if k % 2 else GREEN, rib=False))
    for ang in (-40, -15, 10, 35):
        x, y = tip(ang, 30)
        parts.append(stem(128, 168, x, y, width=2.5))
        parts.append(leaf(x, y, 30, 14, ang, GREEN))
    # the vines hang down in front of the pot
    return svg("".join(parts[-8:]), front="".join(parts[:-8]))


def upright():
    parts = []
    for i, (ang, ln) in enumerate([(-22, 120), (-10, 140), (2, 150), (14, 132), (26, 110), (-4, 100)]):
        parts.append(
            f'<g transform="translate({128 + ang * 0.6:.1f},170) rotate({ang:.1f})">'
            f'<path d="M-9,0 C-12,{-ln * 0.5} -6,{-ln * 0.9} 0,{-ln} C6,{-ln * 0.9} 12,{-ln * 0.5} 9,0 Z" fill="{GREEN_DARK if i % 2 else GREEN}" stroke="#c9c46a" stroke-width="2"/>'
            f'<path d="M-5,{-ln * 0.2} L5,{-ln * 0.25} M-6,{-ln * 0.45} L6,{-ln * 0.5} M-5,{-ln * 0.7} L5,{-ln * 0.72}" stroke="{GREEN_LIGHT}" stroke-width="2"/></g>'
        )
    return svg("".join(parts))


def succulent():
    parts = []
    cx, cy = 128, 160
    for ring, (count, ln, w, col) in enumerate([(9, 72, 22, "#6fa596"), (7, 54, 18, "#86bba9"), (5, 34, 13, "#a3d1bf")]):
        for k in range(count):
            ang = -90 + 180 * k / (count - 1) + ring * 6
            parts.append(leaf(cx, cy, ln, w, ang, col, rib=False))
    return svg("".join(parts))


def cactus():
    col = "#4f9a5a"
    body = (
        f'<rect x="108" y="58" width="40" height="112" rx="20" fill="{col}"/>'
        f'<path d="M108,120 L88,120 Q78,120 78,110 L78,86" stroke="{col}" stroke-width="18" fill="none" stroke-linecap="round"/>'
        f'<path d="M148,104 L166,104 Q176,104 176,94 L176,74" stroke="{col}" stroke-width="18" fill="none" stroke-linecap="round"/>'
        '<path d="M120,66 L120,164 M128,60 L128,166 M136,66 L136,164" stroke="#3d7f48" stroke-width="2"/>'
        '<circle cx="128" cy="56" r="7" fill="#e86a8a"/>'
    )
    spines = "".join(
        f'<path d="M{x},{y} l-4,-3 M{x},{y} l4,-3" stroke="#f5f0d0" stroke-width="1.2"/>'
        for x, y in [(116, 80), (140, 92), (116, 108), (140, 128), (116, 140), (128, 74), (84, 98), (172, 86)]
    )
    return svg(body + spines)


def frond(x, y, ang, ln, col, leaflet_len=14, leaflet_w=4, curve=18):
    out = []
    a = math.radians(ang)
    ex, ey = x + math.sin(a) * ln, y - math.cos(a) * ln
    cx = (x + ex) / 2 + math.cos(a) * curve * (1 if ang >= 0 else -1)
    cy = (y + ey) / 2 - abs(math.sin(a)) * curve * 0.2
    out.append(f'<path d="M{x},{y} Q{cx:.1f},{cy:.1f} {ex:.1f},{ey:.1f}" stroke="{GREEN_DARK}" stroke-width="2" fill="none"/>')
    n = 9
    for k in range(1, n + 1):
        t = k / (n + 1)
        px = (1 - t) ** 2 * x + 2 * (1 - t) * t * cx + t ** 2 * ex
        py = (1 - t) ** 2 * y + 2 * (1 - t) * t * cy + t ** 2 * ey
        size = leaflet_len * (1.1 - t * 0.6)
        for side in (-1, 1):
            out.append(leaf(px, py, size, leaflet_w, ang + side * 60, col, rib=False))
    return "".join(out)


def fern():
    parts = [
        frond(128, 168, ang, ln, GREEN if i % 2 else GREEN_LIGHT, curve=26)
        for i, (ang, ln) in enumerate([(-75, 92), (-48, 105), (-20, 112), (8, 115), (34, 108), (62, 98), (82, 84)])
    ]
    return svg("".join(parts))


def palm():
    parts = []
    for i, (ang, ln) in enumerate([(-40, 128), (-14, 140), (12, 138), (38, 124)]):
        parts.append(frond(128, 168, ang, ln, GREEN_DARK if i % 2 else GREEN, leaflet_len=24, leaflet_w=3.5, curve=30))
    return svg("".join(parts))


def tree():
    parts = [
        '<path d="M128,168 L128,92 M128,128 L104,104 M128,116 L152,92" stroke="#7a5236" stroke-width="7" fill="none" stroke-linecap="round"/>'
    ]
    spots = [(104, 104, -60), (98, 86, -25), (118, 70, -10), (140, 66, 15), (156, 86, 40), (152, 92, 70),
             (128, 92, 0), (112, 118, -80), (144, 112, 75), (130, 52, 5), (108, 62, -40), (160, 70, 30)]
    for i, (x, y, ang) in enumerate(spots):
        parts.append(leaf(x, y, 40, 17, ang, GREEN_DARK if i % 3 == 0 else GREEN))
    return svg("".join(parts))


def lily():
    parts = []
    for i, (ang, ln) in enumerate([(-58, 86), (-30, 104), (-6, 110), (22, 104), (50, 88)]):
        x, y = tip(ang, ln * 0.4)
        parts.append(stem(128, 168, x, y))
        parts.append(leaf(x, y, ln * 0.65, 18, ang, GREEN_DARK))
    for ang, ln in [(-18, 132), (14, 124)]:
        x, y = tip(ang, ln)
        parts.append(stem(128, 168, x, y, color=GREEN, width=2.5))
        parts.append(leaf(x, y + 4, 34, 14, ang, "#fbfbf4", rib=False))
        parts.append(
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({ang:.1f})"><rect x="-2.5" y="-24" width="5" height="20" rx="2.5" fill="#efe18a"/></g>'
        )
    return svg("".join(parts))


def flower(x, y, r, petal, centre="#f6d34a"):
    out = "".join(
        f'<circle cx="{x + math.cos(math.radians(a)) * r:.1f}" cy="{y + math.sin(math.radians(a)) * r:.1f}" r="{r:.1f}" fill="{petal}"/>'
        for a in range(0, 360, 72)
    )
    return out + f'<circle cx="{x}" cy="{y}" r="{r * 0.7:.1f}" fill="{centre}"/>'


def orchid():
    parts = [
        leaf(128, 166, 52, 18, -70, GREEN_DARK),
        leaf(128, 166, 56, 18, 72, GREEN),
        leaf(128, 166, 44, 16, -35, GREEN),
        '<path d="M132,164 C134,110 150,70 186,62" stroke="#5c7c45" stroke-width="3" fill="none"/>',
    ]
    for x, y, r in [(146, 92, 11), (162, 74, 12), (184, 64, 10), (138, 116, 9)]:
        parts.append(flower(x, y, r, "#e9a6d0", centre="#c43d7f"))
    return svg("".join(parts))


def herb():
    parts = []
    for i, (ang, ln) in enumerate([(-45, 70), (-20, 90), (5, 96), (28, 88), (50, 66)]):
        x, y = tip(ang, ln)
        parts.append(stem(128, 168, x, y, color="#4d7a3a", width=2.5))
        for k in range(1, 5):
            t = k / 4.5
            px, py = 128 + (x - 128) * t, 168 + (y - 168) * t
            for side in (-1, 1):
                parts.append(leaf(px, py, 18, 9, ang + side * 55, GREEN_LIGHT if (i + k) % 2 else GREEN, rib=False))
        parts.append(leaf(x, y, 20, 10, ang, GREEN_LIGHT, rib=False))
    return svg("".join(parts))


def zz():
    parts = []
    for i, (ang, ln) in enumerate([(-30, 110), (-12, 130), (6, 138), (24, 120), (40, 96)]):
        x, y = tip(ang, ln)
        parts.append(stem(128, 168, x, y, color="#3c5a2c", width=4))
        for k in range(2, 8):
            t = k / 8
            px, py = 128 + (x - 128) * t, 168 + (y - 168) * t
            for side in (-1, 1):
                parts.append(leaf(px, py, 20, 8, ang + side * 50, "#2f7a3e" if k % 2 else "#3f9150", rib=False))
        parts.append(leaf(x, y, 18, 8, ang, "#3f9150", rib=False))
    return svg("".join(parts))


def calathea():
    parts = []
    for i, (ang, ln) in enumerate([(-55, 100), (-28, 118), (0, 126), (28, 116), (55, 98)]):
        x, y = tip(ang, ln * 0.45)
        parts.append(stem(128, 168, x, y, color="#6b3b5a"))
        lx, ly = x, y
        parts.append(leaf(lx, ly, ln * 0.6, 24, ang, "#356b46"))
        parts.append(
            f'<g transform="translate({lx:.1f},{ly:.1f}) rotate({ang:.1f})">'
            + "".join(
                f'<path d="M0,{-ln * 0.6 * t:.1f} l{s * 15},{-6}" stroke="#a8d39b" stroke-width="3" stroke-linecap="round"/>'
                for t in (0.25, 0.42, 0.59, 0.76)
                for s in (-1, 1)
            )
            + "</g>"
        )
    return svg("".join(parts))


def spider():
    parts = []
    for ang in range(-80, 81, 16):
        side = 1 if ang >= 0 else -1
        ex = 128 + side * (12 + abs(ang) * 0.95)
        ey = 72 + abs(ang) * 1.05
        cx, cy = 128 + (ex - 128) * 0.35, min(ey, 100) - 30
        for colr, w in ((GREEN, 7), ("#f1f0d2", 2)):
            parts.append(f'<path d="M128,168 Q{cx:.1f},{cy:.1f} {ex:.1f},{ey:.1f}" stroke="{colr}" stroke-width="{w}" fill="none" stroke-linecap="round"/>')
    # a baby plantlet on a runner
    parts.append('<path d="M150,166 C200,130 214,170 206,206" stroke="#c9c58f" stroke-width="2" fill="none"/>')
    for ang in (-40, -10, 20, 50):
        parts.append(leaf(206, 206, 16, 3, ang, GREEN, rib=False))
    return svg("".join(parts))


def flowering():
    parts = []
    for i, (ang, ln) in enumerate([(-70, 60), (-45, 66), (-15, 62), (15, 62), (45, 66), (70, 60)]):
        parts.append(leaf(128, 166, ln, 22, ang, GREEN_DARK if i % 2 else GREEN, rib=True))
    for x, y in [(106, 106), (128, 96), (150, 108), (118, 120), (140, 122)]:
        parts.append(stem(128, 160, x, y, color=GREEN, width=2))
        parts.append(flower(x, y, 7, "#9b6ad6"))
    return svg("".join(parts))


ARCHETYPES = {
    "leafy": leafy,
    "monstera": monstera,
    "trailing": trailing,
    "upright": upright,
    "succulent": succulent,
    "cactus": cactus,
    "fern": fern,
    "palm": palm,
    "tree": tree,
    "lily": lily,
    "orchid": orchid,
    "herb": herb,
    "zz": zz,
    "calathea": calathea,
    "spider": spider,
    "flowering": flowering,
}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in ARCHETYPES.items():
        (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
        print("wrote", name)
