"""Full-resolution stills straight from the comp (no render needed): fast review of any moment, any cut.

  python3 scripts/stills.py --comp "comp.html?lang=zh" --out review/zh 6.8 12.4 31.5 57.0
Writes review/zh_<t>.png and prints page errors. A 404 on a font, footage frame or data file is a bug. (The starter comp's
HEAD probes for OPTIONAL frames/open, frames/end and footage/demo also log 404s until those exist: that's expected.)
"""
import argparse, asyncio, os
from playwright.async_api import async_playwright

GL = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']


async def main(a):
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=GL); pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto(a.url.rstrip('/') + '/' + a.comp); await pg.wait_for_function('window.__ready', timeout=120000); await pg.evaluate('window.__ready')
        for t in a.times:
            await pg.evaluate(f'window.__seek({t})'); await pg.screenshot(path=f'{a.out}_{t:06.2f}.png')
        print(len(a.times), 'stills', 'errors:', errs[:5]); await b.close()

ap = argparse.ArgumentParser(); ap.add_argument('times', type=float, nargs='+'); ap.add_argument('--comp', default='comp.html')
ap.add_argument('--url', default='http://localhost:8777/'); ap.add_argument('--out', default='review/still')
asyncio.run(main(ap.parse_args()))
