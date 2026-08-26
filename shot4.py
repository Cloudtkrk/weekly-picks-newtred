import asyncio, hashlib
from playwright.async_api import async_playwright
SHA=hashlib.sha256("newtrend2026".encode()).hexdigest()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        ctx=await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2)
        pg=await ctx.new_page(); errs=[]
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
        await pg.goto('http://localhost:8899/tap.html')
        await pg.evaluate(f'localStorage.setItem("wp_gate","{SHA}")')
        await pg.reload(); await pg.wait_for_timeout(1200)
        await pg.evaluate("document.querySelector('#seg button[data-v=c]').click()")
        await pg.wait_for_timeout(600)
        print('titles:', await pg.eval_on_selector_all('.ccard .cname','e=>e.slice(0,5).map(x=>x.textContent)'))
        print('imgs  :', await pg.eval_on_selector_all('.ccard img','e=>e.length'))
        await pg.screenshot(path='/tmp/s1.png')
        await pg.evaluate("document.querySelector('.ccard').click()")
        await pg.wait_for_timeout(500)
        print('filter banner:', await pg.inner_text('#af'))
        print('errors:', errs[:3])
        await b.close()
asyncio.run(main())
