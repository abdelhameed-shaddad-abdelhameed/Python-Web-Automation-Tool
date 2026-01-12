# jaco_async_incognito_lowdata.py
# Requirements:
#   pip install playwright
#   playwright install
#
# Purpose:
#   Same as previous async script but blocks images, media (video/audio) and fonts to reduce data usage.
#   Reads numbers from "numbers.txt" (one per line).
#   Uses Playwright async API + asyncio with CONCURRENT=3 incognito contexts.
#
# Note:
#   Blocking images/media may alter page layout slightly but will significantly reduce bandwidth.

import re
import asyncio
import random
import time
from typing import Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, Route, Request

# ---------- Config ----------
CONCURRENT = 1
INPUT_FILE = "numbers.txt"
LAUNCH_OPTIONS = {
    "headless": False,  # visible windows (set True for headless)
    "args": [
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
    ],
}
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
]

COUNTRY_MAP = {
    "20": "Egypt",
    "968": "Oman",
    "961": "Lebanon",
    "218": "Libya",
    "964": "Iraq",
    "216": "Tunisia",
    "1": "United States",
    "44": "United Kingdom",
    "55": "Brazil",
    "591": "Bolivia",
    "355": "Albania",
    "213": "Algeria",
    "380": "Ukraine",
    "7": "Russia",
    "61": "Australia",
    "49": "Germany",
    "33": "France",
    "39": "Italy",
    "34": "Spain",
    "965": "Kuwait",
    "966": "Saudi Arabia",
    "971": "United Arab Emirates",
    "972": "Israel",
}
SORTED_CODES = sorted(COUNTRY_MAP.keys(), key=lambda x: -len(x))

# ---------- Stealth JS ----------
STEALTH_JS = """
(() => {
  try {
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3] });
    if (!window.chrome) window.chrome = { runtime: {} };
    const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
    if (originalQuery) {
      window.navigator.permissions.query = (params) => (
        params.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(params)
      );
    }
    try {
      const getParameter = WebGLRenderingContext.prototype.getParameter;
      WebGLRenderingContext.prototype.getParameter = function(parameter) {
        if (parameter === 37445) { return 'Intel Inc.'; }
        if (parameter === 37446) { return 'Intel Iris OpenGL Engine'; }
        return getParameter.call(this, parameter);
      };
    } catch (e) {}
  } catch (e) {}
})();
"""

# ---------- Helpers ----------
def normalize_number(raw: str) -> str:
    return re.sub(r"\D", "", raw.strip())

def split_country_local(number: str) -> Tuple[Optional[str], str]:
    if not number:
        return None, ""
    for code in SORTED_CODES:
        if number.startswith(code):
            return code, number[len(code):]
    for l in (3,2,1):
        if len(number) > l:
            return number[:l], number[l:]
    return None, number

async def human_move_mouse_random(page: Page, duration=0.8, steps=10):
    try:
        viewport = page.viewport_size or {"width": 1280, "height": 720}
        w, h = viewport["width"], viewport["height"]
        sx = random.randint(int(w*0.15), int(w*0.85))
        sy = random.randint(int(h*0.15), int(h*0.85))
        ex = random.randint(int(w*0.15), int(w*0.85))
        ey = random.randint(int(h*0.15), int(h*0.85))
        for i in range(steps):
            nx = int(sx + (ex-sx) * (i / max(1, steps-1)) + random.uniform(-8,8))
            ny = int(sy + (ey-sy) * (i / max(1, steps-1)) + random.uniform(-8,8))
            try:
                await page.mouse.move(nx, ny)
            except Exception:
                pass
            await asyncio.sleep(duration / max(1, steps))
    except Exception:
        pass

async def human_type(page: Page, selector: str, text: str, min_delay_ms=30, max_delay_ms=100):
    try:
        try:
            await page.focus(selector)
        except Exception:
            pass
        for ch in text:
            try:
                await page.keyboard.insert_text(ch)
            except Exception:
                try:
                    await page.type(selector, ch, timeout=2000)
                except Exception:
                    await page.evaluate(
                        """(sel, c) => {
                            const el = document.querySelector(sel);
                            if (el) el.value = (el.value || '') + c;
                        }""",
                        selector, ch
                    )
            await asyncio.sleep(random.uniform(min_delay_ms, max_delay_ms) / 1000.0)
    except Exception:
        pass

async def choose_country_on_page(page: Page, country_code: Optional[str], country_name_hint: Optional[str]) -> bool:
    if not country_code:
        return False
    open_selectors = [
        "button[aria-label='Country']",
        "button:has-text('+')",
        "div[class*='country']",
        "div[class*='select']",
        "span:has-text('+')",
        "text=/\\+[0-9]{1,4}/",
    ]
    opened = False
    for sel in open_selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click(timeout=2500)
                opened = True
                await asyncio.sleep(0.18)
                break
        except Exception:
            continue
    if not opened:
        try:
            el = await page.locator("use").nth(2).element_handle()
            if el:
                await el.click()
                opened = True
        except Exception:
            pass
    if not opened:
        return False
    await asyncio.sleep(0.2)
    try:
        inputs = await page.query_selector_all("input[type='search'], input[placeholder*='Search'], input[placeholder*='search']")
        if inputs:
            try:
                await inputs[0].fill("+" + country_code)
            except Exception:
                pass
            await asyncio.sleep(0.15)
            el = await page.query_selector(f"text=+{country_code}") or (await page.query_selector(f"text={country_name_hint}") if country_name_hint else None)
            if el:
                await el.click()
                return True
    except Exception:
        pass
    try:
        if country_name_hint:
            el = await page.locator(f"text={country_name_hint}").first
            if el:
                await el.click(timeout=2500)
                return True
    except Exception:
        pass
    try:
        el = await page.locator(f"text=+{country_code}").first
        if el:
            await el.click(timeout=2500)
            return True
    except Exception:
        pass
    try:
        matches = await page.locator(f"text={country_code}")
        if await matches.count() > 0:
            await matches.nth(0).click()
            return True
    except Exception:
        pass
    return False

