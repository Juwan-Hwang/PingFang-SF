"""Dump a comp's timeline events (window.__events) and meta to JSON. The score and the SFX are placed from this file,
so picture, music and sound effects can never drift apart.

  python3 scripts/dump_events.py --comp "comp.html?lang=en" --out audio/events_en.json
Output: {"meta": {"dur": .., "fps": .., "bpm": ..}, "events": [{"t": 2.0, "kind": "hit"}, ...]}
"""
import argparse, asyncio, json, os
from collections import Counter
from playwright.async_api import async_playwright


async def main(a):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(a.url.rstrip('/') + '/' + a.comp)
        await pg.wait_for_function('!!window.__ready && typeof window.__events === "function"', timeout=120000)
        await pg.evaluate('window.__ready')
        ev = await pg.evaluate('window.__events()')
        meta = await pg.evaluate('window.__meta')
        await b.close()
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump({'meta': meta, 'events': sorted(ev, key=lambda e: e['t'])}, open(a.out, 'w'), indent=1)
    print(a.out, len(ev), 'events', dict(Counter(e['kind'] for e in ev)), 'dur', meta.get('dur'), 'errors', errs[:3])

ap = argparse.ArgumentParser()
ap.add_argument('--comp', default='comp.html'); ap.add_argument('--url', default='http://localhost:8777/')
ap.add_argument('--out', default='audio/events.json')
asyncio.run(main(ap.parse_args()))
