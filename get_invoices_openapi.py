import asyncio
import os
import json
import time
from pathlib import Path
from playwright.async_api import async_playwright

INVOICES_DIR = Path("invoices/openai")
PORTAL_URL = "https://chat.openai.com/backend-api/payments/customer_portal"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/113.0.0.0 Safari/537.36"
)

async def verify_token(page, token: str) -> bool:
    print("🔄 Verifiëren access token...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://chat.openai.com/",
        "Content-Type": "application/json"
    }
    response = await page.request.get(PORTAL_URL, headers=headers)
    if response.ok:
        print("✅ Access token is geldig.")
        return True
    else:
        print(f"❌ Token ongeldig (status {response.status}).")
        return False

async def get_invoice_portal_url(page, token: str) -> str:
    print("🔄 Factuurportaal ophalen...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Referer": "https://chat.openai.com/",
        "Content-Type": "application/json"
    }
    response = await page.request.get(PORTAL_URL, headers=headers)
    
    if not response.ok:
        raise Exception(f"❌ API request failed with status {response.status}")
    
    data = await response.json()
    url = data.get("url")
    if not url:
        raise Exception("❌ Geen URL in API-respons.")
    print("✅ Factuurportaal URL:", url)
    return url

async def get_all_invoice_urls(page, portal_url):
    print("🔄 Laden van alle factuurlinks...")
    await page.goto(portal_url, wait_until='domcontentloaded', timeout=60000)
    await page.wait_for_selector('a[data-testid="hip-link"]', timeout=15000)
    links = await page.eval_on_selector_all('a[data-testid="hip-link"]', 'els => els.map(el => el.href)')
    print(f"✅ {len(links)} factuurlinks gevonden.")
    return links

async def download_invoice(page, invoice_url, download_dir: Path):
    print("⬇️ Downloaden factuur...")
    download_dir.mkdir(parents=True, exist_ok=True)

    await page.goto(invoice_url, wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_selector('button.Button--primary', timeout=15000)

    async with page.expect_download() as download_info:
        await page.click('button.Button--primary')

    download = await download_info.value
    filename = download.suggested_filename
    save_path = download_dir / filename

    await download.save_as(str(save_path))
    print(f"✅ Factuur opgeslagen als: {save_path}")
    return save_path


async def wait_for_file_completion(file_path: Path, timeout: int = 30):
    print("⏳ Download afronden...")
    start = time.time()
    last_size = -1
    while time.time() - start < timeout:
        if file_path.exists():
            size = file_path.stat().st_size
            if size > 0 and size == last_size:
                print("✅ Bestand volledig.")
                return True
            last_size = size
        time.sleep(1)
    raise TimeoutError("❌ Download time-out of incompleet.")

async def main():
    token = os.getenv("CHAT_GPT_ACCESS_TOKEN")
    if not token:
        print("❌ Geen CHAT_GPT_ACCESS_TOKEN gevonden in environment.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            accept_downloads=True,
            user_agent=USER_AGENT
        )
        page = await context.new_page()

        if not await verify_token(page, token):
            print("❌ Ongeldige token. Script afgebroken.")
            return

        invoice_portal_url = await get_invoice_portal_url(page, token)
        invoice_urls = await get_all_invoice_urls(page, invoice_portal_url)
        for i, invoice_url in enumerate(invoice_urls, start=1):
            print(f"\n📄 Downloaden factuur {i} van {len(invoice_urls)}...")

            # Eerst ophalen hoe de bestandsnaam eruit zou zien
            preview_page = await context.new_page()
            await preview_page.goto(invoice_url, wait_until="domcontentloaded", timeout=60000)
            await preview_page.wait_for_selector('button.Button--primary', timeout=15000)

            async with preview_page.expect_download() as info:
                await preview_page.click('button.Button--primary')

            download = await info.value
            filename = download.suggested_filename
            save_path = INVOICES_DIR / filename

            # Skip als hij al bestaat
            if save_path.exists():
                print(f"⏩ Factuur bestaat al: {save_path.name}")
                continue

            # Download opnieuw met echte pagina
            await download.save_as(str(save_path))
            print(f"✅ Factuur opgeslagen als: {save_path}")
            await wait_for_file_completion(save_path)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
