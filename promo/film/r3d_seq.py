"""Render a three.js shot (o3d.html) to a JPEG sequence with real shutter blur.

Each frame = mean of --sub renders spread across a 180° shutter, averaged in LINEAR light. WebGL runs on SwiftShader
(software) so it works headless with no GPU; it is slow (≈1 s per sub-frame at 1080p) and that is fine: 3D is offline.

  python3 r3d_seq.py open 6.0 film/frames/open --sub 3
  python3 r3d_seq.py end 2.5 film/frames/end --sub 3 --handoff "comp.html"     # ppu/sx/sy/ox/oy read from comp's __handoff()
  python3 r3d_seq.py end 2.5 film/frames/end --q "&ppu=0.8&sx=960&sy=500"       # or pass them yourself

Frames are named %04d.jpg; existing frames are skipped (resumable).
"""
import argparse, asyncio, io, os, time
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

_u = np.arange(256) / 255.0
S2L = np.where(_u <= 0.04045, _u / 12.92, ((_u + 0.055) / 1.055) ** 2.4).astype(np.float32)
GL_ARGS = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']


def l2s(x):
    x = np.clip(x, 0, 1)
    return np.clip(np.rint(np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055) * 255), 0, 255).astype(np.uint8)


async def handoff_query(p, url, comp):
    b = await p.chromium.launch()
    pg = await b.new_page(viewport={'width': 1920, 'height': 1080})
    await pg.goto(url.rstrip('/') + '/' + comp)
    await pg.wait_for_function('window.__ready', timeout=120000)
    await pg.evaluate('window.__ready')
    h = await pg.evaluate('window.__handoff()')
    await b.close()
    q = ''.join(f'&{k}={v}' for k, v in h.items())
    print('handoff', q, flush=True)
    return q


async def main(a):
    os.makedirs(a.outdir, exist_ok=True)
    async with async_playwright() as p:
        q = a.q + (await handoff_query(p, a.url, a.handoff) if a.handoff else '')
        b = await p.chromium.launch(args=GL_ARGS)
        pg = await b.new_page(viewport={'width': a.width, 'height': a.height})
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(f'{a.url.rstrip("/")}/{a.page}?shot={a.shot}{q}')
        try:
            await pg.wait_for_function('window.__ready===true', timeout=60000)
        except Exception:
            raise SystemExit(f'3D page never became ready: {errs[:3]}')
        n = int(round(a.dur * a.fps))
        f1 = n if a.to is None else min(n, a.to)
        t0 = time.time()
        for f in range(a.frm, f1):
            path = f'{a.outdir}/{f:04d}.jpg'
            if os.path.exists(path):
                continue
            t = f / a.fps
            offs = [0.0] if a.sub <= 1 else [((k / (a.sub - 1)) - 0.5) * (0.5 / a.fps) for k in range(a.sub)]
            acc = None
            for o in offs:
                await pg.evaluate(f'window.__seek({max(0, t + o)})')
                lin = S2L[np.asarray(Image.open(io.BytesIO(await pg.screenshot(type='png'))).convert('RGB'))]
                acc = lin if acc is None else acc + lin
            Image.fromarray(l2s(acc / len(offs))).save(path + '.tmp.jpg', quality=95)
            os.replace(path + '.tmp.jpg', path)
            if f % 30 == 0:
                print(a.shot, f, '/', f1, round(time.time() - t0, 1), 's', flush=True)
        if errs:
            print('page errors', errs[:3])
        await b.close()

ap = argparse.ArgumentParser()
ap.add_argument('shot'); ap.add_argument('dur', type=float); ap.add_argument('outdir')
ap.add_argument('--page', default='o3d.html'); ap.add_argument('--url', default='http://localhost:8777/')
ap.add_argument('--sub', type=int, default=3); ap.add_argument('--fps', type=int, default=30)
ap.add_argument('--width', type=int, default=1920); ap.add_argument('--height', type=int, default=1080)
ap.add_argument('--q', default='', help='extra query, e.g. "&ppu=0.8&sx=960&sy=500"')
ap.add_argument('--handoff', default=None, help='comp page to read window.__handoff() from, e.g. "comp.html"')
ap.add_argument('--from', dest='frm', type=int, default=0); ap.add_argument('--to', type=int, default=None)
asyncio.run(main(ap.parse_args()))
