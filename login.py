# save_auth.py
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        context = await pw.chromium.launch_persistent_context(
            user_data_dir="coursera_profile",   
            channel="chrome",                   
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.coursera.org/?authMode=login")
        input("Log in in the browser, then press Enter here...")
        await context.storage_state(path="auth.json")
        await context.close()

asyncio.run(main())