# ---------- Network routing: block images/media/fonts ----------
async def block_heavy_requests(route: Route, request: Request):
    """
    Abort requests whose resource type is image, media (video/audio) or font
    to reduce bandwidth usage.
    """
    try:
        rtype = request.resource_type
        if rtype in ("image", "media", "font"):
            await route.abort()
        else:
            await route.continue_()
    except Exception:
        # safe fallback: continue
        try:
            await route.continue_()
        except Exception:
            pass

# ---------- Core worker ----------
async def process_number_sem(browser: Browser, sem: asyncio.Semaphore, raw_number: str, idx:int):
    async with sem:
        number = normalize_number(raw_number)
        if not number:
            print(f"[{idx}] skip empty/invalid line")
            return
        country_code, local_part = split_country_local(number)
        country_name = COUNTRY_MAP.get(country_code)
        user_agent = random.choice(USER_AGENTS)
        viewport = {"width": random.choice([1280,1366,1440]), "height": random.choice([720,780,900])}

        print(f"[{idx}] Start -> raw='{raw_number.strip()}', country='{country_code}', local='{local_part}', name='{country_name}'")

        context = await browser.new_context(user_agent=user_agent, viewport=viewport, locale="en-US",
                                            timezone_id="UTC", java_script_enabled=True, ignore_https_errors=True)
        # add stealth
        await context.add_init_script(STEALTH_JS)

        # set up route to block images/media/fonts for all pages in this context
        await context.route("**/*", block_heavy_requests)

        page = await context.new_page()
        try:
            await page.goto("https://jaco.live/", timeout=30000)
            await asyncio.sleep(random.uniform(0.25,0.9))
            await human_move_mouse_random(page, duration=0.8, steps=8)

            # click Login
            try:
                btn = await page.get_by_role("button", name="Login")
                await btn.click(timeout=7000)
            except Exception:
                try:
                    await page.click("text=Login", timeout=7000)
                except Exception:
                    pass

            await asyncio.sleep(random.uniform(0.2,0.6))
            await human_move_mouse_random(page, duration=0.6, steps=6)

            # Click Continue with Phone
            try:
                await page.get_by_text("Continue with Phone").click(timeout=7000)
            except Exception:
                try:
                    await page.click("text=/Continue with/i", timeout=5000)
                except Exception:
                    pass

            await asyncio.sleep(random.uniform(0.2,0.6))

            ok = await choose_country_on_page(page, country_code, country_name)
            if not ok:
                print(f"[{idx}] WARN: couldn't select country {country_code} ({country_name}) — proceeding to fill local part")

            await asyncio.sleep(0.2)

            # Fill number
            filled = False
            try:
                textbox = page.get_by_role("textbox", name="Enter your number")
                await textbox.wait_for(state="visible", timeout=6000)
                await textbox.click()
                await asyncio.sleep(0.08)
                await human_type(page, "input[type='tel'], input[placeholder*='number'], input[placeholder*='phone']", local_part)
                filled = True
            except Exception:
                selectors = ["input[type='tel']", "input[placeholder*='number']", "input[placeholder*='phone']", "input[name*='phone']"]
                for sel in selectors:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            await el.click()
                            await asyncio.sleep(0.08)
                            await human_type(page, sel, local_part)
                            filled = True
                            break
                    except Exception:
                        continue
            if not filled:
                print(f"[{idx}] WARN: phone input not found for {raw_number.strip()}")

            await asyncio.sleep(0.25)
            await human_move_mouse_random(page, duration=0.5, steps=6)

            # Click Send Code
            try:
                await page.get_by_role("button", name="Send Code").click(timeout=7000)
                print(f"[{idx}] INFO: Clicked Send Code for {raw_number.strip()}")
            except Exception:
                try:
                    await page.click("text=Send Code", timeout=5000)
                    print(f"[{idx}] INFO: Clicked Send Code (fallback) for {raw_number.strip()}")
                except Exception as e:
                    print(f"[{idx}] WARN: couldn't click Send Code: {e}")


            await asyncio.sleep(random.uniform(8.0,10.0))

            # clear cookies & storage
            try:
                await context.clear_cookies()
            except Exception:
                pass
            try:
                await page.evaluate("() => { localStorage.clear(); sessionStorage.clear(); }")
            except Exception:
                pass

            await asyncio.sleep(0.25 + random.random()*0.6)

        except Exception as e:
            print(f"[{idx}] ERROR: {e}")
        finally:
            try:
                await page.close()
            except Exception:
                pass
            try:
                await context.close()
            except Exception:
                pass
            print(f"[{idx}] Finished -> {raw_number.strip()}")

# ---------- Runner ----------
async def main():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        print(f"{INPUT_FILE} not found. Put your numbers file in the same folder.")
        return

    print(f"Total numbers: {len(lines)}. Running up to {CONCURRENT} concurrent contexts (images/media/fonts blocked).")

    sem = asyncio.Semaphore(CONCURRENT)
    async with async_playwright() as p:
        browser = await p.chromium.launch(**LAUNCH_OPTIONS)
        tasks = []
        for idx, raw in enumerate(lines, start=1):
            task = asyncio.create_task(process_number_sem(browser, sem, raw, idx))
            tasks.append(task)
            await asyncio.sleep(0.12 + random.random()*0.15)

        await asyncio.gather(*tasks, return_exceptions=True)

        try:
            await browser.close()
        except Exception:
            pass

    print("All done.")

if __name__ == "__main__":
    asyncio.run(main())
