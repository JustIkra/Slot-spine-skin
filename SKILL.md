---
name: slot-spine-skin
description: >
  Turn a FLAT single-image slot symbol (a baked PNG: frame + character + sun + WILD
  plaque, etc.) into a multi-part Spine 2D rig animated for the pixi-spine 3.8 runtime
  (Urso / Zephyr slot engines). Use this skill whenever the user wants to "animate a
  slot symbol", "rig a wild/scatter/high symbol", "cut the symbol into moving parts",
  "make the character grow / the sun spin / a shine sweep / eyes glow", "add a win /
  landing / idle animation to a symbol", or "split a symbol into frame + character +
  background". It codifies: cutting components via Gemini (slot-gen) on magenta +
  chroma-key, pivot-bone rigging, the CRITICAL pixi-spine 3.8 scalar-curve format,
  component layering (background / frame-on-top-clip / additive glow / FX frame
  sequences), and offline PIL preview BEFORE running the game. Triggers also on
  "spine 3.8", "attachment swap sequence", "additive glow slot", "noAtlas spine".
user-invocable: true
---

# Slot Spine Skin

Animate a **flat, pre-baked slot symbol** by cutting it into components and rigging them
in Spine for the **pixi-spine 3.8** runtime (the one shipped inside Urso / `@zephyr/slot-base`).

This is **not** humanoid character rigging. The input is one finished PNG (a wild/scatter/high
symbol with a frame, a character, a sun disc, a "WILD" plaque, a background, …). The job is to
**separate those elements**, put each on its own bone, and animate them (grow, spin, throb,
glow, shine-sweep) so a static icon becomes a juicy win/landing/idle animation.

> Born from a full production reskin ("Book of Abydos"). Every rule below is a scar from that run.

## When to reach for this vs other skills

- **This skill** — flat slot symbol → cut into parts → pixi-spine **3.8** rig + win/landing/idle.
- `slot-gen` — the image backend (OpenRouter/Gemini generate, `chroma_key.py`, `recolor_lut.py`).
  This skill **calls** slot-gen scripts for every cut. Set its scripts dir in `SLOTGEN` (see below).
- `spine-animation` — generic humanoid cutout rig, **Spine 4.x array curves**. Do NOT copy its
  curve format here — 3.8 needs scalars (see below) or tokens vanish.

## Setup

```bash
pip install Pillow numpy --break-system-packages -q
# slot-gen scripts (image gen + chroma key). Adjust path to your install:
export SLOTGEN="$HOME/.claude/skills/slot-gen/scripts"
# OpenRouter / remove.bg keys live in ~/.claude/.env (OPENROUTER_KEY, REMOVEBG_API_KEY)
```

**Temp working folder — in the CURRENT/project directory, NOT `/tmp`.** Put every
intermediate (anchors, video mp4, extracted frames, keyed frames, contact-sheet
previews, packer/helper scripts) in `./.tmp_<symbol>/` at the repo root (e.g.
`.tmp_high2/`). Reason: the assets live in the repo, the helpers reference repo-relative
paths, and you want the scratch reviewable/diffable alongside the work — `/tmp` is
opaque and wiped. All `--out` / preview paths in this skill use `./.tmp_<symbol>/…`.

## The hard rules (read before touching JSON)

1. **pixi-spine 3.8 curve = FOUR SCALARS, never an array.**
   `{"time":t,"x":..,"y":..,"curve":0.25,"c2":0,"c3":0.75,"c4":1}`.
   The Spine **4.x** array form `"curve":[..]` makes the runtime compute **NaN** → the bone/slot
   scales to NaN → **the part disappears / the whole token goes invisible**. context7 examples are
   usually 4.x — wrong for this runtime. See `references/pixi-spine-3.8.md`.
   - Bone `rotate` key uses `angle`; `translate`/`scale` use `x`,`y`.
   - Ease `0.25,0,0.75,1`; slow/breath `0.4,0,0.6,1`.

2. **Cuts are ALWAYS done by Gemini, never by a geometric/threshold mask.**
   Generate the isolated part on **solid magenta `#FF00FF`** → `chroma_key.py`. A geometric mask
   gives ragged edges and was explicitly rejected. See `references/cutting-with-gemini.md`.

3. **`noAtlas` spines resolve attachment names as ATLAS FRAME names.**
   A source `src/.../no_opt/png/wild_egypt_sun.png` becomes frame `png/wild_egypt_sun`. The skin
   attachment / animation must use that exact string. Same `sourceSize` ⇒ parts share registration
   even when trimmed differently (the packer reconstructs from offset).

