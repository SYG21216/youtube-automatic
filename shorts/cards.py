"""cards.py - motion-graphics cards for long-form videos, drawn as ASS subtitle events (no stock media).

A scene {"say": "...", "card": {...}} in a doc-style script becomes a plain background plus these events.
Kinds: headline, number, compare, list, vs, timeline, ratio, quote, talk. Every card also gets the channel
mascot (a TV with eyes) in a corner unless "mascot": false; "react": "!" / "?" / "♥" pops a bubble over it.
People: "quote" shows one person with a speech bubble, "talk" two people taking turns; "mood" is smile/shock/sad.
"""

CARD_BG = "0x141826"
# ASS colours are &HBBGGRR&
PINK, BLUE, YELLOW, GREEN = "&H7E2EFF&", "&HF0B43C&", "&H42C8FF&", "&H6EE0A0&"
ACCENTS = [PINK, BLUE, YELLOW, GREEN]
WHITE, DARK, SKIN, HAIR = "&HFFFFFF&", "&H1C1316&", "&H9FC8F2&", "&H2A2230&"

STYLES = """Style: CShape,Pretendard ExtraBold,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1
Style: CHead,Pretendard ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,100,100,0,1
Style: CBig,Pretendard ExtraBold,120,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,120,120,0,1
Style: CHuge,Pretendard ExtraBold,220,&H0042C8FF,&H0042C8FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,100,100,0,1
Style: CText,Pretendard ExtraBold,62,&H00E6E6E6,&H00E6E6E6,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,4,100,100,0,1
Style: CLabel,Pretendard ExtraBold,56,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,6,100,100,0,1
Style: CVal,Pretendard ExtraBold,60,&H0042C8FF,&H0042C8FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,4,100,100,0,1
Style: CBubble,Pretendard ExtraBold,46,&H001C1316,&H001C1316,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1
Style: CEmote,Pretendard ExtraBold,64,&H001C1316,&H001C1316,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
"""


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def circle(r):
    """Circle inside the box (0,0)-(2r,2r): with \\an5 it is centred on \\pos."""
    k = round(r * 0.5523)
    c = lambda x, y: f"{x + r} {y + r}"
    return (f"m {c(r, 0)} b {c(r, k)} {c(k, r)} {c(0, r)} b {c(-k, r)} {c(-r, k)} {c(-r, 0)} "
            f"b {c(-r, -k)} {c(-k, -r)} {c(0, -r)} b {c(k, -r)} {c(r, -k)} {c(r, 0)}")


def rrect(w, h, r):
    """Rounded rectangle (0,0)-(w,h)."""
    k = round(r * 0.45)
    return (f"m {r} 0 l {w - r} 0 b {w - k} 0 {w} {k} {w} {r} l {w} {h - r} b {w} {h - k} {w - k} {h} {w - r} {h} "
            f"l {r} {h} b {k} {h} 0 {h - k} 0 {h - r} l 0 {r} b 0 {k} {k} 0 {r} 0")


class Canvas:
    def __init__(self, a, b):
        self.a, self.b, self.L = a, b, []

    def ev(self, s, e, style, txt, layer=3):
        self.L.append(f"Dialogue: {layer},{ts(s)},{ts(max(e, s + 0.05))},{style},,0,0,0,,{txt}")

    def shape(self, s, e, x, y, color, path, tags="", layer=2, an=7, alpha="&H00&"):
        self.ev(s, e, "CShape", f"{{\\an{an}\\pos({x},{y})\\1c{color}\\1a{alpha}{tags}\\p1}}{path}", layer)

    def text(self, s, e, x, y, style, txt, an=5, tags="\\fad(200,0)", layer=3):
        self.ev(s, e, style, f"{{\\an{an}\\pos({x},{y}){tags}}}{txt}", layer)


POP = "\\fscx60\\fscy60\\t(0,180,\\fscx108\\fscy108)\\t(180,280,\\fscx100\\fscy100)"


def wiggle(dur, deg=2.5, step=700):
    """Gentle left-right sway for the whole duration (needs a shared \\org)."""
    out, k, sign = "", 0, 1
    while k * step < dur * 1000:
        out += f"\\t({k * step},{(k + 1) * step},\\frz{sign * deg})"
        k, sign = k + 1, -sign
    return out


