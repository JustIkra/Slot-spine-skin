# Spine Pixi v8 4.2 JSON contract

Use this reference with the current Urso/Zephyr production profile:

- exact `@zephyr/slot-base 0.11.2`;
- Pixi 8 supplied by the resolved Zephyr/Urso tree;
- exact `@esotericsoftware/spine-pixi-v8 4.2.119` override;
- Spine JSON 4.2.

Confirm all versions from the target game's `package.json`, `package-lock.json`,
and installed packages. Runtime and data must share the same Spine major/minor.

## Skeleton, bones, slots, and skin

```json
{
  "skeleton": {
    "hash": "asset-source-hash",
    "spine": "4.2.0",
    "x": -155.5,
    "y": -155.5,
    "width": 311,
    "height": 311
  },
  "bones": [
    { "name": "root" },
    { "name": "character", "parent": "root", "x": 0, "y": -4.67 }
  ],
  "slots": [
    {
      "name": "png/character",
      "bone": "character",
      "attachment": "png/character"
    },
    {
      "name": "png/glow",
      "bone": "character",
      "attachment": "png/glow",
      "color": "ffffff00",
      "blend": "additive"
    }
  ],
  "skins": [
    {
      "name": "default",
      "attachments": {
        "png/character": {
          "png/character": { "width": 216.1, "height": 233.25 }
        },
        "png/glow": {
          "png/glow": { "width": 216.1, "height": 233.25 }
        }
      }
    }
  ]
}
```

Bone order is parent before child. Slot array order is draw order from back to
front. Region attachments support `x`, `y`, `rotation`, `scaleX`, `scaleY`,
`width`, and `height`.

## Bezier arrays

Spine 4.2 stores four bezier control values per animated channel. For the common
ease `[0.25, 0, 0.75, 1]`:

```json
{
  "rotate": [
    { "time": 0, "angle": 0, "curve": [0.25, 0, 0.75, 1] },
    { "time": 1, "angle": 15 }
  ],
  "translate": [
    {
      "time": 0,
      "x": 0,
      "y": 0,
      "curve": [0.25, 0, 0.75, 1, 0.25, 0, 0.75, 1]
    },
    { "time": 1, "x": 0, "y": 10 }
  ],
  "scale": [
    {
      "time": 0,
      "x": 1,
      "y": 1,
      "curve": [0.25, 0, 0.75, 1, 0.25, 0, 0.75, 1]
    },
    { "time": 1, "x": 1.1, "y": 1.1 }
  ]
}
```

Use `"curve": "stepped"` for a hold and omit `curve` for linear interpolation.
If a timeline has N interpolated values, a custom bezier has `N * 4` numbers.

## Slot alpha and color

For alpha-only fades, prefer the one-channel `alpha` timeline:

```json
{
  "slots": {
    "png/glow": {
      "alpha": [
        { "time": 0, "value": 0, "curve": [0.25, 0, 0.75, 1] },
        { "time": 0.2, "value": 0.7 },
        { "time": 1.2, "value": 0 }
      ]
    }
  }
}
```

For full color animation, use `rgba`. Each key retains an eight-digit
`RRGGBBAA` `color`. A custom RGBA bezier contains sixteen values, four each for
R, G, B, and A. Omit the curve when linear color interpolation is sufficient.

## Attachment sequences

```json
{
  "slots": {
    "png/fx": {
      "attachment": [
        { "time": 0.12, "name": "png/fx_00" },
        { "time": 0.22, "name": "png/fx_01" },
        { "time": 1.52, "name": null }
      ]
    }
  }
}
```

Attachment swaps are discrete. Use key spacing to control perceived frame rate.

## `noAtlas` and Texture Builder

With `noAtlas: true`, attachment paths resolve as frame keys in the game's shared
Texture Builder output. Keep source filenames and skin attachment paths aligned.
Trimming remains safe when registered parts share the same source canvas because
Texture Builder records source size and trim offsets.

For Pixi multipacks, load only the root `_0` descriptor. Its
`related_multi_packs` list identifies linked pages; treating every linked page as
another root can create circular loads and duplicate cache work.

## Parser gate

Parse the complete data with the exact installed
`@esotericsoftware/spine-core 4.2.119`. Assert expected bones, slots, skins,
animations, timeline types, duration, and finite curve storage. Checking only
`skeleton.spine` cannot detect malformed multidimensional bezier arrays.