4. **Pixel ↔ skeleton mapping is fixed by the symbol canvas.**
   For a `C`-px square symbol with skeleton width `S` (e.g. 400 → 311):
   `bx = (px/C − 0.5)·S`, `by = (0.5 − py/C)·S` (y is up in Spine), attachment size `= dim/C·S`.
   Helper: `scripts/px_to_skel.py`.

5. **Never reveal a hole.** A moving part must always cover whatever is behind it:
   - parts laid OVER a base must stay **≥** the base element they hide, and grow-only (`scale ≥ 1`)
     if the base still contains that element;
   - or remove that element from the base (then the part is the only copy and may move freely).
   This is why the sun ghosted / a black blob appeared in early iterations.

6. **Emissive LIGHT goes OVER the frame; the SOLID body goes UNDER it.** The frame slot
   clips/contains the solid art (looks framed). But glow / burst / rays / shine are LIGHT —
   if they sit under the frame their upper part is hidden by the frame ring ("свет под рамкой").
   Split them: keep the body sprite under the frame, and draw the growing light as a SEPARATE
   additive slot placed AFTER the frame in draw order (and sized larger than the window) so it
   radiates over and beyond the frame. Extract that light from the lit frames as
   `clamp(lit − calm)` (premultiplied on black; the subject is static so it cancels cleanly,
   leaving only the added light), with **alpha = luminance** (so it both trims tight AND
   premultiply-blends correctly — an additive frame saved with alpha=255 will NOT trim and
   blows the atlas).

7. **In-game attachments OVERFLOW the symbol cell — there is no clipping.** So (a) do NOT shift
   art down to "fit" a burst: the base will poke out PAST the frame on the reel (the offline
   preview clips at the canvas and hides this — the game does not). Centre the SOLID body in the
   window (measure its alpha bbox, offset the attachment so the body centre lands at skel 0,0).
   (b) Conversely, you can deliberately let win FX exit the frame — put them on a slot after the
   frame, sized beyond the window; the overflow is visible in-game and reads as energy.

## Pipeline

```
flat symbol PNG
  │  (1) get a clean, hi-res source        → upscale via Gemini (slot-gen, --size 1K)
  │  (2) CUT each component via Gemini      → magenta + chroma_key  (frame, character, sun, plaque…)
  │  (3) decide the background (фон)        → flat color OR Gemini gradient panel, masked to window
  │  (4) place parts → bones + attachments  → px_to_skel.py, build wild.json (3.8 scalar curves)
  │  (5) animate                            → win / landing / static / static_animated
  │  (6) FX sequences (eyes glow, shine)    → build_fx_sequence.py → attachment-swap slot
  │  (7) PREVIEW OFFLINE                     → preview_spine.py (contact sheet) — BEFORE the game
  └  (8) build                              → assets:build (textures) + assets:copy (spine→bin)
```

### 1. Clean hi-res source
Cutting at higher resolution then downscaling gives crisp edges. Upscale the original faithfully:
```bash
python3 "$SLOTGEN/openrouter_image.py" generate \
  --prompt "Upscale and sharpen this exact symbol, keep composition/colors 100% identical, only raise resolution. Square 1:1." \
  --model nano-banana-pro --size 1K --aspect-ratio 1:1 \
  --reference-image orig.png --output up.png
```
If the source is in a repo using **Git LFS** (png/jpg/webp often are), `git show` returns a pointer,
not the image. Get the real bytes with: `git cat-file --filters HEAD:path/to.png > orig.png`.

### 2. Cut components (Gemini → chroma)
See `references/cutting-with-gemini.md` for the exact prompts. Key tricks:
- Gemini refuses to delete the **main subject** ("keep only the sun" keeps the whole mask).
  → feed a **tight crop** of just that region as `--reference-image`.
- For the **frame**: forceful full-frame prompt — *"erase the ENTIRE interior into one flat magenta
  rectangle, keep only the hollow gold frame ring, empty magenta hole in the middle."*
- Everything on magenta, then `python3 "$SLOTGEN/chroma_key.py" --input X_iso.png --output X.png`.

### 3. Background (фон)
The inner window behind the character must be filled or you get transparent corner gaps (and a
white/grey box on the reel if you bake a white bg). Options:
- **Flat tint** — a rounded-rect panel of the inner colour, transparent outside, edge tucked under
  the frame.
- **Gradient** (preferred, matches original) — ask Gemini to *"reproduce only the visible warm
  radial background gradient, remove mask/sun/frame/plaque"* → mask to the window.
Never leave the full original as the base (it duplicates every component and ghosts on animation).

### 4–5. Rig + animate
Read `references/rigging-and-animation.md`. The proven layout:

```
bones:  root → { rays(center), char(center), wild(plaque) },  sun = CHILD of char
slots (back→front): base/фон, rays(additive), char, charfx(additive seq), frame(STATIC, on top), sun, sun_glow(additive), wild
```
- **frame on top + static** → clips the growing character to the window (no messy overflow).
- **sun is a child of `char`** → when the character grows, the sun automatically rises higher and
  scales with it (only safe once the sun is removed from / never in the base).
