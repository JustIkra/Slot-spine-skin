#!/usr/bin/env python3
"""
preview_spine.py — a Spine 4.2 subset offline renderer for slot-symbol rigs.

Reads Spine 4.2 JSON plus a directory of part PNGs and renders a contact sheet of a
chosen animation, so you can catch ghosts / holes / timing BEFORE the slow in-game
loop. Supports: array bezier curves, the bone hierarchy (translate/rotate/scale),
slot draw order, additive slots (`alpha` or `rgba` timelines), and the
attachment-swap frame sequence.

Frame name -> file mapping: region "png/wild_egypt_sun" -> <parts-dir>/wild_egypt_sun.png
(takes the last path segment + ".png").

Usage:
    python3 preview_spine.py --spine wild.json --parts-dir parts/ \
        --canvas 400 --skel 311 --anim win --cols 6 --rows 2 --out /tmp/win.png

Notes / limitations: region attachments only (no mesh/deform); rotation uses PIL
(approximate AA); good enough to validate motion, coverage and timing.
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image


# ---------- timeline evaluation ----------
def bez(p1x, p1y, p2x, p2y, t):
    lo, hi = 0.0, 1.0
    for _ in range(22):
        m = (lo + hi) / 2
        x = 3 * (1 - m) ** 2 * m * p1x + 3 * (1 - m) * m * m * p2x + m ** 3
        if x < t:
            lo = m
        else:
            hi = m
    m = (lo + hi) / 2
    return 3 * (1 - m) ** 2 * m * p1y + 3 * (1 - m) * m * m * p2y + m ** 3


def curve_value(key, channel, t, t0=0, t1=1, v0=0, v1=1):
    curve = key.get("curve")
    if curve == "stepped":
        return v0
    if curve is None:
        return v0 + (v1-v0)*t
    if not isinstance(curve, list):
        raise ValueError("Spine 4.2 bezier curve must be an array")
    offset = channel * 4
    points = curve[offset:offset + 4]
    if len(points) != 4:
        raise ValueError("Spine 4.2 bezier curve needs four values per animated channel")
    x1, y1, x2, y2 = points
    lo, hi = 0.0, 1.0
    for _ in range(30):
        u = (lo+hi)/2
        x = (1-u)**3*t0 + 3*(1-u)**2*u*x1 + 3*(1-u)*u*u*x2 + u**3*t1
        if x < t0 + (t1-t0)*t:
            lo = u
        else:
            hi = u
    u = (lo+hi)/2
    return (1-u)**3*v0 + 3*(1-u)**2*u*y1 + 3*(1-u)*u*u*y2 + u**3*v1


def ev(keys, t, field, default=0.0, channel=0):
    if not keys:
        return default

    def g(k):
        return k.get(field, default)

    if t <= keys[0]["time"]:
        return g(keys[0])
    if t >= keys[-1]["time"]:
        return g(keys[-1])
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a["time"] <= t <= b["time"]:
            span = b["time"] - a["time"]
            lt = (t - a["time"]) / span if span else 0.0
            if a.get("curve") == "stepped":
                return g(a)
            return curve_value(a, channel, lt, a["time"], b["time"], g(a), g(b))
    return g(keys[-1])


def ev_attachment(keys, t):
    name = None
    for e in keys:
        if e["time"] <= t:
            name = e.get("name")
        else:
            break
    return name


def ev_rgba_alpha(keys, t, default=1.0):
    """RRGGBBAA timeline -> alpha 0..1."""
    if not keys:
        return default
    def aa(k):
        return int(k["color"][6:8], 16) / 255.0
    if t <= keys[0]["time"]:
        return aa(keys[0])
    if t >= keys[-1]["time"]:
        return aa(keys[-1])
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        if a["time"] <= t <= b["time"]:
            span = b["time"] - a["time"]
            lt = (t - a["time"]) / span if span else 0.0
            if a.get("curve") == "stepped":
                return aa(a)
            return curve_value(a, 3, lt, a["time"], b["time"], aa(a), aa(b))
    return aa(keys[-1])


# ---------- skeleton ----------
def world_transforms(spine, anim, t):
    """Return {bone: (wx, wy, wrot_deg, wsx, wsy)} in skeleton units."""
    bones = spine["bones"]
    abones = anim.get("bones", {})
    out = {}
    for b in bones:  # JSON is parent-before-child by Spine convention
        name = b["name"]
        sx0, sy0 = b.get("x", 0.0), b.get("y", 0.0)
        srot = b.get("rotation", 0.0)
        ssx, ssy = b.get("scaleX", 1.0), b.get("scaleY", 1.0)
        tl = abones.get(name, {})
        tx = ev(tl.get("translate", []), t, "x", 0.0, 0)
        ty = ev(tl.get("translate", []), t, "y", 0.0, 1)
        ang = ev(tl.get("rotate", []), t, "value", 0.0)
        ascx = ev(tl.get("scale", []), t, "x", 1.0, 0)
        ascy = ev(tl.get("scale", []), t, "y", 1.0, 1)
        lx, ly = sx0 + tx, sy0 + ty
        lrot = srot + ang
        lsx, lsy = ssx * ascx, ssy * ascy
        parent = b.get("parent")
        if parent is None:
            out[name] = (lx, ly, lrot, lsx, lsy)
        else:
            pwx, pwy, pwr, psx, psy = out[parent]
            cr, sr = math.cos(math.radians(pwr)), math.sin(math.radians(pwr))
            wx = pwx + cr * (psx * lx) - sr * (psy * ly)
            wy = pwy + sr * (psx * lx) + cr * (psy * ly)
            out[name] = (wx, wy, pwr + lrot, psx * lsx, psy * lsy)
    return out


def region_props(skin, slot_name, region_name):
    s = skin.get(slot_name, {})
    return s.get(region_name, {})


def part_path(parts_dir, region_name):
    return os.path.join(parts_dir, region_name.split("/")[-1] + ".png")


def composite_add(canvas, tex, cx, cy, alpha):
    ta = np.asarray(tex).astype(np.float32)
    a = (ta[..., 3:] / 255.0) * alpha
    arr = np.asarray(canvas).astype(np.float32)
    W, H = canvas.size
    x0, y0 = int(cx - tex.width / 2), int(cy - tex.height / 2)
    gx0, gy0 = max(x0, 0), max(y0, 0)
    gx1, gy1 = min(x0 + tex.width, W), min(y0 + tex.height, H)
    if gx1 <= gx0 or gy1 <= gy0:
        return canvas
    sx0, sy0 = gx0 - x0, gy0 - y0
    arr[gy0:gy1, gx0:gx1, :3] = np.clip(
        arr[gy0:gy1, gx0:gx1, :3]
        + ta[sy0:sy0 + (gy1 - gy0), sx0:sx0 + (gx1 - gx0), :3]
        * a[sy0:sy0 + (gy1 - gy0), sx0:sx0 + (gx1 - gx0)], 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def render_frame(spine, anim, t, parts, skin, C, S, bg):
    f = C / S
    cx0, cy0 = C / 2, C / 2
    wt = world_transforms(spine, anim, t)
    aslots = anim.get("slots", {})
    canvas = Image.new("RGBA", (C, C), (*bg, 255))
    for slot in spine["slots"]:
        sname = slot["name"]
        bone = slot["bone"]
        if bone not in wt:
            continue
        atl = aslots.get(sname, {})
        # attachment: setup or swap timeline
        region = slot.get("attachment")
        if "attachment" in atl:
            region = ev_attachment(atl["attachment"], t)
        if not region:
            continue
        img = parts.get(region)
        if img is None:
            raise ValueError(f"Missing attachment texture: {region}")
        props = region_props(skin, sname, region)
        aw = props.get("width", img.width)
        ah = props.get("height", img.height)
        ax = props.get("x", 0.0)
        ay = props.get("y", 0.0)
        arot = props.get("rotation", 0.0)
        wx, wy, wr, wsx, wsy = wt[bone]
        # attachment center in skeleton units
        cr, sr = math.cos(math.radians(wr)), math.sin(math.radians(wr))
        acx = wx + cr * (wsx * ax) - sr * (wsy * ay)
        acy = wy + sr * (wsx * ax) + cr * (wsy * ay)
        # to canvas px
        px = cx0 + acx * f
        py = cy0 - acy * f
        rw = max(1, int(aw * abs(wsx) * f))
        rh = max(1, int(ah * abs(wsy) * f))
        tex = img.resize((rw, rh), Image.LANCZOS)
        rot = wr + arot
        if abs(rot) > 0.01:
            tex = tex.rotate(rot, resample=Image.BICUBIC, expand=True)
        setup_alpha = int(slot.get("color", "ffffffff")[6:8], 16) / 255.0
        if "alpha" in atl:
            alpha = ev(atl["alpha"], t, "value", setup_alpha)
        else:
            alpha = ev_rgba_alpha(atl.get("rgba", []), t, setup_alpha)
        if slot.get("blend") == "additive":
            canvas = composite_add(canvas, tex, px, py, alpha)
        else:
            if alpha < 0.999:
                a2 = np.asarray(tex).astype(np.float32)
                a2[..., 3] *= alpha
                tex = Image.fromarray(a2.astype(np.uint8))
            canvas.alpha_composite(tex, (int(px - tex.width / 2), int(py - tex.height / 2)))
    out = Image.new("RGB", (C, C), bg)
    out.paste(canvas, (0, 0), canvas)
    return out


def validate_subset(spine, anim):
    for constraint in ("ik", "transform", "path", "physics"):
        if spine.get(constraint):
            raise ValueError("Use runtime preview for constraints")
    for bone in spine.get("bones", []):
        if bone.get("inherit", "normal") != "normal" or bone.get("shearX", 0) or bone.get("shearY", 0):
            raise ValueError("Use runtime preview for bone inheritance/shear")
        if bone.get("scaleX", 1) != 1 or bone.get("scaleY", 1) != 1:
            raise ValueError("Use runtime preview for setup bone scaling")
    for skin in spine.get("skins", []):
        for attachments in skin.get("attachments", {}).values():
            for attachment in attachments.values():
                if attachment.get("type", "region") != "region" or attachment.get("sequence"):
                    raise ValueError("Use runtime preview for mesh/deform/sequence attachments")
    if set(anim) - {"bones", "slots"}:
        raise ValueError("Unsupported subset animation; use runtime preview")
    for timelines in anim.get("bones", {}).values():
        if set(timelines) - {"rotate", "translate"}:
            raise ValueError("Use runtime preview for scale/shear timelines")
    for slot in spine.get("slots", []):
        if slot.get("color", "ffffffff")[:6].lower() != "ffffff" or slot.get("blend", "normal") not in ("normal", "additive"):
            raise ValueError("Use runtime preview for tint and advanced blend modes")
    for timelines in anim.get("slots", {}).values():
        if set(timelines) - {"attachment", "alpha"}:
            raise ValueError("Use runtime preview for animated color")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine", required=True)
    ap.add_argument("--parts-dir", required=True)
    ap.add_argument("--anim", default="win")
    ap.add_argument("--canvas", type=int, default=400)
    ap.add_argument("--skel", type=float, default=311.0)
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--cell", type=int, default=150)
    ap.add_argument("--bg", default="45,33,16", help="sheet bg RGB")
    ap.add_argument("--duration", type=float, default=0.0, help="override (0 = auto)")
    ap.add_argument("--out", default="/tmp/spine_preview.png")
    a = ap.parse_args()

    spine = json.load(open(a.spine))
    if a.anim not in spine["animations"]:
        raise SystemExit(f"animation '{a.anim}' not in {list(spine['animations'])}")
    anim = spine["animations"][a.anim]
    validate_subset(spine, anim)
    skin = spine["skins"][0]["attachments"]

    # load all referenced parts
    parts = {}
    needed = set()
    for slot, atts in skin.items():
        for region in atts:
            needed.add(region)
    for region in needed:
        p = part_path(a.parts_dir, region)
        if os.path.exists(p):
            parts[region] = Image.open(p).convert("RGBA")
        else:
            raise SystemExit(f"Missing part for region '{region}': {p}")

    # duration = max key time
    dur = a.duration
    if dur <= 0:
        for tl in anim.get("bones", {}).values():
            for arr in tl.values():
                dur = max(dur, arr[-1]["time"])
        for tl in anim.get("slots", {}).values():
            for arr in tl.values():
                dur = max(dur, arr[-1]["time"])
        dur = dur or 1.0

    n = a.cols * a.rows
    bg = tuple(int(v) for v in a.bg.split(","))
    sheet = Image.new("RGB", (a.cols * a.cell, a.rows * a.cell), bg)
    for i in range(n):
        t = dur * i / (n - 1) if n > 1 else 0.0
        fr = render_frame(spine, anim, t, parts, skin, a.canvas, a.skel, bg)
        sheet.paste(fr.resize((a.cell, a.cell)), ((i % a.cols) * a.cell, (i // a.cols) * a.cell))
    sheet.save(a.out)
    print(f"anim '{a.anim}' dur={dur:.2f}s -> {a.out}  ({n} frames)")


if __name__ == "__main__":
    main()
