# Video to runtime motion

The video master comes from slot-gen/scripts/gen_video.py with its saved job record.
Do not implement a second provider request here. Inspect the full clip and lock framing,
registration and intended timing before extracting frames.

Extract into an ignored project-local directory. Preserve original frame dimensions and a
single shared crop/canvas, use local opaque chroma or light extraction as appropriate,
and inspect dark/light composites for spill, holes, clipped glow and detached features.
Do not regenerate individual frames independently.

Prefer reusable layers/mesh for persistent background FX. Frame swaps are justified for
motion that needs them, such as a coherent opening/morph, and only after checking the
packed atlas budget at each quality. Frame count alone does not measure GPU memory.

Attachment swaps use slots.<slot>.attachment time/name keys. They are discrete; key
spacing controls speed. Verify setup pose, opening/closing holds and any ping-pong join
instead of assuming that reversing a sequence creates a seamless loop.

Use the runtime validator and preview, then Texture Builder and the real wrapper when
integration is requested. No automatic installation of large video-derived texture pages.
