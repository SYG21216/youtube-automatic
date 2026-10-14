"""Generate YouTube profile (800x800) and banner (2560x1440) images.
Usage: python make_branding.py "Channel Name" "tagline"
"""
import sys
from PIL import Image, ImageDraw, ImageFont

NAME = sys.argv[1] if len(sys.argv) > 1 else "YOUTUBE AUTOMATIC"
TAG = sys.argv[2] if len(sys.argv) > 2 else "New videos every week"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
C1, C2, ACCENT = (20, 16, 48), (90, 30, 140), (255, 70, 90)


def gradient(w, h):
    img = Image.new("RGB", (w, h))
    px = img.load()
    for x in range(w):
        for y in range(h):
            t = (x / w + y / h) / 2
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(C1, C2))
    return img


def play(d, cx, cy, r):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ACCENT)
    s = r * 0.45
    d.polygon([(cx - s * 0.7, cy - s), (cx - s * 0.7, cy + s), (cx + s, cy)], fill="white")


def profile():
    img = gradient(800, 800)
    d = ImageDraw.Draw(img)
    play(d, 400, 400, 260)
    img.save("profile.png")


def banner():
    W, H = 2560, 1440
    img = gradient(W, H)
    d = ImageDraw.Draw(img)
    # decorative circles outside the safe area (visible on TV/desktop only)
    for cx, cy, r in [(300, 300, 400), (2300, 1150, 500), (2200, 250, 180)]:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(120, 80, 170), width=6)
    # safe area 1546x423, centered: everything important lives here
    sx, sy = (W - 1546) // 2, (H - 423) // 2
    play(d, sx + 150, H // 2, 120)
    size = 120
    while size > 40:
        f = ImageFont.truetype(BOLD, size)
        if d.textlength(NAME, font=f) <= 1546 - 340:
            break
        size -= 4
    d.text((sx + 310, H // 2 - 20), NAME, font=f, fill="white", anchor="ls")
    d.text((sx + 314, H // 2 + 60), TAG, font=ImageFont.truetype(REG, 52), fill=(220, 210, 255), anchor="ls")
    img.save("banner.png")


if __name__ == "__main__":
    profile()
    banner()
