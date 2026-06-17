# Coherent motion via image-to-video → attachment sequence

When a flat slot symbol must actually MOVE in a coherent way (a book opening, pages leafing/riffling,
a lid lifting, a creature morphing), still-image Gemini fails: every generation drifts, so a hand-stitched
"sequence" flickers and parts look torn. The reliable path is to render a real **image-to-video** clip and
slice it into a Spine **attachment timeline**. This was proven on the "Book of the Dead" scatter
(book opens + pages continuously leaf while the Eye glows).

## 1. Generate the clip (OpenRouter video API)

OpenRouter exposes `POST /api/v1/videos` (separate from chat). List models with `GET /api/v1/videos/models`.

- **Model**: `kwaivgi/kling-v3.0-std` — native **1:1**, image-to-video, ~$0.08/s. (Google **Veo 3.1** is
  great but only 16:9 / 9:16 → you'd crop a square; Seedance/Wan also do 1:1.)
- **Anchor frames**: `frame_images:[{type:image_url,image_url:{url:DATAURL},frame_type:"first_frame"},
  {…,"last_frame"}]`. first = the closed/start art on flat **magenta**, last = the desired end pose
  (e.g. cover+eye visible with pages fanned — keeps identity; a full two-page spread loses the cover).
- **URL = base64 data-URL** (`data:image/jpeg;base64,…`). OpenRouter docs: base64 is required for local/
  non-public files. Do NOT upload proprietary game art to public hosts (catbox/transfer.sh) — the sandbox
  classifier blocks it and it's a real leak.
- Prompt: describe the motion AND forbid the failure mode. e.g. for leafing: "pages continuously flip and
  riffle, all pages stay ATTACHED, NO detaching/flying leaves, STATIC locked camera, book centered".
- Submit → poll `polling_url` every ~20 s until `completed` → download `unsigned_urls[0]`
  (Bearer auth for openrouter.ai URLs). ~5 s clip, 121 frames @ 960².

```python
body = {"model":"kwaivgi/kling-v3.0-std","prompt":PROMPT,"duration":5,"resolution":"720p",
        "aspect_ratio":"1:1","generate_audio":False,
        "frame_images":[{"type":"image_url","image_url":{"url":first_dataurl},"frame_type":"first_frame"},
                        {"type":"image_url","image_url":{"url":last_dataurl},"frame_type":"last_frame"}]}
# POST https://openrouter.ai/api/v1/videos  (Bearer OPENROUTER_KEY), then poll polling_url.
```

Ready-made: **`scripts/gen_video.py`** does submit → poll → download in one call:
```bash
python3 scripts/gen_video.py --first start_magenta.png --last end_magenta.png --out .tmp_<sym>/clip.mp4 \
  --prompt "subject smiles and the torch flares brighter, static locked camera, magenta bg unchanged"
# Generate the END pose first (slot-gen Gemini edit of the start: "same subject/position/scale/magenta,
# change ONLY the effect") so both anchors share bg+subject. That edit may hit the transient
# "no image data" error → retry (see slot-gen gotchas).
```

## 2. Extract + key the frames

- `ffmpeg -loglevel error -i clip.mp4 vframes/f_%03d.png` (ffmpeg numbers from **1**, not 0).
- Key EACH frame to transparent with **remove.bg**, not colour-chroma. Colour-keep chroma TEARS soft paper
  (ragged page edges, holes); remove.bg keeps clean soft edges. Its ~500 px downscale is irrelevant for a
  ≤400 px symbol. (Exception: if the clip baked glow/beams you want to keep, those are additive light →
  generate on magenta and chroma so the beams survive; remove.bg would delete them.)
- remove.bg call = multipart `image_file` + `size=auto`, header `X-Api-Key`. Read the key as the **exact**
  last non-comment `REMOVEBG_API_KEY=` value, stripped (trailing space/CR → `auth_failed`).
- **Rate limit**: rapid batches 429. Space calls ~3 s and retry each ~5–6×. ~20 frames is fine paced.

## 3. Sample frames intelligently

- Sample by **visible** change, not raw pixel-diff — a lighting flash spikes pixel-diff while the book looks
  unchanged, so naive equal-diff clusters useless near-closed frames. Inspect a contact sheet; drop the
  static lead-in; pick where the motion is actually visible.
- Avoid junk frames (e.g. Kling adds flying-petal frames late → exclude them; use the clean fanning range).
- 20+ frames for a smooth attachment swap (swaps are stepped, no tween).

## 4. Build the attachment timeline

Slot with no setup attachment is fine; drive `slots.<slot>.attachment = [{time,name},…]`.

Patterns used on the book:
- **open → close**: forward 0→N over the open phase, hold, reverse N→0 to close.
- **continuous leafing while a glow holds**: open 0→K, then a **ping-pong loop** of a fanned subset
  (`[k..N]+[N-1..k]` repeated) across the whole glow window, then close. The eye/rays colour timelines hold
  a bright **plateau** for the same window so "while the eye glows, the book keeps leafing".
- Light layers (eye-core, rays) are SEPARATE additive slots on a bone pivoted at the eye: eye pulses, rays
  spin (linear `rotate` 0→N°), both ramp alpha. Darken the book at the flash peak via the book slot's
  `color` (e.g. `493f29ff`) so the additive light pops on a dark book.

Validate with `scripts/preview_spine.py` before building, then `yarn assets:build` + `yarn assets:copy`.
