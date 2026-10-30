from fastapi import FastAPI
from playwright.async_api import async_playwright
from pydantic import BaseModel
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
app = FastAPI()

class ScraperRequest(BaseModel):
    link: str

@app.post("/scrape_multiple/{module_num}")
async def scrape_multiple(coursera_link: ScraperRequest, module_num: int):
    async with async_playwright() as pw:
        open_module = module_num
        browser = await pw.chromium.launch()
        context = await browser.new_context(viewport={"width": 1280, "height": 800}, storage_state="auth.json")
        page = await context.new_page()
        main_url = coursera_link.link
        await page.goto(f"{main_url}#authMode=login")
        await page.locator(".cds-113.cds-button-disableElevation.cds-button-primary.css-1374c0a").click()
        modules = page.locator('li[data-testid="rc-WeekNavigationItem"]')
        await modules.first.wait_for(state="attached", timeout=30000)
        module_list = []
        for module in await modules.all():
            module_list.append(f'https://www.coursera.org{await module.locator('a').get_attribute('href')}')

        await page.goto(module_list[open_module-1])
        topics = page.locator('li[data-testid="WeekSingleItemDisplay-lecture"]')
        await topics.first.wait_for(state="attached", timeout=30000)

        topic_list = []
        print(f"Count: {await topics.count()}")
        for topic in await topics.all():
            topic_list.append(f'https://www.coursera.org{await topic.locator('a').get_attribute('href')}')
        opened = False
        transcript_list = []
        for x in range(await topics.count()):
            await page.goto(topic_list[x])
            await page.wait_for_load_state("domcontentloaded")
            title = page.locator(".css-1bdse57")
            
            title_name = await title.inner_text()
            print(title_name)

            if await page.get_by_role("dialog").filter(has_text="You've completed today's goal").is_visible():
                await page.get_by_role("button", name="Continue learning").click()

            if not opened:
                await page.locator('button[data-testid="item-tool-panel-button-files"]').click()
                opened = True

            link = page.locator('a[data-click-key="open_course_home.focused_lex_video_item.click.focused_lex_download_transcript"]')
            
            await link.wait_for()
            href = await link.get_attribute("href")
            response = await page.request.get(f"https://www.coursera.org{href}")
            text = (await response.text()).strip()
            transcript_list.append({ title_name: text })
            print(transcript_list)
        await browser.close()
    return transcript_list

@app.get("/test")
async def test():
    return "Successfull Test"

@app.post("/scraper_single")
async def scrape_single(module_link: ScraperRequest):
    async with async_playwright() as pw:
        link = module_link.link
        browser = await pw.chromium.launch()
        context = await browser.new_context(viewport={"width": 1280, "height": 800}, storage_state="auth.json")
        page = await context.new_page()
        await page.goto(f"{link}#authMode=login")
        modules = page.locator(".css-1psltl0").first
        await modules.first.wait_for(state="attached", timeout=30000)

        if await page.get_by_role("dialog").filter(has_text="You've completed today's goal").is_visible():
            await page.get_by_role("button", name="Continue learning").click()

        await page.locator('button[data-testid="item-tool-panel-button-files"]').click()
        link = page.locator('a[data-click-key="open_course_home.focused_lex_video_item.click.focused_lex_download_transcript"]')

        await link.wait_for()
        href = await link.get_attribute("href")
        response = await page.request.get(f"https://www.coursera.org{href}")
        text = (await response.text()).strip()
        print(text)
        await browser.close()
        return text