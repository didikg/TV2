import re
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

# Define group-title overrides
group_overrides = {
    "A&E SD": "Entertainment",
    "A&E HD": "Entertainment",
    "ACC Network SD": "Sports",
    "ACC Network HD": "Sports",
    "AMC SD": "Movies",
    "AMC HD": "Movies",
    "American Heroes Channel SD": "Entertainment",
    "American Heroes Channel HD": "Entertainment",
    "Animal Planet SD": "Documentary",
    "Animal Planet HD": "Documentary",
    "BBC America SD": "Entertainment",
	"BBC America HD": "Entertainment",
 	"BBC World News HD SD": "News",
	"BBC World News HD HD": "News",
 	"BET SD": "Entertainment",
  	"BET HD": "Entertainment",
   	"BET Her SD": "Entertainment",
	"BET Her HD": "Entertainment",
 	"Big Ten Network SD": "Sports",
    "Big Ten Network HD": "Sports",
	"Bloomberg TV SD": "News",
    "Bloomberg TV HD": "News",
	"Boomerang SD": "Kids",
	"Boomerang HD": "Kids",
    "Bravo SD": "Entertainment",
    "Bravo HD": "Entertainment",
  	"Cartoon Network SD": "Kids",
	"Cartoon Network HD": "Kids",
	"CBS Sports Network SD": "Sports",
    "CBS Sports Network HD": "Sports",
    "Cinemax SD": "Movies",
	"Cinemax HD": "Movies",
    "CNBC SD": "News",
    "CNBC HD": "News",
    "CMT SD": "Entertainment",
    "CMT HD": "Entertainment",
    "CNN SD": "News",
    "CNN HD": "News",
    "Comedy Central SD": "Entertainment",
    "Comedy Central HD": "Entertainment",
    "Cooking Channel SD": "Entertainment",
    "Cooking Channel HD": "Entertainment",
    "Crime & Investigation HD SD": "Documentary",
    "Crime & Investigation HD HD": "Documentary",
    "CSPAN SD": "News",
    "CSPAN HD": "News",
    "CSPAN 2 SD": "News",
    "CSPAN 2 HD": "News",
    "Destination America SD": "Documentary",
    "Destination America HD": "Documentary",
  	"Discovery SD": "Documentary",
  	"Discovery HD": "Documentary",
    "Discovery Family Channel SD": "Kids",
    "Discovery Family Channel HD": "Kids",
    "Discovery Life SD": "Documentary",
    "Discovery Life HD": "Documentary",
   	"Disney Channel (East) SD": "Kids",
   	"Disney Channel (East) HD": "Kids",
    "Disney Junior SD": "Kids",
    "Disney Junior HD": "Kids",
    "Disney XD SD": "Kids",
    "Disney XD HD": "Kids",
    "E! SD": "Entertainment",
    "E! HD": "Entertainment",
    "ESPN SD": "Sports",
    "ESPN HD": "Sports",
   	"ESPN2 SD": "Sports",
   	"ESPN2 HD": "Sports",
    "ESPNews SD": "Sports",
    "ESPNews HD": "Sports",
    "ESPNU SD": "Sports",
    "ESPNU HD": "Sports",
    "Food Network SD": "Entertainment",
    "Food Network HD": "Entertainment",
    "Fox Business Network SD": "News",
    "Fox Business Network HD": "News",
    "FOX News Channel SD": "News",
    "FOX News Channel HD": "News",
    "FOX Sports 1 SD": "Sports",
    "FOX Sports 1 HD": "Sports",
    "FOX Sports 2 SD": "Sports",
    "FOX Sports 2 HD": "Sports",
    "Freeform SD": "Entertainment",
    "Freeform HD": "Entertainment",
    "Fuse HD SD": "Entertainment",
    "Fuse HD HD": "Entertainment",
    "FX SD": "Entertainment",
    "FX HD": "Entertainment",
    "FX Movie SD": "Movies",
    "FX Movie HD": "Movies",
    "FXX SD": "Movies",
    "FXX HD": "Movies",
    "FYI SD": "Entertainment",
    "FYI HD": "Entertainment",
    "Golf Channel SD": "Sports",
    "Golf Channel HD": "Sports",
    "Hallmark SD": "Movies",
    "Hallmark HD": "Movies",
    "Hallmark Drama HD SD": "Movies",
    "Hallmark Drama HD HD": "Movies",
    "Hallmark Movies & Mysteries HD SD": "Movies",
    "Hallmark Movies & Mysteries HD HD": "Movies",
    "HBO 2 East SD": "Movies",
    "HBO 2 East HD": "Movies",
    "HBO Comedy HD SD": "Movies",
    "HBO Comedy HD HD": "Movies",
    "HBO East SD": "Movies",
    "HBO East HD": "Movies",
    "HBO Family East SD": "Movies",
    "HBO Family East HD": "Movies",
    "HBO Signature SD": "Movies",
    "HBO Signature HD": "Movies",
    "HBO Zone HD SD": "Movies",
    "HBO Zone HD HD": "Movies",
    "HGTV SD": "Entertainment",
    "HGTV HD": "Entertainment",
    "History SD": "Documentary",
    "History HD": "Documentary",
    "HLN SD": "News",
    "HLN HD": "News",
    "IFC SD": "Movies",
    "IFC HD": "Movies",
    "Investigation Discovery SD": "Documentary",
    "Investigation Discovery HD": "Documentary",
    "ION Television East HD SD": "Entertainment",
    "ION Television East HD HD": "Entertainment",
    "Lifetime SD": "Movies",
    "Lifetime HD": "Movies",
    "LMN": "Movies",
    "Logo SD": "Entertainment",
    "Logo HD": "Entertainment",
    "MeTV Toons SD": "Kids",
    "MeTV Toons HD": "Kids",
    "MLB Network SD": "Sports",
    "MLB Network HD": "Sports",
    "MoreMAX SD": "Movies",
    "MoreMAX HD": "Movies",
    "MotorTrend HD SD": "Sports",
    "MotorTrend HD HD": "Sports",
    "MovieMAX SD": "Movies",
    "MovieMAX HD": "Movies",
    "MSNBC SD": "News",
    "MSNBC HD": "News",
    "MTV SD": "Music",
    "MTV HD": "Music",
    "Nat Geo WILD SD": "Documentary",
    "Nat Geo WILD HD": "Documentary",
    "National Geographic SD": "Documentary",
    "National Geographic HD": "Documentary",
    "NBA TV SD": "Sports",
    "NBA TV HD": "Sports",
    "Newsmax TV SD": "News",
    "Newsmax TV HD": "News",
    "NFL Network SD": "Sports",
    "NFL Network HD": "Sports",
    "NFL Red Zone SD": "Sports",
    "NFL Red Zone HD": "Sports",
    "NHL Network SD": "Sports",
    "NHL Network HD": "Sports",
    "Nick Jr. SD": "Kids",
    "Nick Jr. HD": "Kids",
    "Nickelodeon East SD": "Kids",
    "Nickelodeon East HD": "Kids",
    "Nicktoons SD": "Kids",
    "Nicktoons HD": "Kids",
    "Outdoor Channel SD": "Documentary",
    "Outdoor Channel HD": "Documentary",
    "OWN SD": "Entertainment",
    "OWN HD": "Entertainment",
    "Oxygen True Crime SD": "Entertainment",
    "Oxygen True Crime HD": "Entertainment",
    "PBS 13 (WNET) New York SD": "Entertainment",
    "PBS 13 (WNET) New York HD": "Entertainment",
    "ReelzChannel SD": "Entertainment",
    "ReelzChannel HD": "Entertainment",
    "Science SD": "Documentary",
    "Science HD": "Documentary",
    "SEC Network SD": "Sports",
    "SEC Network HD": "Sports",
    "Showtime (E) SD": "Movies",
    "Showtime (E) HD": "Movies",
    "SHOWTIME 2 SD": "Movies",
    "SHOWTIME 2 HD": "Movies",
    "STARZ East SD": "Movies",
    "STARZ East HD": "Movies",
    "SundanceTV HD SD": "Movies",
    "SundanceTV HD HD": "Movies",
    "SYFY SD": "Entertainment",
    "SYFY HD": "Entertainment",
    "TBS SD": "Entertainment",
    "TBS HD": "Entertainment",
    "TCM SD": "Movies",
    "TCM HD": "Movies",
    "TeenNick SD": "Kids",
    "TeenNick HD": "Kids",
    "Telemundo East SD": "Spanish",
    "Telemundo East HD": "Spanish",
    "Tennis Channel SD": "Sports",
    "Tennis Channel HD": "Sports",
    "The CW (WPIX New York) SD": "News",
    "The CW (WPIX New York) HD": "News",
    "The Movie Channel East SD": "Entertainment",
    "The Movie Channel East HD": "Entertainment",
    "The Weather Channel SD": "News",
    "The Weather Channel HD": "News",
    "TLC SD": "Entertainment",
    "TLC HD": "Entertainment",
    "TNT SD": "Entertainment",
    "TNT HD": "Entertainment",
    "Travel Channel SD": "Documentary",
    "Travel Channel HD": "Documentary",
    "truTV SD": "Entertainment",
    "truTV HD": "Entertainment",
    "TV One HD SD": "Entertainment",
    "TV One HD HD": "Entertainment",
    "Universal Kids SD": "Kids",
    "Universal Kids HD": "Kids",
    "Univision East SD": "Spanish",
    "Univision East HD": "Spanish",
    "USA Network SD": "Entertainment",
    "USA Network HD": "Entertainment",
   	"VH1 SD": "Entertainment",
   	"VH1 HD": "Entertainment",
    "VICE SD": "Entertainment",
    "VICE HD": "Entertainment",
    "WABC (New York) ABC East SD": "News",
    "WABC (New York) ABC East HD": "News",
    "WCBS (New York) CBS East SD": "News",
    "WCBS (New York) CBS East HD": "News",
    "WE tv SD": "Entertainment",
    "WE tv HD": "Entertainment",
    "WNBC (New York) NBC East SD": "News",
    "WNBC (New York) NBC East HD": "News",
    "WNYW (New York) FOX East SD": "News",
    "WNYW (New York) FOX East HD": "News"
}

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
            group_title = group_overrides.get(tvg_name, "Others")


            if i > 0 and lines[i - 1].startswith("#EXTINF"):
                extinf = lines[i - 1]
                if "," in extinf:
                    parts = extinf.split(",")
                    parts[-1] = title
                    extinf = ",".join(parts)
                    # Inject group-title if not already present
                    if 'group-title=' not in extinf:
                        extinf = re.sub(r'(tvg-logo="[^"]+")', r'\1 group-title="{}"'.format(group_title), extinf)
                updated[-1] = extinf

            updated.append(tv_urls[tv_idx][0])
            tv_idx += 1
        else:
            updated.append(line)
        i += 1
    return updated

async def main():
    if not Path(M3U8_FILE).exists():
        print(f"❌ File not found: {M3U8_FILE}")
        return

    with open(M3U8_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    lines = clean_m3u_header(lines)

    print("🔧 Replacing /tv stream URLs...")
    tv_new_urls = await scrape_tv_urls()
    if tv_new_urls:
        lines = replace_tv_urls(lines, tv_new_urls)

    with open(M3U8_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ {M3U8_FILE} updated with TV streams only.")

if __name__ == "__main__":
    asyncio.run(main())
