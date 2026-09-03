from app.services.resume_templates import render_resume_html


class PDFRendererUnavailable(RuntimeError):
    pass


async def render_resume_pdf(content: dict, template_id: str) -> bytes:
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise PDFRendererUnavailable(
            "Install Playwright and its Chromium browser to export PDFs."
        ) from exc
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.set_content(render_resume_html(content, template_id), wait_until="load")
            return await page.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        finally:
            await browser.close()
