import json
import os
import random
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth  # Updated import for v2.0.0+

# Sites to monitor
SITES = {
    "Frigidaire": {
        "url": "https://www.frigidaire.com/en/p/kitchen/freezers/upright-freezers/FFUE1626AV?srsltid=AfmBOooh9IcFOQZENgvAOCh1606I5K2L5WpavtvGzowXjd9O2Na9rzuj",
        "selector": ".price-current",
    },
    "Home Depot": {
        "url": "https://www.homedepot.com/p/Frigidaire-16-cu-ft-Convertible-Frost-Free-Upright-Freezer-in-Fingerprint-Resistant-Stainless-Steel-Look-FFUE1626AV/339011917",
        "selector": ".price-format__main-price", 
    },
    "Best Buy": {
        "url": "https://www.bestbuy.com/product/frigidaire-16-cu-ft-garage-ready-convertible-upright-freezer-fingerprint-resistant-stainless-steel-look/J3GWPSKSGY",
        "selector": "[data-testid='customer-price'] span",
    },
    "Lowe's": {
        "url": "https://www.lowes.com/pd/Frigidaire-16-Cu-Ft-Garage-Ready-Upright-Freezer/5018048023",
        "selector": ".ad-prc-v2",
    }
}

def clean_price(price_str):
    if not price_str: return None
    # Extracts numbers and decimals only
    cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
    try:
        return float(cleaned)
    except:
        return None

def fetch_prices():
    current_results = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"), "retailers": {}}
    
    # NEW STEALTH PATTERN: Wraps the entire playwright session
    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        for name, info in SITES.items():
            print(f"Scraping {name}...")
            page = context.new_page()
            
            try:
                time.sleep(random.uniform(3, 6)) # Mimic human reading time
                page.goto(info["url"], wait_until="networkidle", timeout=60000)
                
                element = page.wait_for_selector(info["selector"], timeout=15000)
                if element:
                    raw_price = element.inner_text()
                    price = clean_price(raw_price)
                    current_results["retailers"][name] = price
                    print(f"Found {name}: ${price}")
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
    # Keep only the last 30 entries to save space
    with open(file, 'w') as f:
        json.dump(history[-30:], f, indent=4)

if __name__ == "__main__":
    data = fetch_prices()
    update_data(data)
    
    # EMAIL ALERT LOGIC
    # Triggers GitHub "Workflow Failed" email if price is below $729
    TARGET_PRICE = 729.0
    found_deal = False
    
    for retailer, price in data["retailers"].items():
        if isinstance(price, (int, float)) and price < TARGET_PRICE:
            print(f"🚨 DEAL ALERT: {retailer} has the freezer for ${price}!")
            found_deal = True
    
    if found_deal:
        print("Failing workflow to trigger GitHub Notification Email...")
        exit(1) 
    else:
        print("No price drops below $729 detected.")
