# Source layers for rigging

Generation and raster extraction belong to slot-gen. Supply it with the accepted master,
parts needed for motion, canonical canvas and reference points.

Use native alpha when present. For an opaque subject, choose a chroma not present in its
palette (green for purple/magenta), then process locally without independently trimming
registered layers. For glow, use the separate light-on-black path and preserve graded alpha.
Do not use the largest-component logo tool on particles or a halo.

Keep source resolution; do not upscale a source to disguise a weak cut. If source art is
insufficient, request a new coherent master rather than repairing every frame differently.
Only generate extra layers that need independent draw order, movement or tint.

Use the prompt to isolate the intended part without moving it, then inspect registration
against the source. If a crop is necessary, record its offset in the canonical canvas.
A removed moving feature must not remain baked into the base image.
