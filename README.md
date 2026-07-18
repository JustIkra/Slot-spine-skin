# slot-spine-skin

Codex skill for turning a flat slot symbol into a multi-part Spine 4.2 rig for
the current Urso/Zephyr Pixi 8 runtime.

The production profile is exact `@zephyr/slot-base 0.11.2`, exact overridden
`@esotericsoftware/spine-pixi-v8 4.2.119`, Spine 4.2 JSON, and the Urso Texture
Builder. Always confirm the target game's `package.json`, `package-lock.json`,
loader, and installed package source before integration.

## Contents

- `SKILL.md` — end-to-end production playbook.
- `references/spine-pixi-v8-4.2.md` — current JSON/timeline contract.
- `references/cutting-with-gemini.md` — component extraction through slot-gen.
- `references/rigging-and-animation.md` — pivot, layering, and timing recipes.
- `references/video-to-sequence.md` — coherent motion through attachment swaps.
- `scripts/preview_spine.py` — offline Spine 4.2 subset contact-sheet renderer.
- `scripts/build_fx_sequence.py` — additive eye-glow and shine-sweep frames.
- `scripts/px_to_skel.py` — pixel placement to skeleton coordinates.

Provider keys are read from `~/.codex/.env` and must never be committed.

## Quick verification

```bash
python3 scripts/preview_spine.py --spine symbol.json --parts-dir parts \
  --canvas 400 --skel 311 --anim win --out .tmp_symbol/win.png
npm run assets:textures
npm run assets:copy
```

The final gate is parsing with the exact installed Spine 4.2 runtime and testing
the built asset through the real wrapper with zero game/local console errors.
