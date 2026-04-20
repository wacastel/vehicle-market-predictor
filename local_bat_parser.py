import csv
import re
from bs4 import BeautifulSoup

# Ensure this matches the exact filename you saved
HTML_FILE_PATH = "Mercedes-Benz C-Class For Sale - BaT Auctions.html"
OUTPUT_CSV = "bat_c_class_historical_data.csv"

def extract_from_html(file_path):
    print(f"Loading and parsing {file_path}...")
    
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Target the specific container for completed auctions
    completed_container = soup.find(id="auctions-completed-container")
    
    if not completed_container:
        print("[!] Could not find the '#auctions-completed-container' in the HTML.")
        return []

    # Find all listing cards within that container
    cards = completed_container.find_all("a", class_="listing-card")
    print(f"Found {len(cards)} auction cards in the DOM. Extracting data...")

    results = []

    for card in cards:
        try:
            # Extract URL
            url = card.get("href", "")
            
            # Extract Title
            title_element = card.find("h3")
            title = title_element.get_text(strip=True) if title_element else None
            
            # Extract Results Text (e.g., "Sold for USD $54,000 on 4/15/2026")
            results_element = card.find("div", class_="item-results")
            results_text = results_element.get_text(strip=True) if results_element else ""
            
            is_sold = "Sold" in results_text
            
            if title and results_text:
                # Clean up the price string
                raw_price_string = results_text.split(" on ")[0] 
                price_numeric = re.sub(r'[^\d]', '', raw_price_string)

                results.append({
                    "raw_title": title,
                    "raw_price": price_numeric,
                    "is_sold": is_sold,
                    "auction_url": url
                })
        except Exception as e:
            print(f"Skipped a card due to error: {e}")
            continue

    return results

def main():
    market_data = extract_from_html(HTML_FILE_PATH)
    
    if not market_data:
        print("No data extracted. Exiting.")
        return

    # Filter out "Reserve Not Met" listings
    sold_listings = [item for item in market_data if item['is_sold']]
    
    print(f"Filtering out 'Reserve Not Met'... {len(sold_listings)} successful sales remain.")

    # Save to CSV
    keys = sold_listings[0].keys()
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(sold_listings)
        
    print(f"\nSuccess! Data saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
