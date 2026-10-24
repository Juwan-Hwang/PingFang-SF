"""Render a seekable HTML composition frame by frame with Playwright + Chromium, with adaptive motion blur.

The comp must expose window.__ready (promise), window.__meta = {dur, fps}, window.__seek(t), window.__motion(t0, t1).
For every frame the renderer asks the comp how far the camera travels (screen px) across a 180° shutter
(half a frame). Holds (< --gap px) are one capture. Whips/zoom-throughs get S = ceil(travel / gap) sub-captures
(2..--sub) spread over the shutter and AVERAGED IN LINEAR LIGHT (sRGB → linear → mean → sRGB). Averaging in sRGB
darkens bright edges and looks like smearing, not blur.

Resumable and time-boxed: existing frames are skipped, writes are atomic (tmp + os.replace), and --max-seconds stops
cleanly so you can run it in chunks under a tool timeout and just run it again.

  python3 -m http.server 8777 --directory film &
  python3 render_film.py --comp "comp.html?lang=en" --out film/out/frames_en --workers 2
"""
import argparse, asyncio, io, math, os, time
from multiprocessing import Process
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

_u = np.arange(256) / 255.0
S2L = np.where(_u <= 0.04045, _u / 12.92, ((_u + 0.055) / 1.055) ** 2.4).astype(np.float32)


def l2s(x):
    x = np.clip(x, 0, 1)
    return np.clip(np.rint(np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055) * 255), 0, 255).astype(np.uint8)


async def work(k, n, a, deadline):
    async with async_playwright() as p:
        br = await p.chromium.launch()
        pg = await (await br.new_context(viewport={'width': a.width, 'height': a.height}, device_scale_factor=1)).new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(a.url.rstrip('/') + '/' + a.comp)
        await pg.wait_for_function('window.__ready', timeout=120000)
        await pg.evaluate('window.__ready')
        dur = await pg.evaluate('window.__meta.dur')
        N = int(math.floor(dur * a.fps))
        f1 = N if a.to is None else min(N, a.to)
        opn = 0.5 / a.fps                      # 180° shutter = half a frame interval
        done = 0
        for f in range(a.frm + k, f1, n):
            if time.time() > deadline:
                break
            path = f'{a.out}/{f:05d}.jpg'
            if os.path.exists(path):
                continue
            t = f / a.fps
            far = await pg.evaluate(f'window.__motion({max(0, t - opn / 2)}, {min(dur - 1e-4, t + opn / 2)})')
            S = 1 if far < a.gap else min(a.sub, max(2, math.ceil(far / a.gap)))
            if S == 1:
                await pg.evaluate(f'window.__seek({t})')
                png = await pg.screenshot(type='png')          # PNG from the browser, JPEG q96 on disk: one lossy step only
                Image.open(io.BytesIO(png)).convert('RGB').save(path + '.tmp.jpg', quality=a.quality)
            else:
                acc = None
                for s in range(S):
                    ts = min(dur - 1e-4, max(0, t + opn * ((s + 0.5) / S - 0.5)))
                    await pg.evaluate(f'window.__seek({ts})')
                    lin = S2L[np.asarray(Image.open(io.BytesIO(await pg.screenshot(type='png'))).convert('RGB'))]
                    acc = lin if acc is None else acc + lin
                Image.fromarray(l2s(acc / S)).save(path + '.tmp.jpg', quality=a.quality)
            os.replace(path + '.tmp.jpg', path)
            done += 1
            if done % 60 == 0:
                print(f'worker {k}: frame {f}/{f1}', flush=True)
        if errs:
            print('page errors', errs[:3], flush=True)
        await br.close()


def run(k, n, a, deadline):
    asyncio.run(work(k, n, a, deadline))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://localhost:8777/', help='static server serving the film/ folder (fetch() needs http, not file://)')
    ap.add_argument('--comp', default='comp.html', help='page + query, e.g. "comp.html?lang=zh"')
    ap.add_argument('--out', default='film/out/frames')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--width', type=int, default=1920); ap.add_argument('--height', type=int, default=1080)
    ap.add_argument('--workers', type=int, default=2, help='parallel Chromium instances (2–3 on a laptop-class sandbox)')
    ap.add_argument('--from', dest='frm', type=int, default=0); ap.add_argument('--to', type=int, default=None)
    ap.add_argument('--gap', type=float, default=40, help='px of travel per sub-frame before blur kicks in')
    ap.add_argument('--sub', type=int, default=5, help='max sub-frames per frame')
    ap.add_argument('--quality', type=int, default=96)
    ap.add_argument('--max-seconds', type=float, default=1100, help='stop cleanly after this long; rerun to resume')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    deadline = time.time() + a.max_seconds
    ps = [Process(target=run, args=(k, a.workers, a, deadline)) for k in range(a.workers)]
    [p.start() for p in ps]; [p.join() for p in ps]
    print('rendered', len([x for x in os.listdir(a.out) if x.endswith('.jpg') and not x.endswith('.tmp.jpg')]), 'frames in', a.out)
