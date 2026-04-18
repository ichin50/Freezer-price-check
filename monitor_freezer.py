import json
import os
import random
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

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
    if not price_str: return None
    cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
    try:
        return float(cleaned)
    except:
        return None

def fetch_prices():
    current_results = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "retailers": {}}
    
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for name, info in SITES.items():
            print(f"Scraping {name}...")
            page = context.new_page()
            stealth_sync(page) # Apply stealth to hide Playwright
            
            try:
                # Random delay to mimic human behavior
                time.sleep(random.uniform(2, 5)) 
                page.goto(info["url"], wait_until="networkidle", timeout=60000)
                
                element = page.wait_for_selector(info["selector"], timeout=10000)
                if element:
                    raw_price = element.inner_text()
                    current_results["retailers"][name] = clean_price(raw_price)
                else:
                    current_results["retailers"][name] = "Not Found"
            except Exception as e:
                print(f"Failed {name}: {str(e)[:50]}")
                current_results["retailers"][name] = "Timeout/Block"
            
            page.close()
        
        browser.close()
    return current_results

def update_data(new_data):
    file = 'freezer_prices.json'
    history = json.load(open(file)) if os.path.exists(file) else []
    history.append(new_data)
    with open(file, 'w') as f:
        json.dump(history[-30:], f, indent=4)

if __name__ == "__main__":
    data = fetch_prices()
    update_data(data)
    print("Done!")
