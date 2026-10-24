"""Copy lint, per cut. Catches the three copy mistakes that actually happened:
  1. mixed languages in one cut   (EN copy containing CJK, ZH copy that is mostly Latin prose)
  2. CJK headline punctuation     (a trailing 。 leaves a full-width gap before the caret)
  3. off-positioning phrases       (--ban "make yourself the API" "that's me": the sister product's pitch leaking in)
It checks window.__copy AND the visible, non-monospace DOM text at sampled times (copy hard-coded outside COPY).
Monospace text is DATA (commands, output) and is exempt: it stays exactly as captured in every cut.

  python3 scripts/lint_copy.py --comp comp.html --langs en zh --ban "make yourself the API" "turn yourself into" --step 0.5
Real data rendered in the SANS face reads as copy (omni2api v2's ZH cut shows the real English SSE stream big in PingFang:
the lint flags it). Either set it in mono, capture a native-language sample for that cut, or --allow it on purpose.
"""
import argparse, asyncio, re, sys
from playwright.async_api import async_playwright

CJK = re.compile(r'[\u3000-\u303f\u3400-\u9fff\uff00-\uffef]')
LAT = re.compile(r'[A-Za-z]{3,}')
VISIBLE_TEXT = """() => { const out = new Set();
  for (const el of document.querySelectorAll('#stage *')) {
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim(); if (!own) continue;
    const cs = getComputedStyle(el); if (/mono|JBM|Menlo|Consolas/i.test(cs.fontFamily) || el.closest('pre,.win,.mono')) continue;
    let v = true; for (let n = el; n && n !== document.body; n = n.parentElement) { const s = getComputedStyle(n); if (s.visibility === 'hidden' || +s.opacity < 0.05 || s.display === 'none') { v = false; break; } }
    if (v) { const r = el.getBoundingClientRect(); if (r.width > 0 && r.right > 0 && r.left < 1920 && r.bottom > 0 && r.top < 1080) out.add(own); } }
  return [...out]; }"""


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, (dict, list)):
        for v in (o.values() if isinstance(o, dict) else o):
            yield from strings(v)


def check(lang, s, ban):
    errs = []
    if lang == 'en' and CJK.search(s): errs.append('CJK in the EN cut')
    if lang.startswith('zh'):
        if s.rstrip().endswith('。'): errs.append('trailing 。')
        if not CJK.search(s) and ' ' in s.strip() and not re.match(r'^\S+\.\S+/', s.strip()) and len(LAT.findall(s)) >= 3:
            errs.append('Latin prose in the ZH cut (fine only for product names)')
    for b in ban:
        if b.lower() in s.lower(): errs.append(f'banned phrase "{b}"')
    return errs


async def main(a):
    bad = 0
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for lang in a.langs:
            pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
            await pg.goto(f'{a.url.rstrip("/")}/{a.comp}{"&" if "?" in a.comp else "?"}lang={lang}')
            await pg.wait_for_function('window.__ready', timeout=120000); await pg.evaluate('window.__ready')
            copy = await pg.evaluate('window.__copy || {}'); dur = await pg.evaluate('window.__meta.dur')
            seen = {s: 'COPY' for s in strings(copy)}
            t = 0.0
            while t < dur:
                await pg.evaluate(f'window.__seek({t})')
                for s in await pg.evaluate(VISIBLE_TEXT): seen.setdefault(s, f'{t:.1f}s')
                t += a.step
            for s, where in seen.items():
                if s in a.allow: continue
                for e in check(lang, s, a.ban): bad += 1; print(f'[{lang}] {where}: {e}: {s!r}')
            await pg.close()
        await b.close()
    print('copy lint:', 'clean' if not bad else f'{bad} problem(s)'); sys.exit(1 if bad else 0)

ap = argparse.ArgumentParser(); ap.add_argument('--comp', default='comp.html'); ap.add_argument('--url', default='http://localhost:8777/')
ap.add_argument('--langs', nargs='+', default=['en', 'zh']); ap.add_argument('--ban', nargs='*', default=[]); ap.add_argument('--step', type=float, default=0.5)
ap.add_argument('--allow', nargs='*', default=[], help='exact strings that are DATA shown in the sans face (decide consciously)')
asyncio.run(main(ap.parse_args()))
