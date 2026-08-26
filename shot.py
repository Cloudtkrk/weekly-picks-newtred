import asyncio, hashlib, sys
from playwright.async_api import async_playwright
SHA=hashlib.sha256("newtrend2026".encode()).hexdigest()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx=await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2)
        pg=await ctx.new_page()
        await pg.goto('http://localhost:8899/tap.html')
        await pg.evaluate(f'localStorage.setItem("wp_gate","{SHA}")')
        await pg.reload(); await pg.wait_for_timeout(1500)
        errs=[]
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
        await pg.screenshot(path='/tmp/tap1.png')
        await pg.evaluate("document.querySelector('#seg button[data-v=c]').click()")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path='/tmp/tap2.png')
        await pg.evaluate("document.querySelector('.ccard').click()")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path='/tmp/tap3.png')
        print('hits', await pg.inner_text('#hits'))
        print('errors', errs[:5])
        await b.close()
asyncio.run(main())
