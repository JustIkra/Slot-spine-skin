# Rigging & animation recipes (slot symbol)

## Coordinate mapping (px ↔ skeleton)

Symbol canvas `C` px square, skeleton width `S` (commonly 400 → 311). y is **up** in Spine.
```
bx = (px/C − 0.5) · S      by = (0.5 − py/C) · S      attachment_size = dim_px/C · S
```
`scripts/px_to_skel.py` prints bone x/y + attachment width/height from pixel placement.

## Layering (the proven slot rig)

```
bones:
  root
   ├ rays   (parent root, at symbol/char centre)
   ├ char   (parent root, at character centre)        ← scales = "character grows"
   │  └ sun (parent CHAR, at sun centre)              ← rises + scales WITH the character
   └ wild   (parent root, at plaque centre)

slots (draw order, back → front):
  base/фон                  bone root         (background panel, transparent outside window)
  rays      additive        bone rays         (light from inside out, hidden at setup)
  char                      bone char
  charfx    additive seq    bone char         (eyes glow + shine sweep, hidden at setup)
  frame                     bone root         (STATIC, on top → clips the growing character)
  sun                       bone sun
  sun_glow  additive        bone sun          (glow tracks the spinning sun)
  wild                      bone wild         (throb)
```

Why these choices:
- **frame static & on top** → the enlarging character is clipped to the window; no overflow over
  hieroglyphs. (If you want a pop-OUT instead, put frame below the character.)
- **sun is a child of char** → "raise the sun higher because the character also grows" comes for
  free (parent scale lifts + scales the child). Only safe once the sun is **not** in the base
  (else the static base sun ghosts behind the moving one).
- **additive glow/rays** → second slot, `blend:"additive"`, setup `color:"ffffff00"`, animate AA.

## No-hole rules (re-stated, they cause every bug)
- A part over a base that STILL contains that element → keep the part `scale ≥ 1` (grow-only) and
  sized ≥ the base element, so it always covers it. (wild plaque, sun-in-place.)
- A part that must MOVE/spin/translate → remove that element from the base first (dark-fill or, far
  better, a Gemini gradient/background with no element), so there is nothing to ghost.
- A dark "fill" that pokes between a spinning part's rays reads as a black blob → don't dark-fill;
  remove the element cleanly or keep the original behind and fully cover it.

## Animation set & timings

| anim | length | content |
|---|---|---|
| `static` | — | `{}` empty. Holds the setup pose (the resting symbol). |
| `landing` | ~0.5 s | drop-in: char squash-settle `1→1.09→0.98→1`; sun rotate-kick `−30→0`; wild pop; quick rays flash + short FX shine. |
| `win` | ~2.0 s | the showcase (below). |
| `static_animated` | ~3.0 s | idle: char breath `1→1.012→1`; sun sway `0→9→−9→0`; faint rays. (Only for special symbols.) |

### `win` recipe (2.0 s)
- **char.scale** (grow, with in-betweens): `1 → 0.98(0.12) → 1.15(0.3) → 1.10(0.6) → 1.12(1.0) → 1.06(1.4) → 1.02(1.7) → 1(2.0)`.
- **sun.rotate** (full spin + settle): `0 → 170(0.3) → 330(0.8) → 390(1.3) → 355(1.7) → 360(2.0)` (overshoot then settle so it ends upright).
- **sun.scale**: subtle `1 → 1.1(0.15) → 1(0.5) → 1.06(0.9) → 1` (the char parent already enlarges it).
- **wild.scale** (throb, MANY in-betweens, always ≥1): `1 →1.12 →1.02 →1.09 →1.02 →1.07 →1.01 →1.04 →1`.
- **rays.scale** (burst outward = light inside-out): `0.6 → 1.4(0.2) → 1.05 → 1.3(1.0) → 1.05 → 0.7`.
- **rays.color** (additive): `00 → aa(0.15) → 55 → 88(0.8) → 44 → 28 → 00`.
- **sun_glow.color**: `00 → 55(0.2) → 22 → 44(1.0) → 18 → 00`.
- **charfx.attachment**: swap the FX sequence (see below), then `null`.
- **root.scale**: tiny whole-symbol life `1 → 1.03 → 1`.

All keys carry a scalar curve (`0.25,0,0.75,1`), except final keys (linear hold).

## FX frame sequence (eyes glow + shine sweep)

Real sprite sequence via a slot **attachment timeline** on an additive slot sharing the character's
bone (so FX scales/moves with the character). Frames built by `scripts/build_fx_sequence.py`:
- **Eye glow**: golden radial + a soft upward beam at each eye, intensity follows a rise→fall curve.
- **Shine sweep**: a diagonal gaussian band swept across, **multiplied by the character alpha** so it
  only glints on the symbol, not in empty space.
- Frames are on transparent, same canvas as the character → trim small in atlas, perfectly coherent.

Wire-up (skin + animation), 14 frames `png/wild_fx_00..13`:
```jsonc
"slots": [ /* … */ { "name":"png/charfx", "bone":"char", "blend":"additive" } ],   // no attachment = hidden
"skins":[{ "name":"default","attachments":{ "png/charfx":{
   "png/wild_fx_00":{"width":216.1,"height":233.25}, /* …_01.._13 same size … */ } }}],
"animations": { "win": { "slots": { "png/charfx": { "attachment": [
   {"time":0.12,"name":"png/wild_fx_00"}, {"time":0.22,"name":"png/wild_fx_01"}, /* … */
   {"time":1.42,"name":"png/wild_fx_13"}, {"time":1.52,"name":null} ] } } } }
```

### Playback speed of a sequence (fire/flame "too fast")
Attachment swaps are **stepped** (no tween), so perceived speed = swap rate (1/Δt between keys), set
**independently of the win duration**. To slow a flame/fire that reads as frantic WITHOUT shortening
the animation: don't cram every frame — **thin the frames** (play every 2nd: `_00,_02,_04,…`) and
**hold each longer** (Δt ≈ 0.09–0.13 s ⇒ ~8–11 fps reads calm; ≤0.05 s ⇒ ~20 fps reads frantic). For a
hold phase use a slow ping-pong of a few frames (`_17,_15,_17,_18,_16`) at ~0.13 s each rather than a
fast cycle of all of them. A real-motion video sequence (smile, torch flare) lands its key pose in the
**first half** by spacing the forward swaps, then dances a small frame subset for the rest.

### Scale only the character over a frame-BELOW it (pop-out)
For a "character grows out of the frame" win: put the frame slot UNDER the char (draw order), and give
the char its OWN bone (`char`, child of root) — animate `char.scale` (e.g. `1→1.13→1.06→1.11→1`) so
only the figure enlarges and overflows the frame; bg/frame stay on `root` and don't move. End back at
`1.0` so it settles into the neutral `static` pose with no pop. In-game overflow past the frame is
expected (the cell doesn't clip) and reads as energy — confirm the intent, it's a feature not a bug.

## Verify, then build
1. `scripts/preview_spine.py` → contact sheet. Look for: ghosts, holes, the part you expect to move
   actually moving, timing. Iterate here (fast).
2. `yarn assets:build` (textures) → `yarn assets:copy` (spine → bin) → `yarn build:dev` (webpack sanity).
3. In-game (`yarn start`) for the final read (additive + timing look different live).
