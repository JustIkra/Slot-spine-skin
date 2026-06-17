# pixi-spine 3.8 JSON format (the parts that bite)

Verified against `@pixi-spine/runtime-3.8` (`SkeletonJson` reader) and context7
`/esotericsoftware/spine-runtimes`. The runtime is **3.8** — do not author 4.x JSON.

## Curve format — the #1 killer

```jsonc
// CORRECT (3.8): four scalars
{ "time": 0.3, "x": 1.18, "y": 1.18, "curve": 0.25, "c2": 0.0, "c3": 0.75, "c4": 1.0 }

// WRONG (4.x array) -> readCurve mis-parses -> bezier = NaN -> NaN scale -> part vanishes
{ "time": 0.3, "x": 1.18, "y": 1.18, "curve": [0.25, 0, 0.75, 1] }
```

The reader does: `timeline.setCurve(i, map.curve, getValue(map,"c2",0), getValue(map,"c3",1), getValue(map,"c4",1))`.
So `curve` is `cx1`, `c2`=`cy1`, `c3`=`cx2`, `c4`=`cy2`.
- `"curve":"stepped"` is also valid (hard cut — used for attachment-style holds).
- Presets: ease-in-out `0.25,0,0.75,1`; gentle/breath `0.4,0,0.6,1`; linear = omit `curve`.

## Bone timelines

```jsonc
"bones": {
  "sun": {
    "rotate":    [ { "time":0, "angle":0, "curve":0.25,"c2":0,"c3":0.75,"c4":1 }, { "time":2.0, "angle":360 } ],
    "translate": [ { "time":0, "x":0, "y":0 }, { "time":1.0, "x":0, "y":10 } ],
    "scale":     [ { "time":0, "x":1, "y":1 }, { "time":0.15, "x":1.2, "y":1.2 } ]
  }
}
```
- `rotate` uses **`angle`** (degrees, additive over setup). `translate`/`scale`/`shear` use **`x`,`y`**.
- `scale` values are **multipliers** of the setup scale (1.0 = unchanged).
- `translate` `x`,`y` are in skeleton units, added to the bone's setup position.

## Slot timelines

```jsonc
"slots": {
  "png/wild_glow": { "color": [ { "time":0, "color":"ffffff00", ...curve }, { "time":0.2, "color":"ffffffaa" } ] },
  "png/wild_fx":   { "attachment": [ { "time":0.12, "name":"png/wild_fx_00" }, { "time":0.22, "name":"png/wild_fx_01" }, { "time":1.5, "name":null } ] }
}
```
- `color` is `RRGGBBAA` hex. For an **additive glow**, keep RGB `ffffff` and animate the **AA** alpha.
- `attachment` is the **frame sequence** mechanism: swap region names over time, `name:null` hides.
  This is discrete (no tween) — use ~10–16 frames for a smooth sweep.

## Bones / slots / skin skeleton

```jsonc
"bones": [
  { "name":"root" },
  { "name":"char", "parent":"root", "x":0.0, "y":-4.67 },          // x,y in skeleton units
  { "name":"sun",  "parent":"char", "x":0.0, "y":125.97 }          // child → inherits char transform
],
"slots": [
  { "name":"png/wild_char", "bone":"char", "attachment":"png/wild_char" },
  { "name":"png/wild_glow", "bone":"sun",  "attachment":"png/wild_sun", "color":"ffffff00", "blend":"additive" }
  // slot ORDER = draw order, back → front
],
"skins": [ { "name":"default", "attachments": {
  "png/wild_char": { "png/wild_char": { "width":216.1, "height":233.25 } },              // slot → attachment → region
  "png/wild_frame":{ "png/wild_frame":{ "y":-0.78, "width":307.9, "height":307.9 } }     // region supports x,y,rotation,scaleX,scaleY
} } ]
```
- Region attachment supports `x`, `y`, `scaleX`, `scaleY`, `rotation`, `width`, `height`.
  An attachment with no `x/y` is centered on its bone → rotating/scaling the bone pivots about the
  part center (put the bone at the part's centre to spin a sun in place).
- A slot with **no `attachment`** field shows nothing in setup (used for FX/glow that start hidden).
- One slot can hold **many** attachments (the frame-sequence pattern).

## noAtlas + atlas frames

Symbol spines load with `noAtlas:true`: attachment region names are looked up as **frame keys** in
the shared atlas spritesheet JSON (e.g. `src/bin/images/hd/no_opt_*.json`). The frame key equals the
source path relative to the pack root — `no_opt/png/wild_sun.png` → `png/wild_sun`. So:
- name your source PNGs to produce the frame names your skin references;
- replacing PNG **content** under the same filename needs no JSON change (just repack);
- a part can live on any atlas page — the loader resolves by name across all pages of the group.

### sourceSize and trimming
The packer trims transparent margins but records `sourceSize` + `spriteSourceSize` (offset). Parts
built on the **same canvas size** share registration even if trimmed differently — pixi reconstructs
placement from the offset. That is why an additive overlay on the same canvas lines up perfectly.

## skeleton block
```jsonc
"skeleton": { "hash":"unique-string", "spine":"3.8.99", "x":-155.5, "y":-155.5, "width":311, "height":311, "images":"./images/", "audio":"" }
```
Bump `hash` on every change (cheap cache-bust). `x/y` = `-width/2, -height/2` (centered).
