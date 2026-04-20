import asyncio
import pandas as pd
from playwright.async_api import async_playwright
import random
import re

TARGET_URLS = [
    "https://bringatrailer.com/porsche/911/",
    "https://bringatrailer.com/porsche/macan/",
    "https://bringatrailer.com/mercedes-benz/c-class/"
]

async def scroll_to_load(page, max_scrolls=5):
    for _ in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(random.uniform(1.5, 3.0))

async def click_show_more(page, max_clicks=10):
    """
    Looks for the 'Show More' button strictly within the completed auctions container.
    """
    # Scope the locator to ONLY the completed auctions section to fix the strict mode violation
    button_locator = page.locator("#auctions-completed-container button").filter(has_text=re.compile("show more", re.IGNORECASE))

    for i in range(max_clicks):
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)

            if await button_locator.is_visible():
                print(f"  -> Clicking 'Show More' (Attempt {i+1}/{max_clicks})...")
                await button_locator.click()
                await page.wait_for_timeout(random.uniform(2500, 4500))
            else:
                print("  -> 'Show More' button not found or no longer visible. Reached the end of available history.")
                break

        except Exception as e:
            print(f"  -> Interrupted while trying to load more: {e}")
            break

async def parse_auction_cards(page):
    results = []
    
    # Target specifically the completed auctions cards based on the new HTML structure
    card_selector = '#auctions-completed-container .listing-card' 
    
    cards = await page.locator(card_selector).all()
    
    for card in cards:
        try:
            # The title is now inside an h3 tag
            title_element = card.locator('h3')
            title = await title_element.inner_text() if await title_element.count() > 0 else None
            
            # The price and sale status are now bundled in the .item-results div
            results_element = card.locator('.item-results')
            results_text = await results_element.inner_text() if await results_element.count() > 0 else ""
            
            # The card itself is the <a> tag containing the URL
            url = await card.get_attribute('href')
            
            # BaT uses "Sold for..." vs "Bid to..." (Reserve Not Met)
            is_sold = "Sold" in results_text

            if title and results_text:
                # Clean up the results text (e.g., "Sold for USD $54,000 on 4/15/2026")
                # Split by " on " to drop the date, leaving just the price string
                raw_price_string = results_text.split(" on ")[0] 
                
                # Strip out all non-numeric characters to get a clean integer string
                price_numeric = re.sub(r'[^\d]', '', raw_price_string)

                results.append({
                    "raw_title": title.strip(),
                    "raw_price": price_numeric,
                    "is_sold": is_sold,
                    "auction_url": url
                })
        except Exception as e:
            continue
            
    return results

async def main():
    all_listing_data = []

    async with async_playwright() as p:
        # CHANGED: headless=False allows you to see if Cloudflare is blocking the script.
        # If a CAPTCHA appears, you can manually solve it in the pop-up browser window.
        browser = await p.chromium.launch(headless=False) 
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        
        for url in TARGET_URLS:
            print(f"\nNavigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded")
            
            print(f"Loading historical data via pagination...")
            # Call the new clicking function
            await click_show_more(page, max_clicks=10) 
            
            print("Parsing DOM for auction cards...")
            market_data = await parse_auction_cards(page)
            print(f"Extracted {len(market_data)} listings from this category.")
            
            all_listing_data.extend(market_data)
            await asyncio.sleep(random.uniform(2.0, 5.0))
            
        await browser.close()

    df = pd.DataFrame(all_listing_data)
    
    # CHANGED: Graceful exit if selectors fail or script is blocked
    if df.empty:
        print("\n[!] Extraction Failed: DataFrame is empty.")
        print("Check the browser window during execution to see if Cloudflare blocked the request, or update the CSS selectors in the script.")
        return
    
    # Clean and save data
    df = df.dropna(subset=['raw_price'])
    df = df[df['is_sold'] == True] 
    df.to_csv("bat_raw_market_data.csv", index=False)
    print("\nData ingestion complete. Saved to bat_raw_market_data.csv")
    print(df.head())

if __name__ == "__main__":
    asyncio.run(main())
