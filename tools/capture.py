"""Chup man hinh trang ATEEZ Tracker de dung video gioi thieu (chay tren GitHub Actions)."""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://mthvu19.github.io/ateez-tracker/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "capture"
os.makedirs(OUT, exist_ok=True)


async def load_all(pg):
    h = await pg.evaluate("document.body.scrollHeight")
    y = 0
    while y < h:
        y += 600
        await pg.evaluate(f"window.scrollTo(0,{y})")
        await pg.wait_for_timeout(250)
        h = await pg.evaluate("document.body.scrollHeight")
    await pg.evaluate("window.scrollTo(0,0)")
    await pg.wait_for_load_state("networkidle")
    await pg.wait_for_timeout(800)


async def shot(pg, name, full=False):
    await pg.screenshot(path=f"{OUT}/{name}.jpg", type="jpeg", quality=92, full_page=full)
    print("saved", name)


async def news_top(pg):
    await pg.evaluate("document.getElementById('feedT').scrollIntoView({block:'start'}); window.scrollBy(0,-90)")
    await pg.wait_for_timeout(500)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---------- desktop ----------
        d = await b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1.2)
        await d.goto(URL + "#today", wait_until="networkidle")
        await load_all(d)
        await shot(d, "d_today")
        await shot(d, "d_today_full", full=True)
        for cat in ["official", "schedule", "release", "tour", "sns", "charts", "press", "video", "merch"]:
            btn = d.locator(f'[data-cat="{cat}"]')
            if await btn.count():
                await btn.first.click()
                await d.wait_for_timeout(400)
                await news_top(d)
                await shot(d, f"d_cat_{cat}")
        await d.locator('[data-cat="all"]').first.click()
        await d.locator('[data-member="San"]').first.click()
        await d.wait_for_timeout(600)
        await d.evaluate("window.scrollTo(0,0)")
        await shot(d, "d_member_san")
        await d.locator('[data-member="San"]').first.click()
        await d.goto(URL + "#photos", wait_until="networkidle")
        await load_all(d)
        await shot(d, "d_photos")
        await d.goto(URL + "#calendar", wait_until="networkidle")
        await d.locator('[data-mon="1"]').first.click()
        await d.locator('[data-day$="-12-07"]').first.click()
        await d.wait_for_timeout(500)
        await shot(d, "d_calendar")
        await shot(d, "d_calendar_full", full=True)
        await d.goto(URL + "#funfacts", wait_until="networkidle")
        await shot(d, "d_funfacts")
        # ---------- mobile ----------
        m = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                             is_mobile=True, has_touch=True)
        await m.goto(URL + "#today", wait_until="networkidle")
        await load_all(m)
        await shot(m, "m_today")
        await shot(m, "m_today_full", full=True)
        await m.goto(URL + "#calendar", wait_until="networkidle")
        await m.locator('[data-mon="1"]').first.click()
        await m.locator('[data-day$="-12-07"]').first.click()
        await m.wait_for_timeout(400)
        await shot(m, "m_calendar_full", full=True)
        await m.goto(URL + "#photos", wait_until="networkidle")
        await load_all(m)
        await shot(m, "m_photos_full", full=True)
        await b.close()


asyncio.run(main())
