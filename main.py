import os
from fastapi import FastAPI, Response, Query
from playwright.async_api import async_playwright

app = FastAPI()

# Default pages
DEFAULT_SOCHI_URL = os.getenv(
    "SOCHI_URL",
    "https://sochi.camera/vse-kamery/cam-323/"
)

DEFAULT_VK_EMBED_URL = os.getenv(
    "VK_EMBED_URL",
    "https://vk.com/video_ext.php?oid=874508662&id=456239018&hd=2"
)

# A normal UA helps some players behave more like a real browser
DEFAULT_UA = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
)


@app.get("/health")
async def health():
    return {"ok": True}


async def _make_screenshot(url: str, click_play: bool) -> bytes:
    """
    Open a page in headless Chromium, optionally click play, and return PNG screenshot bytes.
    Designed to work on low-resource instances (Render Free) using lightweight chromium args.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--no-zygote",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=DEFAULT_UA,
        )

        page = await context.new_page()

        # IMPORTANT: do not wait for networkidle on streaming pages
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(1500)

        if click_play:
            # Try a few common selectors for "play"
            selectors = [
                "button[aria-label*='Play']",
                "button[aria-label*='Воспроизвести']",
                ".vjs-big-play-button",
                "text=▶",
                "text=Play",
                "text=Воспроизвести",
                "div[class*='play']",
                "button[class*='play']",
            ]
            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        await el.click(timeout=1000)
                        break
                except Exception:
                    pass

            # Give the player a moment to show a frame
            await page.wait_for_timeout(2500)

        png_bytes = await page.screenshot(type="png")
        await browser.close()
        return png_bytes


@app.get("/frame")
async def frame(
    url: str = Query(default=DEFAULT_SOCHI_URL, description="Any page URL to screenshot"),
    click_play: bool = Query(default=False, description="Try clicking Play before screenshot"),
):
    """
    Generic screenshot endpoint. Good for quick tests.
    Example:
      /frame?url=https://example.com
      /frame?url=...&click_play=true
    """
    try:
        png = await _make_screenshot(url=url, click_play=click_play)
        return Response(content=png, media_type="image/png")
    except Exception as e:
        return {"error": str(e), "url": url}


@app.get("/frame_vk")
async def frame_vk(
    url: str = Query(default=DEFAULT_VK_EMBED_URL, description="VK embed URL to screenshot"),
):
    """
    VK-specific shortcut: tries to click Play automatically.
    """
    try:
        png = await _make_screenshot(url=url, click_play=True)
        return Response(content=png, media_type="image/png")
    except Exception as e:
        return {"error": str(e), "url": url}


@app.get("/debug_html")
async def debug_html(
    url: str = Query(default=DEFAULT_VK_EMBED_URL, description="Page URL to fetch HTML from"),
):
    """
    Returns a trimmed HTML snapshot (first ~50k chars).
    Useful to inspect which selectors exist for Play button, etc.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process",
                    "--no-zygote",
                ],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent=DEFAULT_UA,
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)

            html = await page.content()
            await browser.close()

        html = html[:50000]  # limit
        return Response(content=html, media_type="text/html; charset=utf-8")

    except Exception as e:
        return {"error": str(e), "url": url}
