---
name: slot-spine-skin
description: >
  Turn a flat slot symbol into a multi-part Spine 4.2 rig for the current Pixi 8
  Urso/Zephyr runtime. Use when a user asks to animate a wild, scatter, high
  symbol, hero, minion, glow, shine sweep, landing, idle, win, or attachment
  sequence; split a baked symbol into layers; build a noAtlas Spine asset; or
  integrate a Spine symbol through the Urso Texture Builder.
---

# Slot Spine Skin

Build a reusable Spine 4.2 asset from a flat symbol, verify it offline, then
integrate it through the target game's actual Urso/Zephyr asset contract.

## Production runtime gate

Before authoring, read the target game's `package.json`, `package-lock.json`,
loader declaration, Texture Builder configuration, and installed package source.
For the current production stack, require:

- exact direct `@zephyr/slot-base 0.11.2`;
- Pixi 8 supplied transitively by Zephyr/Urso;
- exact overridden `@esotericsoftware/spine-pixi-v8 4.2.119`;
- Spine 4.2 JSON parsed by the exact installed 4.2 runtime;
- Urso Texture Builder for shared PNG/WebP atlases and quality variants.

Do not add direct Pixi, Urso, or Spine dependencies beside the Zephyr boundary.
Treat the target game's `package.json`, lockfile, and installed package source as
the authoritative API/build documentation. This skill documents only the current
Pixi 8 + Spine 4.2 contract; legacy runtime recipes must not be added. Resolve
asset-build commands from the target package `scripts` and its installed Urso
Texture Builder instead of copying commands from another project.
Do not keep a second runtime recipe in this skill. If an existing game resolves a
different package tree, follow its package files and installed source.

## Scope

Use this skill for a baked symbol that needs internal motion or reusable runtime
color. Use `slot-gen` for image generation, cutting, chroma keying, and source-art
variants. Use the general `spine-animation` skill for full characters with many
body parts and locomotion cycles.

The default symbol structure is:

```text
root
├── background
├── character
│   └── focal
├── plaque
└── fx
```

Slots are ordered back to front. Put a static frame after the moving content when
it must visually cover overflow. Put it before the character only when the brief
explicitly calls for a pop-out effect.

## Working directory and secrets

Keep generated candidates, extracted parts, contact sheets, and helper outputs in
an ignored project-local `./.tmp_<symbol>/` directory. Provider keys live in
`~/.codex/.env`; never print or commit them.

For the shared image backend:

```bash
export SLOTGEN=/Users/maksim/git_projects/Slot-gen-skill/scripts
```

## Workflow

### 1. Lock the runtime and loader contract

Record the resolved Zephyr, Urso, Pixi, Spine runtime, and Spine core versions.
Inspect the game's asset loader:

- `noAtlas: true`: attachment paths resolve against Texture Builder/Pixi frame
  keys. Add source PNGs to the existing texture projects and load only the root
  `_0` atlas JSON; linked pages come from `related_multi_packs`.
- explicit Spine atlas: keep skeleton and atlas versions aligned and preserve the
  loader's existing `SPINEATLAS` ordering.

Do not infer these choices from another game.

### 2. Decompose the symbol

Read [cutting-with-gemini.md](references/cutting-with-gemini.md). Produce only
layers that need independent draw order, transform, blend mode, color, or future
animation. Keep every source aligned to one canonical canvas whenever registration
matters.

Typical layers are background, moving character, focal object, frame, plaque,
neutral body, neutral plasma, glow, and an optional FX sequence. Remove a baked
element from the base before translating or rotating its replacement, otherwise it
will ghost behind the animated part.

### 3. Place pivots and attachments

Use `scripts/px_to_skel.py` to convert canvas coordinates. Put each bone at the
visual pivot of its part and express child positions relative to their parent.
Keep attachments centered on their bone unless a deliberate local offset is
needed.

For a shared hero/minion master, author one neutral skeleton and one attachment
set. Instantiate it multiple times; change only per-instance transform, alpha,
body color, and glow color. Static minions remain in setup pose while selected
hero instances may later play animation tracks.

### 4. Author valid Spine 4.2 timelines

Read [spine-pixi-v8-4.2.md](references/spine-pixi-v8-4.2.md) before writing JSON.
The hard rules are:

- `skeleton.spine` targets `4.2`;
- slot color animation uses `rgba`, or `alpha` with `value` for alpha-only fades;
- bezier curves are arrays with four numbers per animated channel;
- rotate/alpha curves contain four values;
- translate/scale curves contain eight values;
- RGBA curves contain sixteen values;
- attachment swaps use `slots.<slot>.attachment` and are discrete;
- setup slot color remains eight-digit `RRGGBBAA`.

Prefer the one-channel `alpha` timeline for additive glow fades. It is shorter and
avoids unnecessary four-channel curves.

### 5. Build motion

Use the timing recipes in
[rigging-and-animation.md](references/rigging-and-animation.md). Keep setup pose as
the neutral/static result. Recommended animation names are `landing`, `win`, and
`static_animated`; an empty `static` animation is optional when game code expects
that name.

For coherent opening, leafing, morphing, or facial changes, use
[video-to-sequence.md](references/video-to-sequence.md) and drive a slot attachment
timeline. Frame swaps are stepped, so control perceived speed with frame selection
and key spacing.

### 6. Verify offline

```bash
python3 scripts/preview_spine.py \
  --spine symbol.json --parts-dir parts \
  --canvas 400 --skel 311 --anim win \
  --out .tmp_symbol/win-contact-sheet.png
```

Reject ghosts, holes, detached overlays, clipped glow, dark alpha fringes,
unintended overflow, and a final pose that does not return to setup.

Then parse the complete JSON with the exact installed
`@esotericsoftware/spine-core 4.2.119`. A matching version string alone is not a
validity test; assert that every parsed timeline contains only finite numbers.

### 7. Pack with Texture Builder

Use the target game's existing scripts, normally:

```bash
npm run assets:textures
npm run assets:copy
```

Require all attachment keys in every configured quality and PNG/WebP variant.
For multipack atlases, application code loads the root `_0` descriptor once and
the runtime follows `related_multi_packs`; do not load each linked page as an
independent root.

### 8. Integrate and prove through the wrapper

Preserve wrapper-owned startup. Test through a real Zephyr launcher session and
require:

- successful local skeleton and texture requests;
- one nonblank Pixi canvas;
- zero game/local console errors;
- correct setup pose, draw order, tint, blend modes, and animation completion;
- desktop landscape, mobile portrait, and initialized-mobile landscape evidence.

For a spin check, completion means the reel service is no longer spinning, reel
movement flags are false, and queues are empty. Do not require a specific terminal
state when the game has no implemented win presentation.

## Delivery checklist

- One canonical source kit and one Spine 4.2 skeleton per master asset.
- Production version/loader contract recorded from package files and installed
  source.
- Official 4.2 parser accepts finite timelines.
- Offline contact sheet reviewed before a game build.
- Texture Builder outputs contain every attachment in all configured variants.
- Real-wrapper canvas is nonblank and game/local console errors are zero.
- Scratch directories and helper files are removed after acceptance.

## References

- [Spine Pixi v8 4.2 JSON](references/spine-pixi-v8-4.2.md)
- [Cutting components](references/cutting-with-gemini.md)
- [Rigging and animation](references/rigging-and-animation.md)
- [Video to attachment sequence](references/video-to-sequence.md)
