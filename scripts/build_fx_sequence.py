#!/usr/bin/env python3
"""
build_fx_sequence.py — generate a frame sequence (additive FX overlay) for a slot
character: glow emanating from the eyes + a shine/gleam that sweeps across the
character, masked to the character silhouette.

Frames are built procedurally on transparent canvas (same size as the character PNG)
so they are perfectly coherent (the base art never "breathes"). Drive them in Spine
via a slot ATTACHMENT timeline on an additive slot sharing the character's bone.

Output: <out-dir>/<prefix>00.png .. <prefix>(N-1).png  + a contact-sheet preview.

Usage:
    python3 build_fx_sequence.py --char wild_char.png \
        --eyes 120,134 180,134 --frames 14 \
        --out-dir parts/ --prefix wild_fx_ --preview /tmp/fx.png

Each frame: additive RGBA where alpha = light intensity, RGB = light colour.
"""
import argparse
import math
import os

import numpy as np
from PIL import Image


def build(char_path, eyes, n, color, angle_deg, eye_radius, shine_sigma,
          eye_gain, shine_gain):
    char = Image.open(char_path).convert("RGBA")
    W, H = char.size
    calpha = np.asarray(char)[..., 3].astype(np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = math.radians(angle_deg)
    proj = xx * math.cos(a) + yy * math.sin(a)
    pmin, pmax = float(proj.min()), float(proj.max())

    frames = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        fx = np.zeros((H, W, 4), np.float32)

        # eyes: rise -> fall over the first ~85% of the sequence
        eg = max(math.sin(min(t / 0.85, 1.0) * math.pi), 0.0) * eye_gain
        for (ex, ey) in eyes:
            d2 = (xx - ex) ** 2 + (yy - ey) ** 2
            core = np.exp(-d2 / (2 * eye_radius ** 2))
            halo = np.exp(-d2 / (2 * (eye_radius * 2.2) ** 2)) * 0.5
            beam = (np.exp(-((xx - ex) ** 2) / (2 * (eye_radius * 0.7) ** 2))
                    * np.exp(-((yy - (ey - eye_radius * 2.3)) ** 2) / (2 * (eye_radius * 2.6) ** 2)) * 0.6)
            fx[..., 3] += (core + halo + beam) * eg

        # shine band sweeping across, clipped to the character silhouette
        st = (t - 0.12) / 0.8
        if 0.0 <= st <= 1.0:
            pos = pmin + (pmax - pmin) * st
            band = np.exp(-((proj - pos) ** 2) / (2 * shine_sigma ** 2)) * shine_gain
            fx[..., 3] += band * calpha * math.sin(st * math.pi)

        fx[..., 3] = np.clip(fx[..., 3], 0.0, 1.0) * 255.0
        fx[..., 0], fx[..., 1], fx[..., 2] = color
        frames.append(Image.fromarray(fx.astype(np.uint8), "RGBA"))
    return char, frames


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--char", required=True, help="character PNG (transparent)")
    ap.add_argument("--eyes", nargs="+", required=True, metavar="X,Y",
                    help="eye centers, e.g. --eyes 120,134 180,134")
    ap.add_argument("--frames", type=int, default=14)
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--prefix", default="wild_fx_")
    ap.add_argument("--color", default="255,240,190", help="light RGB")
    ap.add_argument("--angle", type=float, default=62.0, help="shine band angle (deg)")
    ap.add_argument("--eye-radius", type=float, default=13.0)
    ap.add_argument("--shine-sigma", type=float, default=16.0)
    ap.add_argument("--eye-gain", type=float, default=0.85)
    ap.add_argument("--shine-gain", type=float, default=0.85)
    ap.add_argument("--preview", default=None, help="optional contact-sheet path")
    a = ap.parse_args()

    eyes = [tuple(float(v) for v in e.split(",")) for e in a.eyes]
    color = tuple(int(v) for v in a.color.split(","))
    char, frames = build(a.char, eyes, a.frames, color, a.angle, a.eye_radius,
                         a.shine_sigma, a.eye_gain, a.shine_gain)

    os.makedirs(a.out_dir, exist_ok=True)
    for i, f in enumerate(frames):
        f.save(os.path.join(a.out_dir, f"{a.prefix}{i:02d}.png"))
    print(f"wrote {len(frames)} frames -> {a.out_dir}/{a.prefix}NN.png")

    if a.preview:
        W, H = char.size
        cols = min(7, len(frames))
        rows = (len(frames) + cols - 1) // cols
        cell = 110
        sheet = Image.new("RGB", (cols * cell, rows * cell), (22, 16, 8))
        for i, f in enumerate(frames):
            bg = Image.new("RGBA", (W, H), (25, 18, 8, 255))
            bg.alpha_composite(char)
            arr = np.asarray(bg).astype(np.float32)
            fa = np.asarray(f).astype(np.float32)
            al = fa[..., 3:] / 255.0
            arr[..., :3] = np.clip(arr[..., :3] + fa[..., :3] * al, 0, 255)
            prev = Image.fromarray(arr.astype(np.uint8)).convert("RGB").resize((cell, cell))
            sheet.paste(prev, ((i % cols) * cell, (i // cols) * cell))
        sheet.save(a.preview)
        print(f"preview -> {a.preview}")


if __name__ == "__main__":
    main()
