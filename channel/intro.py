#!/usr/bin/env python3
"""intro.py - render the 1-second brand intro (logo pop + coin drop + "띵") to shorts/intro.mp4.

    python3 channel/intro.py

Needs ffmpeg and the Playwright headless Chromium in /opt/pw-browsers. Re-run only when the branding changes.
"""
import glob, math, os, subprocess, tempfile, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, "shorts", ".cache", "Pretendard-ExtraBold.otf")  # make.py downloads it
OUT = os.path.join(ROOT, "shorts", "intro.mp4")
CHROME = glob.glob("/opt/pw-browsers/chromium_headless_shell-*/*/headless_shell")[0]
FPS, DUR, SR = 30, 1.0, 44100
COIN_LAND = 0.42  # seconds; the "띵" plays here

HOUSE = """<svg viewBox="0 0 400 380" width="560" height="532" xmlns="http://www.w3.org/2000/svg">
  <rect x="268" y="40" width="44" height="90" rx="8" fill="#111"/>
  <path d="M200 10 L385 165 L15 165 Z" fill="#111" stroke="#111" stroke-width="20" stroke-linejoin="round"/>
  <rect x="30" y="150" width="340" height="220" rx="28" fill="#111"/>
  <path d="M48 175 L200 285 L352 175" fill="none" stroke="#FFD400" stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""

def ease_back(x):  # overshoot then settle, for the "pop"
    x = min(max(x, 0), 1); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def frame_html(t):
    pop = ease_back(t / 0.3)                                  # logo 0 -> 1 with overshoot
    drop = min(max((t - 0.12) / (COIN_LAND - 0.12), 0), 1)    # coin falls in
    coin_y = -700 * (1 - drop) ** 2 + (12 * math.sin((t - COIN_LAND) * 30) * math.exp(-(t - COIN_LAND) * 12) if t > COIN_LAND else 0)
    txt = min(max((t - 0.45) / 0.25, 0), 1)
    return f"""<html><head><style>@font-face{{font-family:P;src:url(file://{FONT})}}
body{{margin:0;width:1080px;height:1920px;background:#FFD400;overflow:hidden;font-family:P}}
.logo{{position:absolute;left:260px;top:600px;width:560px;height:532px;transform:scale({pop:.3f});transform-origin:50% 70%}}
.coin{{position:absolute;left:{260 + 280 - 53}px;top:{600 + 147 - 53 + coin_y:.1f}px;width:106px;height:106px;border-radius:50%;
  background:#FFD400;border:10px solid #111;box-sizing:border-box;display:flex;align-items:center;justify-content:center;
  font-size:66px;color:#111;opacity:{1 if drop > 0 else 0}}}
.t{{position:absolute;width:100%;top:{1190 + 40 * (1 - txt):.1f}px;text-align:center;font-size:150px;letter-spacing:-5px;color:#111;opacity:{txt:.2f}}}
</style></head><body><div class="logo">{HOUSE}</div><div class="coin">₩</div><div class="t">봉투자취</div></body></html>"""

def ding(path):
    t = np.arange(int(SR * DUR)) / SR
    a = np.zeros_like(t)
    for start, f in ((COIN_LAND, 988), (COIN_LAND + 0.07, 1319)):  # B5 -> E6, the classic coin
        m = t >= start; tt = t[m] - start
        a[m] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 9) * 0.35
    pcm = (np.stack([a, a], 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(int(FPS * DUR)):
            html = os.path.join(tmp, f"f{i}.html")
            open(html, "w").write(frame_html(i / FPS))
            subprocess.run([CHROME, "--no-sandbox", "--hide-scrollbars", "--window-size=1080,1920",
                            f"--screenshot={tmp}/{i:03d}.png", f"file://{html}"], check=True, capture_output=True)
        ding(os.path.join(tmp, "a.wav"))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", f"{tmp}/%03d.png", "-i", f"{tmp}/a.wav",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-ar", "44100", "-ac", "2",
                        "-shortest", OUT], check=True)
    print(OUT)
