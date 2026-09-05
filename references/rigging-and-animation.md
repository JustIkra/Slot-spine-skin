# Registration and motion

Use one source canvas for layers that must register. Place pivots at joints or visual
anchors; convert pixels with px_to_skel.py. position_parts.py can estimate SIFT/RANSAC
alignment against a reference; inspect the resulting composite, especially low-detail parts.
canonical_layout.py is an initial humanoid guess, not an accepted pose.

Use a parent-before-child skeleton and deliberate back-to-front slots. Decompose only
where independent transforms, tint, blend or occlusion are needed. Remove a baked feature
before moving its replacement. Test motion at extrema for holes and overlap.

build_spine_json.py supports idle, walk, run, wave, jump and attack presets. The built-in
bone naming contract is documented in its config/example and generated --help. Presets
are starting motion, not a substitute for animation direction. Custom animations contain
valid Spine 4.2 data; read the runtime reference for absolute curves.

Use reusable meshes/layers for continuous plasma or glow. Pin a stable silhouette when
the subject should keep its outline; interior motion should not become whole-object shaking.
Compare geometry and alpha before/after loop wrap, including neighboring samples.

Validate using the exact installed runtime and inspect runtime preview. The limited Python
renderer refuses unsupported data; do not weaken its gate to produce a contact sheet.
After acceptance, use the target project's existing asset scripts and real-wrapper checks.
