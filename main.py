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
            print(await title.inner_text())
            transcript_list.append({await title.inner_text(): []})

            if await page.get_by_role("dialog").filter(has_text="You've completed today's goal").is_visible():
                await page.get_by_role("button", name="Continue learning").click()

            if not opened:
                transcript = page.locator('button[data-testid="item-tool-panel-button-transcript"]')
                await transcript.wait_for(state="visible", timeout=30000)
                await transcript.scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)
                await transcript.click()
                opened = True
        
            phrases = page.locator('div.phrases')
            await phrases.first.wait_for(state="attached", timeout=30000)
            subs = phrases.locator('.rc-Phrase.css-nhymx3')
            await subs.first.wait_for(state="attached", timeout=30000)
            print(f"Sub Counts: {await subs.count()}")
            for phrase in await subs.locator('span').all():
                text = await phrase.inner_text()
                transcript_list[x][await title.inner_text()].append(text.replace("\u200b", "").strip())
                print(await phrase.inner_text())
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

        await page.locator('button[data-testid="item-tool-panel-button-transcript"]').click()
        transcription_list = await page.locator(".css-mlsl36").all()
        extracted_list = []
        for phrase in transcription_list:
            text = await phrase.inner_text()
            print(text)
            extracted_list.append(text)
        return ' '.join(extracted_list)