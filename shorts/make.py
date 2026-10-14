#!/usr/bin/env python3
"""make.py - build a vertical Short from a script: Pixabay clips + Google TTS narration + captions.

    python3 make.py script.json [-o out.mp4]

script.json:
    {"scenes": [{"say": "나레이션 문장", "query": "english pixabay search", "caption": "optional on-screen text"}]}

Reads PIXABAY_API_KEY and GOOGLE_TTS_KEY from the environment. Needs ffmpeg/ffprobe.
"""
import argparse, base64, json, os, subprocess, sys, tempfile, textwrap, urllib.parse, urllib.request

VOICE = "ko-KR-Neural2-C"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/blackhansans/BlackHanSans-Regular.ttf"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")

def get(url, data=None, headers={}):
    # Pixabay 403s the default urllib User-Agent
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0", **headers})
    with urllib.request.urlopen(req) as r:
        return r.read()

def font():
    path = os.path.join(CACHE, "BlackHanSans-Regular.ttf")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        open(path, "wb").write(get(FONT_URL))
    return path

def tts(text, out):
    body = {"input": {"text": text}, "voice": {"languageCode": "ko-KR", "name": VOICE},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.1}}
    r = get(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={os.environ['GOOGLE_TTS_KEY']}",
            json.dumps(body).encode(), {"Content-Type": "application/json"})
    open(out, "wb").write(base64.b64decode(json.loads(r)["audioContent"]))

def pick_clip(query, used):
    q = urllib.parse.urlencode({"key": os.environ["PIXABAY_API_KEY"], "q": query, "per_page": 20, "safesearch": "true"})
    hits = [h for h in json.loads(get(f"https://pixabay.com/api/videos/?{q}"))["hits"] if h["id"] not in used]
    if not hits:
        sys.exit(f"no pixabay video for query: {query!r}")
    # vertical clips first, otherwise keep Pixabay's relevance order
    hit = sorted(hits, key=lambda h: h["videos"]["medium"]["width"] > h["videos"]["medium"]["height"])[0]
    used.add(hit["id"])
    return hit["videos"]["medium"]["url"] or hit["videos"]["small"]["url"]

def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).strip())

def wrap(text):
    # ponytail: fixed 12-char wrap; tune if the font or size changes
    return "\n".join(textwrap.wrap(text, 12, break_long_words=True))

def scene(i, s, tmp, used, fontfile):
    audio, clip, cap, out = (os.path.join(tmp, f"{i}.{x}") for x in ("mp3", "src.mp4", "txt", "mp4"))
    tts(s["say"], audio)
    open(clip, "wb").write(get(pick_clip(s["query"], used)))
    open(cap, "w").write(wrap(s.get("caption") or s["say"]))
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
          f"drawtext=fontfile={fontfile}:textfile={cap}:fontsize=80:fontcolor=white:line_spacing=20:"
          "borderw=6:bordercolor=black:x=(w-text_w)/2:y=h*0.62")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-stream_loop", "-1", "-i", clip, "-i", audio,
                    "-map", "0:v", "-map", "1:a", "-t", f"{duration(audio) + 0.3:.2f}", "-vf", vf,
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-ar", "44100", "-ac", "2", out], check=True)
    return out

def make(script, out):
    scenes = script["scenes"]
    with tempfile.TemporaryDirectory() as tmp:
        used, f = set(), font()
        parts = [scene(i, s, tmp, used, f) for i, s in enumerate(scenes)]
        lst = os.path.join(tmp, "list.txt")
        open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    return out

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("script"); p.add_argument("-o", "--out", default="short.mp4")
    a = p.parse_args()
    missing = [k for k in ("PIXABAY_API_KEY", "GOOGLE_TTS_KEY") if not os.environ.get(k)]
    if missing: sys.exit(f"missing env: {', '.join(missing)}")
    out = make(json.load(open(a.script)), a.out)
    d = duration(out)
    print(f"{out} ({d:.1f}s)")
    if d > 59: print("warning: over 59s", file=sys.stderr)
