import asyncio
import urllib.parse
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

M3U8_FILE = "livetv.m3u8"
BASE_URL = "https://thetvapp.to"
CHANNEL_LIST_URL = f"{BASE_URL}/tv"

def extract_real_m3u8(url: str):
    if "ping.gif" in url and "mu=" in url:
        parsed = urllib.parse.urlparse(url)
        qs = urllib.parse.parse_qs(parsed.query)
        mu = qs.get("mu", [None])[0]
        if mu:
            return urllib.parse.unquote(mu)
    if ".m3u8" in url:
        return url
    return None

async def scrape_tv_urls():
    urls = []
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔄 Loading /tv channel list...")
        await page.goto(CHANNEL_LIST_URL)
        links = await page.locator("ol.list-group a").all()
        hrefs_and_titles = [(await link.get_attribute("href"), await link.text_content())
                            for link in links if await link.get_attribute("href")]
        await page.close()

        for href, title_raw in hrefs_and_titles:
            full_url = BASE_URL + href
            title = " - ".join(line.strip() for line in title_raw.splitlines() if line.strip())
            print(f"🎯 Scraping TV page: {full_url}")

            for quality in ["SD", "HD"]:
                stream_url = None
                new_page = await context.new_page()

                async def handle_response(response):
                    nonlocal stream_url
                    real = extract_real_m3u8(response.url)
                    if real and not stream_url:
                        stream_url = real

                new_page.on("response", handle_response)
                await new_page.goto(full_url)

                try:
                    await new_page.get_by_text(f"Load {quality} Stream", exact=True).click(timeout=5000)
                except:
                    pass

                await asyncio.sleep(4)
                await new_page.close()

                if stream_url:
                    urls.append((stream_url, "TV", f"{title} {quality}"))
                    print(f"✅ {quality}: {stream_url}")
                else:
                    print(f"❌ {quality} not found")

        await browser.close()
    return urls

def clean_m3u_header(lines):
    lines = [line for line in lines if not line.strip().startswith("#EXTM3U")]
    timestamp = int(datetime.utcnow().timestamp())
    lines.insert(0, f'#EXTM3U url-tvg="https://tvpass.org/epg.xml" # Updated: {timestamp}')
    return lines

def replace_tv_urls(lines, tv_urls):
    updated = []
    tv_idx = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("http") and tv_idx < len(tv_urls):
            group, title = tv_urls[tv_idx][1], tv_urls[tv_idx][2]
            if i > 0 and lines[i - 1].startswith("#EXTINF"):
                extinf = lines[i - 1]
                if "," in extinf:
                    parts = extinf.split(",")
                    parts[-1] = title
                    extinf = ",".join(parts)
                updated[-1] = extinf
            updated.append(tv_urls[tv_idx][0])
            tv_idx += 1
        else:
            updated.append(line)
        i += 1
    return updated

import re  # Add this at the top if not already present

def remove_group_title(lines):
    cleaned = []
    for line in lines:
        if line.startswith("#EXTINF") and 'group-title=' in line:
            # Remove group-title="..." using regex
            line = re.sub(r'group-title="[^"]*"\s*', '', line)
        cleaned.append(line)
    return cleaned

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    lines = clean_m3u_header(lines)
    lines = remove_group_title(lines)  # 👈 Add this line
    
    print("🔧 Replacing /tv stream URLs...")
    tv_new_urls = await scrape_tv_urls()
    if tv_new_urls:
        lines = replace_tv_urls(lines, tv_new_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ {M3U8_FILE} updated with TV streams only.")
    
if __name__ == "__main__":
    asyncio.run(main())
