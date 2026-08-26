import asyncio, hashlib
from playwright.async_api import async_playwright
SHA=hashlib.sha256("newtrend2026".encode()).hexdigest()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx=await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2)
        pg=await ctx.new_page()
        await pg.goto('http://localhost:8899/tap.html')
        await pg.evaluate(f'localStorage.setItem("wp_gate","{SHA}")')
        await pg.reload(); await pg.wait_for_timeout(1200)
        # filter to ファッション・アパレル and search SOWAN
        await pg.fill('#q','SOWAN'); await pg.wait_for_timeout(400)
        await pg.screenshot(path='/tmp/c1.png')
        print('SOWAN hits:', await pg.inner_text('#hits'))
        await pg.fill('#q',''); await pg.wait_for_timeout(300)
        cats=await pg.eval_on_selector_all('#cats .chip','e=>e.map(x=>x.textContent)')
        print('chips:', cats)
        await b.close()
asyncio.run(main())
