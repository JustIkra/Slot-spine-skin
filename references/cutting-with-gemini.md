# Cutting symbol components with Gemini (slot-gen)

**Rule:** every component cut goes through Gemini on solid magenta `#FF00FF`, then
`chroma_key.py`. Never a geometric/threshold mask — it gives ragged edges (explicitly rejected
by the user). All commands assume `export SLOTGEN="$HOME/.claude/skills/slot-gen/scripts"`.

## Why magenta + chroma (not remove.bg, not white)

- remove.bg free plan downscales to ~578×432 → blurry. Magenta + `chroma_key.py` keeps full res.
- **Never bake parts on white** — a leftover white background becomes a grey/white box on the reel.
- `chroma_key.py` trims to content by default; pass `--no-trim` to keep the canvas (preserves
  position when you need parts to register against each other).

```bash
python3 "$SLOTGEN/chroma_key.py" --input part_iso.png --output part.png --erode 2
# options: --color ff00ff  --erode N  --no-despill  --no-trim  --resize WxH
```

## The two prompt patterns

### A) Isolate a region — Gemini WON'T delete the main subject
"Keep only the sun, delete the mask" → Gemini keeps the mask. Fix: feed a **tight crop** of just
that region as the reference, then ask to isolate on magenta.

```bash
# crop the region from the upscaled source first (PIL), then:
python3 "$SLOTGEN/openrouter_image.py" generate \
  --prompt "Isolate ONLY the glowing sun disc with its golden rays (and the small cobra below it). Place it on flat solid magenta #FF00FF. Delete the headdress, frame and everything else. Keep exact shape/colors. Uniform pure magenta, no white." \
  --model nano-banana-pro --size 1K --aspect-ratio 1:1 \
  --reference-image sun_tight_crop.png --output sun_iso.png
```
Worked for: **sun**, **WILD plaque** (crop the bottom strip).

### B) Erase the interior — keep a ring/border (frame)
For the frame, a forceful FULL-frame prompt works (no crop):
```bash
python3 "$SLOTGEN/openrouter_image.py" generate \
  --prompt "Keep ONLY the ornate square gold hieroglyph frame border (the outer ring). Erase the ENTIRE interior — mask, headdress, sun, plaque, inner background — and replace that whole central area with one flat uniform rectangle of solid magenta #FF00FF. Make everything OUTSIDE the frame magenta too. Result: only the hollow gold frame ring on pure magenta, clean empty magenta hole in the middle. No face, no text. Square 1:1." \
  --model nano-banana-pro --size 1K --aspect-ratio 1:1 \
  --reference-image up.png --output frame_iso.png
```

### Character / background
- **Character**: "Keep ONLY the mask + nemes + collar in exact position. Replace ALL other pixels
  (inside and outside the frame) with flat magenta #FF00FF. No white anywhere." (Gemini may
  recenter/enlarge it — that's fine, you re-place it during rigging.)
- **Background gradient (фон)**: "Reproduce ONLY the warm radial background gradient visible behind
  the character (lighter warm centre, darker edges). Remove mask, sun, frame, plaque. Full square
  panel, no objects." Then mask it to the window rounded-rect (edge hidden under the frame).

## Models / sizes
- `nano-banana-pro` = `google/gemini-3-pro-image-preview` (quality). Rejects 4:1/8:1/1:4/1:8 aspects.
- `nano-banana-2` = `google/gemini-3.1-flash-image-preview` (use for wide strips / fast).
- `--size 1K` is enough when the final part is ≤ ~400 px. Upscale source first, cut, then downscale
  the cut — crisper edges than cutting at native res.

## Getting the original out of Git LFS
PNG/JPG/WEBP/audio are often LFS. `git show HEAD:path` returns the pointer text (PIL can't open it).
```bash
git cat-file --filters HEAD:src/assets/images/no_opt/png/wild_egypt.png > .tmp_<symbol>/orig.png
```

## Re-theming instead of re-cutting
To recolour an existing part/animation set (don't regenerate frames — no temporal coherence):
`python3 "$SLOTGEN/recolor_lut.py" --ramp gold in.png out.png` (luminance → gradient).
