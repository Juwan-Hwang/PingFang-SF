import asyncio,sys,os
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--allow-file-access-from-files","--font-render-hinting=none","--force-color-profile=srgb"])
        for name,w,h in (('hero',1600,760),('scripts',1600,None)):
            pg=await b.new_page(viewport={"width":w,"height":h or 800})
            await pg.goto("file://"+os.path.abspath(name+".html")); await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(500)
            await pg.screenshot(path=name+".png",full_page=True)
        await b.close()
asyncio.run(main())
