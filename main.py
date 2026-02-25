import os
from fastapi import FastAPI, Response, Query
from playwright.async_api import async_playwright

app = FastAPI()

DEFAULT_URL = os.getenv("CAMERA_URL", "https://sochi.camera/vse-kamery/cam-323/")

@app.get("/health")
async def health():
    return {"ok": True}

@app.get("/frame")
async def frame(url: str = Query(default=DEFAULT_URL)):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(1500)
        png_bytes = await page.screenshot(full_page=False, type="png")
        await browser.close()
    return Response(content=png_bytes, media_type="image/png")
