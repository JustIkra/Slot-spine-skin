#!/usr/bin/env python3
"""Image-to-video via OpenRouter /api/v1/videos (Kling 1:1) for coherent flat-symbol motion.

Submits a first+last anchor (base64 data-URLs — never upload proprietary art to public hosts),
polls until completed, downloads the mp4. Slice it with ffmpeg + key per video-to-sequence.md.

  python3 gen_video.py --first start.png --last end.png --out clip.mp4 \
     --prompt "subject smiles and the torch flares, static locked camera, magenta bg unchanged"

Key read from ~/.claude/.env (OPENROUTER_KEY). ~$0.08/s, 5 s clip → 121 frames @ ~960².
Both anchors MUST share an identical background AND subject — only the effect differs (else the
clip's exposure flips mid-way and the light "jumps"). Derive the calm anchor FROM the lit one.
"""
import argparse, base64, json, mimetypes, os, sys, time, urllib.error, urllib.request


def read_key():
    env = os.path.expanduser("~/.claude/.env")
    val = None
    for line in open(env):
        s = line.rstrip("\n")
        if s.strip().startswith("#"):
            continue
        if s.startswith("OPENROUTER_KEY="):
            val = s.split("=", 1)[1].strip()
    if not val:
        sys.exit("no OPENROUTER_KEY in ~/.claude/.env")
    return val


def dataurl(path):
    mime = mimetypes.guess_type(path)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", required=True, help="first_frame anchor (start pose)")
    ap.add_argument("--last", required=True, help="last_frame anchor (end pose; derive from first)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="kwaivgi/kling-v3.0-std")
    ap.add_argument("--duration", type=int, default=5)
    ap.add_argument("--resolution", default="720p")
    ap.add_argument("--aspect", default="1:1")
    a = ap.parse_args()
    key = read_key()

    body = {
        "model": a.model, "prompt": a.prompt, "duration": a.duration,
        "resolution": a.resolution, "aspect_ratio": a.aspect, "generate_audio": False,
        "frame_images": [
            {"type": "image_url", "image_url": {"url": dataurl(a.first)}, "frame_type": "first_frame"},
            {"type": "image_url", "image_url": {"url": dataurl(a.last)}, "frame_type": "last_frame"},
        ],
    }

    def req(url, data=None, method=None):
        h = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        r = urllib.request.Request(url, data=(json.dumps(data).encode() if data else None), headers=h, method=method)
        with urllib.request.urlopen(r, timeout=120) as resp:
            return json.loads(resp.read().decode())

    print("submit...")
    try:
        j = req("https://openrouter.ai/api/v1/videos", data=body, method="POST")
    except urllib.error.HTTPError as e:
        sys.exit("submit error: " + e.read().decode())
    print(json.dumps({k: j.get(k) for k in ("id", "status", "polling_url")}, indent=2))
    poll = j.get("polling_url") or f"https://openrouter.ai/api/v1/videos/{j['id']}"

    for i in range(120):
        time.sleep(20)
        try:
            s = req(poll)
        except urllib.error.HTTPError as e:
            print("poll err", e.read().decode()[:200]); continue
        st = s.get("status")
        print(f"[{i}] {st}")
        if st == "completed":
            urls = s.get("unsigned_urls") or s.get("output", {}).get("urls") or []
            if not urls:
                print(json.dumps(s, indent=2)[:2000]); sys.exit("no urls")
            vurl = urls[0]
            rq = urllib.request.Request(vurl, headers={"Authorization": f"Bearer {key}"} if "openrouter.ai" in vurl else {})
            with urllib.request.urlopen(rq, timeout=300) as resp, open(a.out, "wb") as f:
                f.write(resp.read())
            print("saved", a.out, os.path.getsize(a.out), "bytes")
            return
        if st in ("failed", "error", "canceled"):
            print(json.dumps(s, indent=2)[:2000]); sys.exit("video failed")
    sys.exit("timeout")


if __name__ == "__main__":
    main()
