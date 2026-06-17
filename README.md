# slot-spine-skin

A Claude skill for turning a **flat, pre-baked slot symbol** (one finished PNG — frame +
character + sun + plaque + background) into a **multi-part Spine 2D rig** animated for the
**pixi-spine 3.8** runtime used by Urso / `@zephyr/slot-base` slot engines.

It is the distilled, reusable version of a full production reskin where a static "WILD"
icon was turned into a win/landing/idle animation: the character grows, the sun spins and
rises, a "WILD" plaque throbs, light bursts from inside out, the eyes glow and a shine
sweeps across the character.

## Read first
- `SKILL.md` — the playbook (the hard rules + the pipeline).
- `references/pixi-spine-3.8.md` — the JSON format that actually parses (scalar curves!).
- `references/cutting-with-gemini.md` — how to cut components cleanly (magenta + chroma).
- `references/video-to-sequence.md` — coherent motion (opening/leafing/morph) via image-to-video → attachment sequence.
- `references/rigging-and-animation.md` — bone layout, no-hole rules, win/landing/idle recipes,
  FX sequences.

## Tools (`scripts/`)
| script | what |
|---|---|
| `preview_spine.py` | spine-3.8-lite offline renderer → contact sheet of an animation (verify before the game). |
| `build_fx_sequence.py` | generate the eyes-glow + shine-sweep FX frame sequence (additive overlay). |
| `px_to_skel.py` | pixel placement → Spine bone coords + attachment size. |

Image generation / background removal is delegated to the **slot-gen** skill
(`openrouter_image.py`, `chroma_key.py`, `recolor_lut.py`). Set `export SLOTGEN=…/slot-gen/scripts`.

## Quick start
```bash
pip install -r requirements.txt --break-system-packages -q
export SLOTGEN="$HOME/.claude/skills/slot-gen/scripts"

# 1. cut parts (see references/cutting-with-gemini.md), put PNGs in parts/
# 2. build wild.json (3.8 scalar curves!) with help from px_to_skel.py
# 3. FX sequence:
python3 scripts/build_fx_sequence.py --char parts/wild_char.png --eyes 120,134 180,134 \
    --frames 14 --out-dir parts/ --prefix wild_fx_ --preview .tmp_<symbol>/fx.png
# 4. PREVIEW before the game:
python3 scripts/preview_spine.py --spine wild.json --parts-dir parts/ \
    --canvas 400 --skel 311 --anim win --out .tmp_<symbol>/win.png
# 5. build: yarn assets:build && yarn assets:copy && yarn build:dev
```

## The one rule that wastes the most time
pixi-spine **3.8** wants the curve as **four scalars** — `"curve":0.25,"c2":0,"c3":0.75,"c4":1` —
NOT the Spine 4.x array `"curve":[…]`. The array form → NaN → invisible parts. Don't copy 4.x
examples (most of the web, including context7).
