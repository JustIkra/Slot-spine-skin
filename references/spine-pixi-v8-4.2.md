# Spine 4.2 runtime contract

Resolve the actual project's package tree. Space Nova's tested profile is Pixi 8 and
Spine 4.2.119 through Urso/Zephyr; this is not permission to update another game's versions.
The data major/minor must match the installed runtime.

## Fields and ordering

- Setup bones: rotation; rotate animation keys: value.
- Slot setup color: eight-digit RRGGBBAA. Animated color uses rgba; alpha-only uses alpha/value.
- Skins use the 4.2 array form with name and attachments.
- Bones are parent-before-child; slots are back-to-front.
- Attachment swaps use slots.<slot>.attachment with time/name and are discrete.

## Bezier control points

Spine control points are absolute time/value pairs, not reusable normalized easing.
For a channel going from (t0,v0) to (t1,v1), convert normalized easing (x1,y1,x2,y2) to:

    [t0+(t1-t0)*x1, v0+(v1-v0)*y1, t0+(t1-t0)*x2, v0+(v1-v0)*y2]

Each channel needs four numbers: rotate/alpha four, translate/scale eight, rgba sixteen.
A constant channel keeps constant value controls. Omit curve for linear and use stepped
for a hold. Last keys do not need a curve. Already-exported custom curves are not converted
again by the generator.

Test real samples: rotate 0→30 reaches 30; unchanged x stays zero; nonzero time intervals
interpolate correctly. Finite arrays alone do not catch ignored fields or unintended motion.

## Atlas contract

With noAtlas, texture keys must match attachment paths across every configured PNG/WebP
quality. Load multipack root _0 once and follow related_multi_packs. The validator checks
missing/duplicate keys and page bounds; the budget checker counts each image once.

Preserve canonical registration. For the tested Urso weighted-mesh adapter, final mesh
regions must retain their canonical bounds without further atlas trimming or rotation.
This does not require a separate atlas or retaining a large transparent source canvas.
Prepare a compact material, remap its UVs, clip transparent outer mesh triangles while
preserving skin weights, then pack it into the common atlas. Verify `trimmed: false` and
`rotated: false` for those mesh regions at every quality. Do not infer mesh trim safety
from region-attachment behavior. See [the preparation procedure](texturepacker-animation-optimization.md).

## Tools

    node scripts/validate-spine.mjs --project-root <game> --spine <skeleton.json> --atlas-root <root.json>
    node scripts/build-runtime-preview.mjs --project-root <game> --spine <skeleton.json> --atlas-root <root.json> --out <new-preview-directory>
    node scripts/check-atlas-budget.mjs --atlas-root <root.json> --spine <skeleton.json> --budget <budget.json>

Budget fields: maxDecodedBytes, maxPages, maxEdge. The byte figure is RGBA8 base texture
memory, not a driver/GPU profiler measurement. Run each configured quality independently.

The preview bundles the installed game runtime, not an arbitrary latest CDN. Review mesh,
draw order, tint, light and the loop join. It is asset evidence, not wrapper layout proof.