def mascot(cv, s, e, x, y, react=None, scale=1.0):
    """The channel's TV-with-eyes mascot at (x, y) top-left: sways, glances around, blinks."""
    S = lambda v: round(v * scale)
    org = f"\\org({x + S(130)},{y + S(260)})"
    sway = org + wiggle(e - s)
    cv.shape(s, e, x + S(70), y - S(20), "&H463A4A&", rrect(S(14), S(44), S(7)), "\\frz25" + sway, 4)
    cv.shape(s, e, x + S(176), y - S(20), "&H463A4A&", rrect(S(14), S(44), S(7)), "\\frz-25" + sway, 4)
    cv.shape(s, e, x, y, PINK, rrect(S(260), S(200), S(46)), sway, 4)
    dur = int((e - s) * 1000)
    blink = "".join(f"\\t({t},{t + 70},\\fscy10)\\t({t + 70},{t + 140},\\fscy100)" for t in range(1800, dur, 2600))
    for ex in (S(75), S(185)):
        cv.shape(s, e, x + ex, y + S(95), WHITE, circle(S(40)), sway + blink, 5, an=5)
        look = f"\\move({x + ex - S(12)},{y + S(100)},{x + ex + S(12)},{y + S(100)},0,{min(dur, 1500)})"
        cv.ev(s, e, "CShape", f"{{\\an5{look}\\1c{DARK}{blink}\\p1}}{circle(S(17))}", 6)
    if react:
        bx, by = x + S(230), y - S(70)
        cv.shape(s + 0.3, e, bx, by, YELLOW, circle(S(48)), POP, 6, an=5)
        cv.text(s + 0.3, e, bx, by, "CEmote", react, tags=POP, layer=7)


def person(cv, s, e, x, y, shirt=BLUE, mood="smile", flip=False):
    """A flat, friendly person (head + hair + body) whose top-left is (x, y); about 220x330."""
    org = f"\\org({x + 110},{y + 330})"
    sway = org + wiggle(e - s, 1.5, 900)
    cv.shape(s, e, x + 20, y + 150, shirt, rrect(180, 190, 70), sway, 4)
    cv.shape(s, e, x + 110, y + 85, SKIN, circle(78), sway, 5, an=5)
    hair_x = x + (40 if not flip else 30)
    cv.shape(s, e, hair_x, y + 2, HAIR, rrect(150, 62, 30), sway, 6)
    for ex in (x + 82, x + 138):
        cv.shape(s, e, ex, y + 92, DARK, circle(9), sway, 6, an=5)
    mx, my = x + 110, y + 128
    if mood == "shock":
        cv.shape(s, e, mx, my, DARK, circle(14), sway, 6, an=5)
    elif mood == "sad":
        cv.shape(s, e, mx - 26, my - 4, DARK, "m 0 18 b 14 0 38 0 52 18 l 46 22 b 36 10 16 10 6 22", sway, 6)
    else:
        cv.shape(s, e, mx - 26, my - 14, DARK, "m 0 0 b 14 22 38 22 52 0 l 46 0 b 36 12 16 12 6 0", sway, 6)


