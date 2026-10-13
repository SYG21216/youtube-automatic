#!/usr/bin/env python3
"""hookscore.py - score a YouTube hook before you waste a take on it.

Five properties, 0-100 each, and a verdict that is 60% the mean and 40% the weakest one. The
weakest-link weighting is deliberate: a hook with four strong properties and one dead one is a hook
that leaks at the dead one, and averaging hides that.

    python3 hookscore.py hooks.txt            # one hook per line, ranked
    python3 hookscore.py --hook "one line"    # score a single hook
    python3 hookscore.py --json hooks.txt     # machine-readable

WHAT THIS CAN AND CANNOT TELL YOU. Measured against 74 real short-form hooks (first 15 seconds of
auto-captions, top-8 and bottom-8 by views across five channels): it separates deliberately bad
hooks from real ones well, and it separates a creator's own hits from their own misses barely at
all. Treat a low score as a reason to look again, never a high score as a promise.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORMULAS = json.load(open(os.path.join(HERE, "hooks.json")))["hooks"]

FILLER = {"basically","actually","literally","just","really","very","so","kind","sort","like",
          "guys","hey","welcome","today","video","subscribe","channel"}
VAGUE = {"amazing","incredible","insane","crazy","huge","massive","game","changer","secret",
         "powerful","ultimate","best","revolutionary","mind","blowing","unbelievable"}
CONCRETE = re.compile(r"\b(\d[\d,.]*\s?(%|k|m|x|s|m|h)?|\$\d|\d+\s?(second|minute|hour|day|week|month|year)s?)\b"
                      r"|\d[\d,.]*\s?(만\s?원|억|천만|백만|만|천|원|%|배|명|개|초|분|시간|일|주|개월|달|년|번|회|살|가지|위)"
                      r"|(한|두|세|네|다섯|열)\s?(달|번|명|시간|가지|주)|일주일|하루|만\s?원", re.I)
YOU = re.compile(r"\b(you|your|you're|youre|yourself)\b|여러분|당신|님들|구독자분", re.I)
STAKE = re.compile(r"\b(lose|lost|wasting|waste|quit|fail|broke|cost|risk|before|stop|never|die|dying|dead)\b"
                   r"|날리|날려|날린|손해|잃|망하|망한|망했|낭비|후회|실패|포기|그만두|하지 ?마|절대|위험|기 전에", re.I)
CURIOSITY = re.compile(r"\b(why|how|what|which|until|before|but|nobody|almost|except|reason|actually)\b"
                       r"|왜|어떻게|무엇|뭐가|어떤|사실은|하지만|그런데|근데|아무도|이유|비밀", re.I)
# Korean has no word boundaries worth trusting (particles glue on), so Korean lists match as substrings.
KO_VAGUE = re.compile(r"역대급|꿀팁|대박|미친|레전드|충격|소름|끝판왕|사기급|엄청난|어마어마|완벽|최고의|혁명")
KO_FILLER = re.compile(r"안녕하세요|오늘은|영상|구독|좋아요|알림|채널|그냥|진짜|정말|약간")
HANGUL = re.compile(r"[가-힣]")

def is_ko(t): return len(HANGUL.findall(t)) >= 3

def words(t): return re.findall(r"[a-z0-9'%$.]+", t.lower())

def specificity(t):
    w = words(t)
    if not w and not is_ko(t): return 0
    nums = len(CONCRETE.findall(t))
    vague = sum(1 for x in w if x in VAGUE) + len(KO_VAGUE.findall(t))
    filler = sum(1 for x in w if x in FILLER) + len(KO_FILLER.findall(t))
    s = 34 + nums * 22 - vague * 16 - filler * 5
    # proper nouns that are not sentence-initial read as named things
    s += min(18, 6 * sum(1 for x in t.split()[1:] if x[:1].isupper()))
    return max(0, min(100, s))

def address(t):
    n = len(YOU.findall(t))
    first = 30 if YOU.search(" ".join(t.split()[:6])) else 0
    return max(0, min(100, 26 + n * 20 + first))

def stakes(t):
    n = len(STAKE.findall(t))
    return max(0, min(100, 22 + n * 26 + (14 if CONCRETE.search(t) else 0)))

def curiosity(t):
    n = len(CURIOSITY.findall(t))
    q = 18 if t.strip().endswith("?") else 0
    # a hook that resolves itself has no gap left
    closed = -18 if re.search(r"\b(because|so that|which means)\b|때문에|그래서|덕분에", t, re.I) else 0
    return max(0, min(100, 24 + n * 17 + q + closed))

def brevity(t):
    if is_ko(t):
        # Korean is measured in syllables: 18-55 is ~10 seconds at a normal Korean speaking pace
        n = len(HANGUL.findall(t)) + len(re.findall(r"[A-Za-z0-9]+", t))
        if 18 <= n <= 55: return 100
        if n < 18: return max(30, 100 - (18 - n) * 6)
        return max(10, 100 - (n - 55) * 3)
    n = len(words(t))
    if n == 0: return 0
    # 9-24 words is the band a spoken hook lands in at ~150wpm inside 10 seconds
    if 9 <= n <= 24: return 100
    if n < 9:  return max(30, 100 - (9 - n) * 11)
    return max(10, 100 - (n - 24) * 7)

PROPS = [("SPECIFICITY", specificity), ("ADDRESS", address), ("STAKES", stakes),
         ("CURIOSITY", curiosity), ("BREVITY", brevity)]

def classify(t):
    best, hits = None, 0
    for f in FORMULAS:
        n = sum(1 for p in f["match"] if re.search(p, t, re.I))
        if n > hits: best, hits = f, n
    return (best["name"] if best else "Unclassified"), hits

def score(t):
    parts = {n: fn(t) for n, fn in PROPS}
    vals = list(parts.values())
    verdict = round(0.6 * (sum(vals) / len(vals)) + 0.4 * min(vals))
    name, hits = classify(t)
    return parts, verdict, name, hits

def band(v): return "STRONG" if v >= 72 else "WORKABLE" if v >= 55 else "WEAK"

def report(t, parts, verdict, name, hits):
    print(f"\n  {t.strip()}")
    print(f"  {'-' * min(72, max(20, len(t.strip())))}")
    for k, v in parts.items():
        print(f"    {k:<12} {v:3d}  {'#' * (v // 5)}")
    print(f"    {'VERDICT':<12} {verdict:3d}  {band(verdict)}")
    print(f"    formula      {name}" + (f"  ({hits} pattern{'s' if hits != 1 else ''} matched)" if hits else "  (no formula matched - that is usually a summary, not a hook)"))
    low = min(parts, key=parts.get)
    print(f"    weakest      {low} - {FIX[low]}")

FIX = {
 "SPECIFICITY": "swap one adjective for a number, a name or a date",
 "ADDRESS": "say 'you' in the first six words (Korean: 여러분/당신)",
 "STAKES": "name what it costs them to keep doing it the current way",
 "CURIOSITY": "cut the half of the sentence that answers itself",
 "BREVITY": "9 to 24 words (Korean: 18 to 55 syllables). Read it out loud and stop where you run out of breath",
}

def main():
    a = sys.argv[1:]
    as_json = "--json" in a
    a = [x for x in a if x != "--json"]
    if "--hook" in a:
        lines = [a[a.index("--hook") + 1]]
    elif a and os.path.exists(a[0]):
        lines = [l for l in open(a[0]).read().splitlines() if l.strip()]
    else:
        print(__doc__); sys.exit(1 if not a else 0)
    out = []
    for t in lines:
        parts, verdict, name, hits = score(t)
        out.append({"hook": t.strip(), "properties": parts, "verdict": verdict,
                    "band": band(verdict), "formula": name, "matched": hits})
    out.sort(key=lambda r: -r["verdict"])
    if as_json:
        print(json.dumps([{k: v for k, v in r.items() if k != "matched"} for r in out], indent=1)); return
    for r in out:
        report(r["hook"], r["properties"], r["verdict"], r["formula"], r["matched"])
    if len(out) > 1:
        print(f"\n  winner: {out[0]['hook'].strip()}  ({out[0]['verdict']}, {out[0]['band']})\n")

if __name__ == "__main__":
    main()
