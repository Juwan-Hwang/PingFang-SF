import sys, asyncio, time, os
from playwright.async_api import async_playwright
# usage: cap.py outdir fps start_frame end_frame   OR  cap.py outdir times t1,t2,...
async def main():
    out=sys.argv[1]; os.makedirs(out,exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--allow-file-access-from-files","--disable-web-security","--font-render-hinting=none","--disable-gpu","--force-color-profile=srgb"])
        pg=await b.new_page(viewport={"width":1920,"height":1080},device_scale_factor=1)
        msgs=[]; pg.on("console",lambda m:msgs.append(m.text)); pg.on("pageerror",lambda e:msgs.append("ERR "+str(e)))
        await pg.goto("file://"+os.path.abspath("promo.html"))
        await pg.wait_for_function("window.READY===true",timeout=120000)
        if sys.argv[2]=="times":
            ts=[float(x) for x in sys.argv[3].split(",")]; names=[f"t{t:05.2f}.png" for t in ts]
        else:
            fps=int(sys.argv[2]); a,bb=int(sys.argv[3]),int(sys.argv[4]); ts=[i/fps for i in range(a,bb)]; names=[f"f{i:05d}.png" for i in range(a,bb)]
        t0=time.time()
        for t,n in zip(ts,names):
            await pg.evaluate(f"render({t})")
            await pg.screenshot(path=os.path.join(out,n),type="png")
        print("done",len(ts),"in",round(time.time()-t0,1),"s"); print("\n".join(msgs[:20]))
        await b.close()
asyncio.run(main())
