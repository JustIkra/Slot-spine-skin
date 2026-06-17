#!/usr/bin/env python3
"""
px_to_skel.py — convert pixel placement on a square symbol canvas to Spine bone
coords + attachment size, for the pixi-spine 3.8 slot rig.

Mapping (y up in Spine):
    bx = (px/C - 0.5) * S
    by = (0.5 - py/C) * S
    attachment_size = dim_px / C * S

Usage:
    # bone at pixel center (200,68) of a 400px symbol, skeleton width 311,
    # part 150x150 px:
    python3 px_to_skel.py --canvas 400 --skel 311 --center 200 68 --size 150 150

    # child bone: give parent center to get LOCAL coords (parent has scale 1, rot 0):
    python3 px_to_skel.py --canvas 400 --skel 311 --center 200 58 --parent-center 200 205
"""
import argparse


def to_skel(px, py, C, S):
    return (px / C - 0.5) * S, (0.5 - py / C) * S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canvas", type=float, default=400.0, help="symbol canvas px (square)")
    ap.add_argument("--skel", type=float, default=311.0, help="skeleton width/height")
    ap.add_argument("--center", type=float, nargs=2, required=True, metavar=("PX", "PY"),
                    help="part center in canvas pixels")
    ap.add_argument("--size", type=float, nargs=2, metavar=("W", "H"),
                    help="part size in canvas pixels -> attachment width/height")
    ap.add_argument("--parent-center", type=float, nargs=2, metavar=("PX", "PY"),
                    help="if child bone, parent center px -> prints LOCAL bone coords")
    a = ap.parse_args()

    bx, by = to_skel(a.center[0], a.center[1], a.canvas, a.skel)
    if a.parent_center:
        pbx, pby = to_skel(a.parent_center[0], a.parent_center[1], a.canvas, a.skel)
        print(f"bone (LOCAL to parent): x={bx - pbx:.2f}  y={by - pby:.2f}")
        print(f"  (world: x={bx:.2f} y={by:.2f}; parent world x={pbx:.2f} y={pby:.2f})")
    else:
        print(f"bone: x={bx:.2f}  y={by:.2f}")
    if a.size:
        f = a.skel / a.canvas
        print(f"attachment: width={a.size[0]*f:.2f}  height={a.size[1]*f:.2f}")


if __name__ == "__main__":
    main()
