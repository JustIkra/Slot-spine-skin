# Slot Spine tools

One authoring pipeline for symbols, characters and FX. Read [SKILL.md](SKILL.md).
Install the Python package with python -m pip install -e . in the working environment.

The default verification path uses the target game's installed runtime:
validate-spine.mjs, build-runtime-preview.mjs and check-atlas-budget.mjs.
The Python renderer is a limited region-only contact sheet; the legacy CDN player is
a convenience preview, not proof of production-runtime compatibility.

Tests: python -m unittest discover -s tests -p 'test_*.py'; then run Node tests with
SLOT_TEST_PROJECT set to an installed game and PYTHON set to the working interpreter.
Production integration uses the game's existing Texture Builder and real wrapper.
