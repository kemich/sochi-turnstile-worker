import os
from fastapi import FastAPI, Response, Query
from playwright.async_api import async_playwright

# ⚠️ ВАЖНО — создаём app
app = FastAPI()

DEFAULT_URL = os.getenv(
    "CAMERA_URL",
    "https://sochi.camera/vse-kamery/cam-323/"
)


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/frame")
async def frame(url: str = Query(default=DEFAULT_URL)):
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

            page = await browser.new_page(viewport={"width": 1280, "height": 720})

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)

            png_bytes = await page.screenshot(type="png")

            await browser.close()

        return Response(content=png_bytes, media_type="image/png")

    except Exception as e:
        return {"error": str(e)}
