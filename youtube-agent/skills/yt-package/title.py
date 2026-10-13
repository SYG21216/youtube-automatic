#!/usr/bin/env python3
"""title.py - lint a YouTube title and thumbnail pairing before you publish it.

    python3 title.py --title "..." --thumb "AI RAN IT"
    python3 title.py titles.txt            # one per line, ranked
    python3 title.py --title "..." --json

The pairing is the unit, not the title. A title that repeats the thumbnail text wastes half the
click surface, and that is the single most common mistake this checks for.

Length: YouTube truncates around 60 characters on desktop search and around 40 on a mobile home
feed. Both limits are reported because they are different failures - a desktop truncation loses the
tail, a mobile one can lose the subject. Limits are in display width: one Hangul syllable counts as
two Latin characters, which is roughly how much pixel width it takes.
"""
import json, re, sys, os, unicodedata

DESKTOP, MOBILE, HARD = 60, 40, 100
VAGUE = {"amazing","incredible","insane","crazy","huge","massive","ultimate","best","powerful",
         "secret","revolutionary","mindblowing","epic","perfect","complete","everything"}
# Korean hype words match as substrings so "역대급으로" still counts
KO_VAGUE = re.compile(r"역대급|꿀팁|대박|미친|레전드|충격|소름|끝판왕|사기급|엄청난|어마어마|완벽|최고의|혁명|총정리|필수")
STOP = {"the","a","an","of","for","to","in","on","and","or","is","are","with","your","you","my","i",
        "this","that","it","how","what","why",
        "이","그","저","이거","그거","더","꼭","진짜","정말","왜","어떻게","나","내","제","저의",
        "당신","여러분","것","수","하는","하기","이렇게"}
# longest first so "에서는" is stripped before "는"
JOSA = sorted("에서는 으로는 이라는 에서 에게 한테 으로 까지 부터 처럼 보다 라는 이랑 하고 "
              "은 는 이 가 을 를 에 의 도 만 로 와 과 랑".split(), key=len, reverse=True)

def strip_josa(w):
    # ponytail: suffix strip, not a morphological analyzer - "고양이" loses its 이. Both sides of the
    # duplicate check are stripped the same way, so it still compares like with like.
    if re.fullmatch(r"[0-9]*[가-힣]+", w):
        for j in JOSA:
            if w.endswith(j) and len(w) > len(j): return w[:-len(j)]
    return w

def words(t): return [strip_josa(w) for w in re.findall(r"[a-z0-9'가-힣]+", t.lower())]

def width(t): return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in t)

def cut(t, w):
    out, n = "", 0
    for c in t:
        n += width(c)
        if n > w: break
        out += c
    return out

def check(title, thumb=None):
    t = title.strip()
    n, w = len(t), width(t)
    issues, good = [], []
    if n > HARD: issues.append(("length", f"{n} characters - YouTube's hard limit is {HARD}"))
    elif w > DESKTOP: issues.append(("length", f"width {w} - desktop search cuts near {DESKTOP}"))
    else: good.append(f"width {w}, inside the {DESKTOP} desktop cut")
    if w > MOBILE:
        head = cut(t, MOBILE).rsplit(" ", 1)[0]
        issues.append(("mobile", f'a mobile feed shows about "{head}..." - check the subject survives'))
    caps = [w for w in t.split() if len(w) > 2 and w.isupper()]
    if len(caps) > 2: issues.append(("shouting", f"{len(caps)} all-caps words - two is the ceiling before it reads as spam"))
    elif caps: good.append(f"{len(caps)} all-caps word for emphasis")
    v = [x for x in words(t) if x in VAGUE] + KO_VAGUE.findall(t)
    if v: issues.append(("vague", f"{', '.join(sorted(set(v)))} - swap for a number, a name or a date"))
    nums = re.findall(r"\d[\d,.]*%?|(?:한|두|세|네|다섯|열)\s?(?:달|번|가지|명|주)|일주일|하루", t)
    if nums: good.append(f"carries a concrete figure ({', '.join(nums[:3])})")
    else: issues.append(("no-number", "no number, date or name - the most reliable single fix"))
    if t.endswith("?"): good.append("open question in the title")
    front = [x for x in words(t)[:3] if x not in STOP]
    if not front: issues.append(("front-load", "the first three words are all filler - move the subject forward"))
    if thumb:
        tw, hw = set(words(t)) - STOP, set(words(thumb)) - STOP
        shared = tw & hw
        if shared:
            issues.append(("duplicate", f"thumbnail repeats the title on {', '.join(sorted(shared))} - "
                                        "the thumbnail should say what the title does not"))
        else:
            good.append("thumbnail and title carry different words")
        if len(words(thumb)) > 4:
            issues.append(("thumb-length", f"{len(words(thumb))} words on the thumbnail - three is the ceiling at feed size"))
    score = max(0, min(100, 100 - 14 * len(issues) + 4 * len(good)))
    return {"title": t, "chars": n, "width": w, "score": score, "issues": issues, "good": good}

def show(r):
    print(f'\n  "{r["title"]}"')
    print(f"  {r['chars']} chars, width {r['width']}   score {r['score']}/100")
    for k, m in r["issues"]: print(f"    x  {k:<12} {m}")
    for m in r["good"]:      print(f"    ok              {m}")

def main():
    a = sys.argv[1:]
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    thumb = a[a.index("--thumb") + 1] if "--thumb" in a else None
    if "--title" in a:
        rows = [check(a[a.index("--title") + 1], thumb)]
    elif a and os.path.exists(a[0]):
        rows = [check(l, thumb) for l in open(a[0]).read().splitlines() if l.strip()]
    else:
        print(__doc__); sys.exit(1)
    rows.sort(key=lambda r: -r["score"])
    if as_json: print(json.dumps(rows, indent=1)); return
    for r in rows: show(r)
    print()

if __name__ == "__main__":
    main()