- **glow** = a second slot reusing a part's frame, `blend:"additive"`, setup `color:"ffffff00"`,
  animate the alpha hex (`ffffffXX`).

Animation set: `static` (empty, holds setup) · `landing` (~0.5 s squash-settle + kick) ·
`win` (~2 s the showcase) · `static_animated` (~3 s idle breath/sway). Recipes in the reference.

### 6. FX sequences (frame-by-frame)
For "glow from the eyes" and "a shine running across the character", use a **slot attachment
timeline** (real sprite sequence). 3.8 supports `slots.<slot>.attachment = [{time,name}, … ,{time,name:null}]`
(null = hide). Build the frames procedurally (perfect coherence — the base never "breathes"):
```bash
python3 scripts/build_fx_sequence.py --char wild_egypt_char.png \
  --eyes 120,134 180,134 --frames 14 --out-dir parts/ --prefix wild_fx_
```
Put them on an **additive** slot on the same bone as the character (so FX scales/moves with it),
hidden in setup, swapped through during `win`.

### 7. Preview OFFLINE first (do not skip)
`preview_spine.py` is a spine-3.8-lite renderer: it evaluates scalar-bezier timelines, the bone
hierarchy (translate/rotate/scale), additive slots and attachment swaps, then writes a contact
sheet. Catch ghosts/holes/timing here — the game loop is slow to iterate.
```bash
python3 scripts/preview_spine.py --spine wild.json --parts-dir parts/ \
  --canvas 400 --skel 311 --anim win --cols 6 --rows 2 --out .tmp_<symbol>/win.png
```
Bigger cells: `--cell 200`. To see overflow beyond the frame, set `--canvas` larger than the
symbol (e.g. 520). To compare backgrounds, write each candidate to the bg PNG, preview `static`,
restore — assemble a labelled contact sheet (offline A/B/C/D beats blind regen).

### 8. Build
Game loads from `bin/`, not `src/`:
- textures changed (any PNG) → `yarn assets:build`  (repacks atlases, png + webp)
- spine JSON changed → `yarn assets:copy`  (copies `src/assets/spine/*.json` → `src/bin/spine`)
- **GEOMETRY-ONLY changes (attachment x/y/width, bone offsets, timings) need NO repack** — the
  atlas pixels are unchanged, just `yarn assets:copy`. Only NEW/changed PNGs need `assets:build`.
- sanity: `yarn build:dev` (catches webpack errors only, not animation correctness)
- Never call `texturepacker` directly (watermark) — only `yarn assets:*`.

## Coherent transforms (opening/leafing/morphs) → image-to-video, NOT still-image

