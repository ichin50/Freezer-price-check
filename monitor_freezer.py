import cloudscraper
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# Configuration: Site URLs and CSS Selectors
SITES = {
    "Frigidaire": {
        "url": "https://www.frigidaire.com/en/p/kitchen/freezers/upright-freezers/FFUE1626AV",
        "selector": ".price-current",
    },
    "Home Depot": {
        "url": "https://www.homedepot.com/p/Frigidaire-16-cu-ft-Garage-Ready-Convertible-Upright-Freezer-FFUE1626AV/328409000",
        "selector": ".price-format__main-price", 
    },
    "Best Buy": {
        "url": "https://www.bestbuy.com/site/frigidaire-16-cu-ft-garage-ready-convertible-upright-freezer-stainless-steel-look/6571591.p?skuId=6571591",
        "selector": "[data-testid='customer-price'] span",
    },
    "Lowe's": {
        "url": "https://www.lowes.com/pd/Frigidaire-Convertible-16-cu-ft-Garage-Ready-Frost-free-Upright-Freezer-Fingerprint-Resistant-Stainless-Steel-Look/5015183371",
        "selector": ".ad-prc-v2",
    },
    "Costco": {
        "url": "https://www.costco.com/frigidaire-16-cu.-ft.-garage-ready-upright-freezer.product.4000447650.html",
        "selector": ".price",
    }
}

def clean_price(price_str):
    """Removes currency symbols and formatting to return a float."""
    if not price_str:
        return None
    # Keep digits and decimal points
    cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
    try:
        return float(cleaned)
    except ValueError:
        return None

def fetch_prices():
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    
    current_results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "retailers": {}
    }

    for name, info in SITES.items():
        try:
            print(f"Checking {name}...")
            response = scraper.get(info["url"], timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                element = soup.select_one(info["selector"])
                
                if element:
                    price = clean_price(element.get_text())
                    current_results["retailers"][name] = price
                else:
                    # Costco often hides price behind login
                    if name == "Costco" and "sign in" in response.text.lower():
                        current_results["retailers"][name] = "Member Only"
                    else:
                        current_results["retailers"][name] = "Out of Stock/Hidden"
            else:
                current_results["retailers"][name] = f"Error {response.status_code}"
                
        except Exception as e:
            print(f"Failed to scrape {name}: {e}")
            current_results["retailers"][name] = "Scrape Failed"

    return current_results

def update_data_file(new_data):
    filename = 'freezer_prices.json'
    
    # Read existing data
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []
    else:
        history = []

    # Append new results and save
    history.append(new_data)
    
    # Keep only the last 30 entries to prevent the file from getting too big
    history = history[-30:]

    with open(filename, 'w') as f:
        json.dump(history, f, indent=4)

if __name__ == "__main__":
    latest_prices = fetch_prices()
    update_data_file(latest_prices)
    print("Update Complete.")
