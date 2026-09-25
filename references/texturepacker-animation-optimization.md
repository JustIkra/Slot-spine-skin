# TexturePacker and animation optimization

Apply this to slot animation authoring, packing and integration. It records the user's
runtime preferences; it does not expand an asset-only task into game integration.

## Use the installed Urso workflow

Read `package.json`, the asset config, loader and live `.tps` files. Run the existing
`npm run assets:textures`; use the project's copy/full-build commands when relevant.
Use the installed TexturePacker. Do not substitute a hand-written packing
algorithm or a parallel asset pipeline merely to optimize an existing game.

Check unfamiliar flags in the installed CLI, including its actual executable. In Urso
CLI 0.4.2d, `-w 75` means WebP quality 75 and adds a WebP pass for every discovered TPS.
It is not texture width, page size or a redundant switch to remove automatically.
A separate WebP TPS may also receive that pass. Inspect the emitted paths and actual
loader before classifying files as redundant; retain explicit user quality settings.

Keep per-unit source folders but common runtime atlas families. Add new symbols, hero
parts, rims and FX to the existing shared maps. Do not create a runtime TPS/atlas family
per effect just to give it different trim settings. Preserve existing intentional
scene/load-group splits; any new split needs a concrete loading or engine constraint.
Automatic multipack pages are expected when the common map is full.

Choose the largest page limit supported by the project's quality/device contract.
Quality scale and maximum atlas edge are different settings. A verified neighboring
configuration is high scale 1/max 4096, hd .75/max 2048, medium .5/max 2048; inspect the
actual project rather than making those values universal. Independent quality layouts
can have different page counts. Load the root once, follow `related_multi_packs`, and
derive per-quality counts from metadata instead of hard-coding an identical count.

Measure page count, transferred bytes and decoded RGBA bytes separately. Larger pages
can reduce requests without reducing memory. WebP quality changes transfer size, not
RGBA allocation. Count each page once; `width * height * 4` excludes mipmaps and driver
overhead. Do not sum all quality/format alternatives as one game's active texture memory.
After repacking, check both runtime and production output for obsolete numbered pages;
remove/archive only superseded generated files, preserving unrelated assets and sources.

## Develop the idea, then optimize by layer

Sequences can establish the intended motion. After visual acceptance, prefer reusable
mesh/bone motion where it preserves that result. Do not treat a successful flipbook
prototype as automatically production-ready, and do not equate fewer files with success.

| Layer behavior | Suitable representation |
|---|---|
| Changing internal plasma pattern | Short coherent sequence, with a loop and interpolation |
| Rim or continuous contour | Weighted ribbon/annular mesh with a pinned inner edge |
| Rays, tongues and attached flashes | Reusable materials and local bones with varied phases |
| Rigid decorative parts | Region attachments on bones; a mesh may be unnecessary |

Retain sequence layers when a rig cannot reproduce their changing material detail.
Use a hybrid rather than warping the whole picture. Preserve common registration, local
depth, palette and accepted timing. Compare reduced resolution/frame counts explicitly.
Animated sequence layers need a coherent source interval without reconstruction bursts,
a closed loop, and adjacent-frame blending when frame stepping is visible. Complementary
blend weights should sum to one when constant total light is intended.

## Compact mesh materials in a shared atlas

Inspect the installed Urso/Pixi/Spine atlas adapter first. Some mesh adapters interpret
UVs within the packed region and ignore source trimming offsets. Such meshes cannot
simply use the old full-canvas UVs after their image is trimmed. Disabling trim for the
entire game or adding an effect-specific atlas is not the preferred solution.

A verified preparation method is:

1. Let TexturePacker trim a source material into a compact authoring PNG and retain its
   exact `spriteSourceSize` rectangle `(x, y, w, h)` in the original canvas. A single-image
   preparation export can use `--trim-mode Trim --trim-margin 1 --shape-padding 0
   --border-padding 0 --extrude 0 --disable-rotation`. The PNG becomes a source material,
   not a new runtime atlas family. Keep the original source and crop metadata.
2. Remap UVs into that rectangle: `u' = (u * sourceWidth - x) / w`, and similarly for v.
   Clip triangles extending beyond the retained texture rectangle. Merely clamping UVs
   on triangles that still render can stretch border pixels or expose neighboring sprites.
3. At each clipping intersection, interpolate the skin influences as well as UVs. For
   a bone with endpoint weights `wa`, `wb`, the new weight is `(1-t)*wa + t*wb`; interpolate
   its local coordinate with these weighted coefficients and divide by the new weight.
   This preserves deformation. Keep the visible material, pivot and pinned geometry.
4. Pack the compact materials with all other runtime textures in the existing common TPS.
   Confirm the final mesh regions remain untrimmed/unrotated at EVERY quality, with UVs
   inside their canonical bounds. A valid high atlas alone does not prove hd/medium safety.
5. Check the actual installed runtime for missing keys, clipping, texture bleed, mesh
   winding and loops. Compare visible pixels and geometry with the accepted version.

Space Nova's `prepare-hero-rim-materials.js`, `clip-rim-mesh.js` and `check-hero-rim.js`
are a worked implementation when that project is available. Their specific radii and
counts are art parameters, not defaults to copy into other effects.

## Keep attached flashes attached

Anchor a flash to the actual animated mesh location, not merely the nearest control
bone. A partially weighted rim vertex moves differently from a full-strength bone.
Use the same weighted position, or a supported equivalent attachment constraint, and
place the visible base slightly inside the luminous edge. Keep emitted geometry rooted;
vary its local length, intensity, lifetime and phase without making detached flying pieces.

Sample the complete loop: roots remain on their target vertices, inner rows remain
pinned, the seam stays closed, triangles do not flip, and brightness stays controlled.
Report additional bones/vertices as well as texture savings; a texture reduction is not
by itself proof of faster rendering.

## Compare and promote

Use synchronized A/B views with the same surface, arcs, scale, background, quality and
time. Offer pause/scrub, slow playback, rim-only and bone overlays when useful. Record
which sources, skeleton and atlases each side actually uses. A comparison loading both
variants together is not a measurement of either variant's standalone memory use.

When integration is authorized, promote the accepted source kit and deterministic
generator into the game, rebuild through Urso, and verify runtime/production output.
Keep prototype recovery files outside the commit. Real-wrapper desktop/mobile checks
remain separate from asset previews; report external blockers rather than claiming an
asset preview proves the game layout.
