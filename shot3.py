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
        print('sort default:', await pg.input_value('#sort'))
        print('first 3 products:', await pg.eval_on_selector_all('.pcard .pmeta .tag','e=>e.slice(0,3).map(x=>x.textContent)'))
        await pg.screenshot(path='/tmp/n1.png')
        await pg.evaluate("document.querySelector('#seg button[data-v=c]').click()")
        await pg.wait_for_timeout(400)
        print('first 3 campaigns:', await pg.eval_on_selector_all('.ccard .cname','e=>e.slice(0,3).map(x=>x.textContent)'))
        print('sort options visible:', await pg.eval_on_selector_all('#sort option','e=>e.filter(x=>!x.hidden).map(x=>x.textContent)'))
        await pg.screenshot(path='/tmp/n2.png')
        print('errors', errs[:5]); await b.close()
asyncio.run(main())
