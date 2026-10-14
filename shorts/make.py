#!/usr/bin/env python3
"""make.py - build a vertical Short from a script: Pixabay clips + Google TTS narration + pop captions.

    python3 make.py script.json [-o out.mp4]

script.json:
    {"title": "상단 고정 제목\\n*강조*는 노란색",
     "scenes": [{"say": "나레이션 문장, *강조 단어*는 노란 자막", "query": "english pixabay search"}]}

Reads PIXABAY_API_KEY and GOOGLE_TTS_KEY from the environment. Needs ffmpeg/ffprobe (with libass).
"""
import argparse, base64, json, os, subprocess, sys, tempfile, urllib.parse, urllib.request

VOICE = "ko-KR-Chirp3-HD-Leda"
FONT_URL = "https://raw.githubusercontent.com/orioncactus/pretendard/main/packages/pretendard/dist/public/static/Pretendard-ExtraBold.otf"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
CUT = 2.5      # seconds per stock clip; fast cuts read as current
CHUNK = 9      # max chars per caption pop
YELLOW = r"{\c&H00E0FF&}"
OLD_ID = 100000  # ponytail: Pixabay ids below this are ~2015-2021 uploads; tune if picks look dated

def get(url, data=None, headers={}):
    # Pixabay 403s the default urllib User-Agent
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0", **headers})
    with urllib.request.urlopen(req) as r:
        return r.read()

def font():
    path = os.path.join(CACHE, "Pretendard-ExtraBold.otf")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        open(path, "wb").write(get(FONT_URL))
    return CACHE

def tts(text, out):
    body = {"input": {"text": text.replace("*", "")}, "voice": {"languageCode": "ko-KR", "name": VOICE},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 44100, "speakingRate": 1.15}}
    r = get(f"https://texttospeech.googleapis.com/v1/text:synthesize?key={os.environ['GOOGLE_TTS_KEY']}",
            json.dumps(body).encode(), {"Content-Type": "application/json"})
    open(out, "wb").write(base64.b64decode(json.loads(r)["audioContent"]))

def pick_clips(query, n, used):
    q = urllib.parse.urlencode({"key": os.environ["PIXABAY_API_KEY"], "q": query, "per_page": 30,
                                "safesearch": "true", "video_type": "film"})
    hits = [h for h in json.loads(get(f"https://pixabay.com/api/videos/?{q}"))["hits"] if h["id"] not in used][:12]
    if not hits:
        sys.exit(f"no pixabay video for query: {query!r}")
    # keep relevance order, but vertical first and the dated-looking early stock (low ids) last
    hits.sort(key=lambda h: (h["id"] < OLD_ID, h["videos"]["medium"]["width"] > h["videos"]["medium"]["height"]))
    picked = [hits[i % len(hits)] for i in range(n)]
    used.update(h["id"] for h in picked)
    return [h["videos"]["medium"]["url"] or h["videos"]["small"]["url"] for h in picked]

def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).strip())

def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *args], check=True)

def chunks(say):
    """Split narration into short caption pops, keeping *highlight* spans across splits."""
    out, cur, hl = [], [], False
    for word in say.split():
        styled = YELLOW if hl else ""  # highlight may continue from the previous chunk
        for ch in word:
            if ch == "*":
                hl = not hl
                styled += YELLOW if hl else r"{\c&HFFFFFF&}"
            else:
                styled += ch
        plain = "".join(w for w, _ in cur) + word.replace("*", "")
        if cur and len(plain) > CHUNK:
            out.append(cur); cur = []
        cur.append((word.replace("*", ""), styled))
    out.append(cur)
    # each chunk: (plain length for timing, styled ASS text that resets colour at the end)
    return [(len("".join(p for p, _ in c)), " ".join(s for _, s in c) + r"{\c&HFFFFFF&}") for c in out]

def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"

def ass(title, timeline):
    head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Pretendard ExtraBold,88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,7,0,8,60,60,230,1
Style: Cap,Pretendard ExtraBold,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,9,5,5,70,70,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    end = timeline[-1][1] if timeline else 0
    t = title.replace("\\n", "\n").replace("\n", r"\N")
    while "*" in t:
        t = t.replace("*", YELLOW, 1).replace("*", r"{\c&HFFFFFF&}", 1)
    lines = [f"Dialogue: 1,{ts(0)},{ts(end)},Title,,0,0,0,,{t}"]
    pop = r"{\pos(540,1180)\fscx75\fscy75\t(0,90,\fscx105\fscy105)\t(90,160,\fscx100\fscy100)}"
    lines += [f"Dialogue: 0,{ts(a)},{ts(b)},Cap,,0,0,0,,{pop}{text}" for a, b, text in timeline]
    return head + "\n".join(lines) + "\n"

def make(script, out):
    with tempfile.TemporaryDirectory() as tmp:
        used, fontsdir, t = set(), font(), 0.0
        vparts, aparts, timeline = [], [], []
        for i, s in enumerate(script["scenes"]):
            wav = os.path.join(tmp, f"{i}.wav")
            tts(s["say"], wav)
            d = duration(wav)
            aparts.append(wav)
            # captions: spread over the scene by character count
            cs = chunks(s["say"]); total = sum(n for n, _ in cs) or 1; c = t
            for n, text in cs:
                timeline.append((c, c + d * n / total, text)); c += d * n / total
            # video: cut the scene into ~CUT-second stock clips
            k = max(1, round(d / CUT))
            for j, url in enumerate(pick_clips(s["query"], k, used)):
                src, seg = os.path.join(tmp, f"{i}_{j}.src.mp4"), os.path.join(tmp, f"{i}_{j}.mp4")
                open(src, "wb").write(get(url))
                ff("-stream_loop", "-1", "-i", src, "-t", f"{d / k:.3f}", "-an", "-vf",
                   "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
                   "eq=saturation=1.15:contrast=1.05,setsar=1",
                   "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", seg)
                vparts.append(seg)
            t += d
        lst = lambda name, parts: (open(os.path.join(tmp, name), "w").write("".join(f"file '{p}'\n" for p in parts)), os.path.join(tmp, name))[1]
        ff("-f", "concat", "-safe", "0", "-i", lst("v.txt", vparts), "-c", "copy", os.path.join(tmp, "v.mp4"))
        ff("-f", "concat", "-safe", "0", "-i", lst("a.txt", aparts), "-c", "copy", os.path.join(tmp, "a.wav"))
        sub = os.path.join(tmp, "s.ass")
        open(sub, "w").write(ass(script.get("title", ""), timeline))
        # ponytail: no BGM - Pixabay music has no API; add a royalty-free loop with amix if wanted
        ff("-i", os.path.join(tmp, "v.mp4"), "-i", os.path.join(tmp, "a.wav"), "-map", "0:v", "-map", "1:a",
           "-vf", f"subtitles={sub}:fontsdir={fontsdir}", "-t", f"{t:.3f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
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