Still-image Gemini CANNOT produce a coherent open/close/flip sequence (each gen drifts → flicker,
torn parts). For any real motion of a flat symbol (book opening, pages leafing, lid lifting),
generate an **image-to-video** clip and slice it into an attachment sequence. Full recipe:
`references/video-to-sequence.md`. Short version:
- OpenRouter `POST /api/v1/videos`, model `kwaivgi/kling-v3.0-std` (native **1:1**; Veo is 16:9/9:16 only).
  Anchor `first_frame`+`last_frame` (base64 data-URL — don't upload proprietary art to public hosts).
- `ffmpeg -i v.mp4 f_%03d.png` → key each frame with **remove.bg** (NOT colour-chroma — chroma TEARS
  soft pages; remove.bg keeps clean edges; ~500px downscale is fine for a ≤400px symbol). Generate on
  flat magenta; if you bake glow/beams, keep them via chroma instead.
- Sample by **visible** change (pixel-diff lies: a lighting flash reads as motion). Drop the near-closed
  lead-in. For "continuously leafing while X glows" → **ping-pong** a fanned-frame subset as the hold loop.
- More frames = smoother (20+); attachment swaps are stepped.

**Hard-won video rules (a "glowing pyramid" reskin run):**
- **Both anchors MUST share an identical background AND identical subject — only the effect differs.**
  If the calm anchor is on white and the lit anchor on black, the clip's exposure FLIPS mid-way and the
  light "jumps". Generate the lit anchor first, then **derive the calm anchor FROM it** ("remove the glow,
  keep pyramid/position/black-bg identical") — now only the light changes → a smooth ramp.
- **Animate the FULL composition, never a cropped piece.** A cropped tip placed back over a static base
  needs pixel-perfect seam alignment and never matches. Render the whole subject (frame-less, on the
  keying bg) so the keyed frames drop into the symbol 1:1.
- **Pick the keying bg by content luminance** (see slot-gen): a bright/glowing subject → generate the clip
  on **pure black**, key by **luminance** (black→transparent, brightness→alpha) — this preserves the soft
  glow/burst as graded alpha (magenta+chroma tears soft light). A **saturation floor** (sat>~0.3 & bright →
  force opaque) keeps the coloured solid object hole-free. Custom `luma_key` (~30 lines), not `chroma_key.py`.
- **"Just the light appears, no movement"** is a valid clip: prompt the subject PERFECTLY STILL / camera
  locked, and only the light grows. No-rotation clips key rock-steady (no per-frame jitter).
- **Sync the accent flash to the base light.** If a separate star/flare additive ramps LATER than the
  baked light growth, it reads as "lagging". Match their peak times (e.g. both peak at 0.55 s).
- **Tone down a blown-white burst to warm gold** at the keying step (gold-tint + dim the low-saturation
  hot core: `white = bright & low-sat → mix toward [255,205,120]·~0.8`). Users read pure-white clip as
  "overexposed"; warm gold reads as treasure light.

## Framed symbol (bg + frame + plaque) — copy the wild layout
To wrap a symbol like the others: bones `root → content(scale ~0.8, the art+light) → rays/eye; plaque`.
Slots back→front: `bg, frame, <art/light>, plaque`. **Frame drawn BEFORE the art** if it must NOT clip a
growing book (art overflows over the frame); frame AFTER (on top) if it should clip (wild's choice).
Plaque on its own bone with the wild throb curve. Generate bg/frame/plaque on magenta → chroma; the frame
needs a hollow magenta centre. `content` setup-scale shrinks the art into the window; win scale multiplies it.

## Gotchas index
- Invisible token / NaN → array curve instead of 4 scalars (rule 1).
- **Attachment-sequence slot renders INVISIBLE (only the base/last frame shows) → the sequence frames
  aren't declared in the SKIN under that slot.** A `slots.<slot>.attachment` timeline can only name
  attachments that exist in `skins.default.attachments.<slot>`. If you swap `png/char` through
  `png/char_00..18`, ALL of `char_00..18` must be skin entries under slot `png/char` (not just the base
  `png/char`). Missing → the runtime resolves null → the part disappears for every keyed frame. (Cost a
  debug cycle: character was missing in all frames except the final base-named key.) Mirror how high2
  lists every `high2_fire_00..23` in the skin.
- **Reuse another symbol's frame/part with ZERO new PNG.** `noAtlas` spines resolve attachment names as
  shared atlas frame names, so any spine can reference a frame baked by a sibling (e.g. high1's frame slot
  just points at `png/high2_frame`). No copy, no new asset, only `assets:copy`. Same trick for rays/glow
  (`png/wild_egypt_rays` reused as a flash). Frame-glow = a second additive slot reusing the frame's own
  frame name, gold-tinted, alpha-ramped.
- **Green text "name" instead of the symbol → frame-name COLLISION.** `no_opt` and `opt` atlases share the
  `png/...` namespace; a new `no_opt/png/X.png` whose name already exists in `opt/png` makes the spine
  resolve the wrong frame and fall back to a green label. Always give new parts names unique across BOTH
  folders (check `opt/png` before naming). Cost a long debug session.
- White/grey box on reel → a part baked on white; key it on magenta instead, base must be transparent.
- Black blob where a part should be → base still has a dark fill / old copy peeking; cover it or remove it (rule 5).
- Ghost double (two suns, two masks) → moving part smaller than the base copy, or it translated off it.
- Torn/ragged pages from colour-chroma → use remove.bg for soft/paper parts (see video-to-sequence.md).
- Win light hidden / clipped by the frame ("свет под рамкой") → emissive light is under the frame slot;
  move it to an additive slot AFTER the frame, sized beyond the window (rule 6).
- Base/art pokes out PAST the frame on the reel (fine in offline preview) → art shifted down too far; the
  cell does NOT clip in-game. Centre the solid body (rule 7).
- Light "jumps"/flickers across a video clip → the two anchors had different backgrounds/exposure; derive
  the calm anchor from the lit one so only the light differs.
- Additive FX frame won't trim (atlas overflows) / glow looks wrong → saved with alpha=255; rebuild with
  **alpha = luminance** so it trims and premultiply-blends (rule 6).
- A separate flash/star reads as "late" → its ramp peaks after the base light; sync their peak times.
- remove.bg rate-limits rapid batches → space calls (~3 s) + retry; read the key as the exact last
  non-comment value of `REMOVEBG_API_KEY` (trailing chars break auth).
- Pin the runtime: this repo needs `@zephyr/slot-base 0.7.85` (0.7.88 breaks `SlotMachine.Symbol`).

See `references/` for depth and `scripts/` for the tools.
