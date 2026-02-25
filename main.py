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

            # ⚡ ВАЖНО: НЕ networkidle
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Просто подождать немного
            await page.wait_for_timeout(4000)

            png_bytes = await page.screenshot(type="png")

            await browser.close()

        return Response(content=png_bytes, media_type="image/png")

    except Exception as e:
        return {"error": str(e)}
