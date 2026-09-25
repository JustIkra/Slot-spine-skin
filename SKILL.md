---
name: slot-spine-skin
description: >
  Use when positioning existing parts, rigging or animating slot symbols, characters,
  heroes or FX in Spine 4.2; building idle/walk/run/win motion; checking mesh, alpha,
  loops or atlases; or integrating Spine assets into Urso/Zephyr.
---

# Slot Spine authoring and integration

This is the single owner of Spine tools for symbols, full characters and FX.
Use slot-gen only when new artwork/video masters or raster extraction are required.

## Inputs and setup

Read the game's memory index, package/lock files, loader and Texture Builder configuration.
Use its installed Spine/Pixi/Urso versions; do not introduce parallel engine dependencies or
force another project's version into the game. Resolve build commands from that project.

Install this repository in the working Python environment:
    python -m pip install -e .

The shared workspace interpreter is /Users/maksim/MorningCat/.local/skills-venv/bin/python.
Keep authoring kits and accepted masters distinct from ignored .tmp_<task>/ candidates.

## Choose the stage

| Stage | Tool / reference |
|---|---|
| Canvas coordinates to pivots | scripts/px_to_skel.py |
| Place parts against reference | scripts/position_parts.py |
| Initial humanoid layout / inspect composite | scripts/canonical_layout.py / scripts/compose_layout.py |
| Layout to configuration | scripts/build_skeleton_v2.py or scripts/layout_to_spine_config.py |
| Build JSON / animation presets | scripts/build_spine_json.py |
| Standalone source atlas | scripts/make_atlas.py |
| Runtime parse and sampled motion | scripts/validate-spine.mjs |
| Actual installed-runtime preview | scripts/build-runtime-preview.mjs |
| Packed texture memory / attachment keys | scripts/check-atlas-budget.mjs |

Use --help for Python commands. Node validators accept explicit --project-root, --spine,
--atlas-root and optional --out. The preview additionally requires a new/empty output directory.
See [runtime contract](references/spine-pixi-v8-4.2.md) before authoring JSON and
[rigging](references/rigging-and-animation.md) for registration/motion decisions.

## Invariants

- One canonical canvas; pivots reflect joints or visual anchors, not image corners.
- Separate only layers needing independent motion, tint, blend or draw order.
- Remove baked elements before animating replacements to avoid ghosts.
- Slot order is back-to-front. Place the frame/halo where the brief requires coverage.
- Rotate timelines use value; setup bones use rotation. Bezier points are absolute
  time/value coordinates per channel. The builder converts its preset easing; do not
  convert already-exported custom Spine curves a second time.
- Verify actual poses, fixed channels, mesh geometry and loop boundaries, not only finite JSON.
- Prefer reusable layers/mesh for continuous FX. Video frame swaps require an explicit
  memory budget and a reason the motion cannot reasonably use the reusable rig.

## Prototype to optimized runtime

For slot work, the user's preference is to explore motion with sequences when useful,
then realize a successful direction with reusable meshes and bones wherever they retain
its appearance. Split the object by behavior: an evolving surface may retain a short
sequence while the rim, rays and attached flashes use independent rigs. Preserve the
accepted silhouette and material detail; do not replace local motion with whole-image warping.

Use the project's existing Urso `npm run assets:textures` and shared TexturePacker atlas
families. Add new parts to those common maps; do not create a separate runtime atlas for
each hero, rim or FX. Preserve explicit quality options such as `-w 75`.

Before optimizing or integrating a sequenced effect, read
[TexturePacker and animation optimization](references/texturepacker-animation-optimization.md)
for quality limits, compact mesh materials, attached effects and A/B verification.

## Verification

Run validate-spine.mjs against the installed game runtime; --loop <animation> additionally
checks matching end poses and the join relative to neighboring samples. Build the runtime preview and
inspect several times, setup pose, loop join, tint and foreground/background blend.
The Python preview_spine.py is a limited region-only contact sheet: it refuses unsupported
data and is not authoritative for mesh, constraints, tint or advanced blend modes.
Legacy generate_spine_player.py is a convenience CDN player, not the installed-runtime gate.

Check each configured PNG/WebP quality with check-atlas-budget.mjs. Supply a budget JSON
with maxDecodedBytes, maxPages and maxEdge. RGBA estimates exclude mipmaps/driver overhead.
Reject missing keys, oversized packs and clipped canonical layers.

## Integration only when requested

Use the game's existing loader: noAtlas resolves attachment paths through shared texture
keys; explicit Spine atlases retain their loader ordering. Load multipack root _0 once.
Build via the project scripts, then use zephyr-launcher-session for desktop/mobile evidence.
Do not fake wrapper startup or accept a canvas-only capture as layout proof.

Finish with the source kit, one maintained skeleton, verification evidence and limitations.
Preserve recovery material until acceptance; cleanup is scoped, never automatic broad deletion.