def bubble(cv, s, e, x, y, txt, tail="left"):
    """White speech bubble centred at (x, y) sized to the text."""
    w, h = max(260, min(780, 36 * len(txt) + 80)), 120
    cv.shape(s, e, x - w // 2, y - h // 2, WHITE, rrect(w, h, 40), POP, 6)
    tx = x - w // 2 + 40 if tail == "left" else x + w // 2 - 80
    cv.shape(s, e, tx, y + h // 2 - 4, WHITE, "m 0 0 l 40 0 l 6 44", "", 6)
    cv.text(s, e, x, y, "CBubble", txt, tags=POP, layer=7)


def card_lines(c, a, b):
    cv = Canvas(a, b)
    d = b - a
    # background: two soft circles drifting slowly
    cv.ev(a, b, "CShape", f"{{\\an7\\move(-120,720,-60,690)\\1c&H5A2E3C&\\1a&H90&\\p1}}{circle(300)}", 1)
    cv.ev(a, b, "CShape", f"{{\\an7\\move(1500,-200,1440,-160)\\1c&H6A4A1E&\\1a&H98&\\p1}}{circle(380)}", 1)
    top = 170
    if c.get("head"):
        cv.text(a, b, 960, 110, "CHead", c["head"], an=8)
        top = 300
    kind = c.get("kind", "headline")
    if kind == "headline":
        cv.text(a, b, 960, 500, "CBig", c.get("text", ""), tags=POP)
        if c.get("sub"):
            cv.text(a + 0.4, b, 960, 680, "CText", c["sub"])
    elif kind == "number":
        cv.text(a, b, 960, 470, "CHuge", c.get("value", ""), tags=POP)
        cv.text(a + 0.35, b, 960, 680, "CText", c.get("label", ""))
    elif kind == "compare":
        items = c["items"][:4]  # [[label, shown value, number], ...]
        mx = max(float(x[2]) for x in items) or 1
        gap = min(200, 560 // len(items))
        for i, (label, shown, num) in enumerate(items):
            y = top + 60 + i * gap
            st = a + 0.25 + i * min(0.5, d / (len(items) + 2))
            w = max(20, int(1000 * float(num) / mx))
            cv.text(st, b, 560, y + 45, "CLabel", label, an=6)
            cv.shape(st, b, 600, y, ACCENTS[i % 4], f"m 0 0 l {w} 0 {w} 90 0 90", "\\fscx0\\t(0,700,\\fscx100)")
            cv.text(st + 0.6, b, 620 + w, y + 45, "CVal", shown, an=4)
    elif kind == "list":
        items = c["items"][:5]
        step = min(1.2, d / (len(items) + 1))
        for i, it in enumerate(items):
            y = top + 40 + i * 130
            st = a + 0.2 + i * step
            cv.shape(st, b, 330, y + 40, ACCENTS[i % 4], circle(26), POP, an=5)
            cv.text(st, b, 390, y + 40, "CText", it, an=4)
    elif kind == "vs":
        (l_title, l_sub), (r_title, r_sub) = c["items"][:2]  # [[title, sub], [title, sub]]
        for i, (x, ttl, sub, col) in enumerate([(230, l_title, l_sub, PINK), (1090, r_title, r_sub, BLUE)]):
            st = a + 0.2 + i * 0.5
            cv.shape(st, b, x, top + 40, col, rrect(600, 460, 50), POP)
            cv.text(st, b, x + 300, top + 200, "CBig", ttl, tags=POP)
            cv.text(st + 0.3, b, x + 300, top + 360, "CText", sub, an=5)
        cv.shape(a + 1.0, b, 960, top + 270, YELLOW, circle(80), POP, 6, an=5)
        cv.text(a + 1.0, b, 960, top + 270, "CEmote", "VS", tags=POP, layer=7)
    elif kind == "timeline":
        items = c["items"][:5]  # [[year, what], ...]
        y = top + 250
        cv.shape(a, b, 160, y - 4, "&H5A5A6A&", "m 0 0 l 1600 0 1600 8 0 8", "\\fscx0\\t(0,800,\\fscx100)")
        step = min(1.4, (d - 0.5) / len(items))
        for i, (year, what) in enumerate(items):
            x = 260 + i * (1200 // max(1, len(items) - 1)) if len(items) > 1 else 960
            st = a + 0.5 + i * step
            cv.shape(st, b, x, y, ACCENTS[i % 4], circle(30), POP, 4, an=5)
            cv.text(st, b, x, y - 90, "CVal", year)
            cv.text(st + 0.2, b, x, y + 100, "CText", what, an=5)
    elif kind == "ratio":
        items = c["items"][:4]  # [[label, percent], ...]
        x0, w_all, y = 210, 1360, top + 120
        x = x0
        for i, (label, pct) in enumerate(items):
            w = int(w_all * float(pct) / 100)
            st = a + 0.3 + i * 0.45
            cv.shape(st, b, x, y, ACCENTS[i % 4], f"m 0 0 l {w} 0 {w} 140 0 140", "\\fscx0\\t(0,500,\\fscx100)")
            cv.text(st + 0.3, b, x + w // 2, y + 70, "CBubble", f"{pct}%")
            cv.text(st + 0.3, b, x + w // 2, y + 210, "CText", label, an=5)
            x += w
    elif kind == "quote":
        person(cv, a, b, 260, top + 210, c.get("shirt", BLUE), c.get("mood", "smile"))
        bubble(cv, a + 0.3, b, 1000, top + 180, c.get("text", ""))
    elif kind == "talk":
        lines = c["items"][:4]  # [["left"|"right", text], ...]
        person(cv, a, b, 180, 560, PINK, c.get("mood_left", "smile"))
        person(cv, a, b, 1520, 560, BLUE, c.get("mood_right", "smile"), flip=True)
        step = d / (len(lines) + 0.3)
        for i, (side, txt) in enumerate(lines):
            st, en = a + 0.2 + i * step, min(b, a + 0.2 + (i + 1) * step + 0.4)
            if side == "left":
                bubble(cv, st, en, 760, 300 + 110 * i, txt, "left")
            else:
                bubble(cv, st, en, 1160, 300 + 110 * i, txt, "right")
    if c.get("mascot", kind not in ("talk", "quote", "vs")):
        mascot(cv, a, b, 1650, 770, c.get("react"), 0.75)
    return cv.L


if __name__ == "__main__":  # smoke check: every kind produces events
    kinds = [{"kind": "headline", "text": "t"}, {"kind": "number", "value": "3배"},
             {"kind": "compare", "items": [["a", "1", 1], ["b", "2", 2]]}, {"kind": "list", "items": ["x", "y"]},
             {"kind": "vs", "items": [["a", "x"], ["b", "y"]]}, {"kind": "timeline", "items": [["1", "a"], ["2", "b"]]},
             {"kind": "ratio", "items": [["a", 60], ["b", 40]]}, {"kind": "quote", "text": "hi"},
             {"kind": "talk", "items": [["left", "a"], ["right", "b"]]}]
    for k in kinds:
        assert card_lines(k, 0, 5), k
    print("ok")
