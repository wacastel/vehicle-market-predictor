import plistlib
import re
import csv
from bs4 import BeautifulSoup

# Ensure this matches your downloaded filename exactly
FILE_PATH = "Mercedes-Benz C-Class For Sale - BaT Auctions.webarchive"
OUTPUT_CSV = "bat_c_class_historical_data.csv"

def main():
    print(f"Cracking open {FILE_PATH}...")

    # 1. Load the binary plist (Safari WebArchive)
    try:
        with open(FILE_PATH, 'rb') as f:
            archive = plistlib.load(f)
    except Exception as e:
        print(f"[!] Error loading webarchive: {e}")
        return

    # 2. Extract the main HTML payload from the archive
    try:
        html_bytes = archive['WebMainResource']['WebResourceData']
        html_content = html_bytes.decode('utf-8', errors='ignore')
    except KeyError:
        print("[!] Could not locate WebMainResource in the archive.")
        return

    print("Live HTML payload extracted. Parsing DOM...")

    # 3. Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Target all listing cards. Broadening the search since serialized 
    # DOMs can have slightly altered hierarchies.
    cards = soup.find_all("a", class_="listing-card")
    print(f"Found {len(cards)} total auction cards in the saved state.")

    results = []

    for card in cards:
        try:
            url = card.get("href", "")

            # Extract Title
            title_element = card.find("h3")
            title = title_element.get_text(strip=True) if title_element else None

            # Extract Price and Sale Status
            results_element = card.find("div", class_="item-results")
            results_text = results_element.get_text(strip=True) if results_element else ""

            if title and "Sold" in results_text:
                # Clean up the price string
                raw_price_string = results_text.split(" on ")[0]
                price_numeric = re.sub(r'[^\d]', '', raw_price_string)

                if price_numeric and title:
                    results.append({
                        "raw_title": title,
                        "raw_price": price_numeric,
                        "is_sold": True,
                        "auction_url": url
                    })
        except Exception as e:
            continue

    # 4. Deduplicate (serialized DOMs occasionally clone nodes)
    unique_results = {item['auction_url']: item for item in results}.values()

    print(f"Extraction complete. {len(unique_results)} successful sales parsed.")

    # 5. Save to CSV
    if unique_results:
        keys = list(unique_results)[0].keys()
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(unique_results)
        print(f"\nSuccess! Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
