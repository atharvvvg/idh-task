import os
import sys
import time
import random
from datetime import datetime, timedelta
import pandas as pd
from playwright.sync_api import sync_playwright

# Ultra-conservative configuration for avoiding bans
stealth_config = {
    'source_city': 'Mumbai',
    'destination_city': 'Delhi',
    'source_airport': 'BOM',
    'destination_airport': 'DEL',
    'days_to_scrape': 7,  # Very limited for testing
    'output_dir': os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw')),
    'headless': False,
    'delay_min': 45,    # Very long delays
    'delay_max': 90,    # 45-90 seconds between requests
}

def get_target_dates(days):
    today = datetime.today()
    return [(today + timedelta(days=i+1)) for i in range(days)]

def format_date_for_mmt(date_obj):
    return date_obj.strftime('%d/%m/%Y')

def scrape_flights_for_date_stealth(playwright, config, dep_date_obj):
    """Ultra-stealthy version of the scraper with correct selectors"""
    
    # Launch browser with maximum stealth
    browser = playwright.chromium.launch(
        headless=config['headless'],
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-images',  # Faster loading
        ]
    )
    
    # Stealth context
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},  # Common resolution
        locale='en-IN',  # Indian locale
        timezone_id='Asia/Kolkata',
        extra_http_headers={
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    )
    
    # Advanced anti-detection
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        window.chrome = {
            runtime: {},
        };
    """)
    
    page = context.new_page()
    
    dep_date_mmt = format_date_for_mmt(dep_date_obj)
    dep_date_str = dep_date_obj.strftime('%Y-%m-%d')
    
    url = f"https://www.makemytrip.com/flight/search?itinerary={config['source_airport']}-{config['destination_airport']}-{dep_date_mmt}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
    
    print(f"  🕵️ Stealth access: {url}")
    
    try:
        # Very slow navigation
        page.goto(url, wait_until='domcontentloaded', timeout=120000)
        
        # Random human-like delay
        human_delay = random.uniform(8, 15)
        print(f"  😴 Human-like delay: {human_delay:.1f}s")
        time.sleep(human_delay)
        
        # Check page title to detect blocks
        title = page.title()
        print(f"  📄 Page title: {title}")
        
        if "blocked" in title.lower() or "captcha" in title.lower() or len(title) < 10:
            print("  🚫 Detected blocking/CAPTCHA page")
            context.close()
            browser.close()
            return []
        
        # Check for network problem
        if page.locator('text=NETWORK PROBLEM').is_visible():
            print("  🚫 Network problem detected - you're still banned")
            context.close()
            browser.close()
            return []
        
        # Very gentle popup handling
        time.sleep(random.uniform(3, 6))
        
        try:
            popup_button = page.locator('button:has-text("GOT IT")')
            if popup_button.is_visible(timeout=10000):
                # Human-like mouse movement before click
                time.sleep(random.uniform(1, 3))
                popup_button.click()
                print("  ✅ Closed popup")
                time.sleep(random.uniform(2, 4))
        except Exception:
            print("  ℹ️ No popup found")

        # Wait very patiently for results
        print("  ⏳ Waiting patiently for flight results...")
        try:
            page.wait_for_selector('div.listingCard, div.timingOptionOuter', timeout=60000)
            time.sleep(random.uniform(5, 8))
        except Exception as e:
            print(f"  ❌ Still no flight results: {e}")
            print(f"  📝 Page content preview: {page.content()[:200]}...")
            context.close()
            browser.close()
            return []

        # Extract data very carefully using CORRECT selectors
        flights = []
        cards = page.query_selector_all('div.listingCard')
        if not cards:
            cards = page.query_selector_all('div.timingOptionOuter')
        
        print(f"  🎯 Found {len(cards)} flight cards")
        
        # Only extract if we actually found cards
        if len(cards) > 0:
            for i, card in enumerate(cards[:10]):  # Limit to first 10 for testing
                try:
                    # Extract airline name - based on correct HTML: p.airlineName
                    airline = None
                    try:
                        airline_elem = card.query_selector('p.airlineName, .airlineName')
                        if airline_elem:
                            airline = airline_elem.inner_text().strip()
                    except:
                        pass
                    
                    # Extract flight number - based on correct HTML: p.fliCode  
                    flight_number = None
                    try:
                        flight_elem = card.query_selector('p.fliCode, .fliCode')
                        if flight_elem:
                            flight_number = flight_elem.inner_text().strip()
                    except:
                        pass

                    # Extract departure time - based on correct HTML: .timeInfoLeft .flightTimeInfo span
                    dep_time = None
                    try:
                        dep_elem = card.query_selector('.timeInfoLeft .flightTimeInfo span, .timeInfoLeft span')
                        if dep_elem:
                            dep_time = dep_elem.inner_text().strip()
                    except:
                        pass

                    # Extract arrival time - based on correct HTML: .timeInfoRight .flightTimeInfo span
                    arr_time = None
                    try:
                        arr_elem = card.query_selector('.timeInfoRight .flightTimeInfo span, .timeInfoRight span')
                        if arr_elem:
                            arr_time = arr_elem.inner_text().strip()
                    except:
                        pass

                    # Extract layover info - based on correct HTML: p.flightsLayoverInfo
                    layover = "non-stop"  # default
                    try:
                        layover_elem = card.query_selector('p.flightsLayoverInfo, .flightsLayoverInfo')
                        if layover_elem:
                            layover = layover_elem.inner_text().strip()
                    except:
                        pass

                    # Extract fare - using multiple selectors including the correct one
                    total_fare = None
                    fare_selectors = [
                        'span.fontSize18.blackFont',  # User provided selector
                        '.fontSize18.blackFont',
                        'div.blackText.fontSize18.blackFont.white-space-no-wrap',
                        '.price',
                        'span[data-cy="price"]',
                        '.fare-price',
                        '.total-fare'
                    ]
                    
                    for selector in fare_selectors:
                        try:
                            fare_elem = card.query_selector(selector)
                            if fare_elem:
                                fare_text = fare_elem.inner_text().strip()
                                # Extract numbers from fare text (remove ₹, commas, etc.)
                                total_fare = int(''.join(filter(str.isdigit, fare_text)))
                                break
                        except:
                            continue
                    
                    # Only add flight if we have essential data
                    if airline and total_fare:
                        flights.append({
                            'Flight_Number': flight_number or f"Flight-{i+1}",
                            'Source_City': config['source_city'],
                            'Destination_City': config['destination_city'],
                            'Source_Airport': config['source_airport'],
                            'Destination_Airport': config['destination_airport'],
                            'Date': dep_date_str,
                            'Departure_Time': dep_time or "Unknown",
                            'Arrival_Time': arr_time or "Unknown",
                            'Base_Fare': None,
                            'Tax': None,
                            'Total_Fare': total_fare,
                            'Layover': layover,
                            'Airline_Name': airline
                        })
                        print(f"    ✅ {flight_number or 'N/A'} | {airline} | {dep_time or 'N/A'}-{arr_time or 'N/A'} | ₹{total_fare}")
                        
                        # Small delay between extractions
                        time.sleep(random.uniform(0.5, 1.5))
                    else:
                        print(f"    ⚠️ Missing essential data for flight {i+1} (airline: {airline}, fare: {total_fare})")
                        
                        # Debug missing data
                        if not airline:
                            print(f"      Missing airline - tried: p.airlineName, .airlineName")
                        if not total_fare:
                            print(f"      Missing fare - tried multiple selectors")
                            
                except Exception as e:
                    print(f"    ⚠️ Could not extract flight {i+1}: {e}")
                    continue
        
    except Exception as e:
        print(f"  💥 Major error: {e}")
    
    context.close()
    browser.close()
    return flights

def main():
    config = stealth_config
    os.makedirs(config['output_dir'], exist_ok=True)
    
    dates = get_target_dates(config['days_to_scrape'])
    
    print("🕵️ STEALTH MODE SCRAPER - UPDATED SELECTORS")
    print(f"Testing with {len(dates)} days only")
    print(f"Delays: {config['delay_min']}-{config['delay_max']} seconds")
    print("-" * 50)
    
    with sync_playwright() as playwright:
        for i, dep_date_obj in enumerate(dates, 1):
            dep_date_str = dep_date_obj.strftime('%Y-%m-%d')
            out_path = os.path.join(config['output_dir'], f"stealth_{dep_date_str}.parquet")
            
            print(f"[{i}/{len(dates)}] Testing {dep_date_str}...")
            
            try:
                flights = scrape_flights_for_date_stealth(playwright, config, dep_date_obj)
                if flights:
                    df = pd.DataFrame(flights)
                    df.to_parquet(out_path, index=False)
                    print(f"  🎉 SUCCESS! Saved {len(df)} flights")
                else:
                    print(f"  😔 No flights extracted - still banned or no data")
            except Exception as e:
                print(f"  💥 Error: {e}")
            
            # Very long delay
            if i < len(dates):
                wait_time = random.uniform(config['delay_min'], config['delay_max'])
                print(f"  😴 Long wait: {wait_time:.1f}s...")
                time.sleep(wait_time)
    
    print("🏁 Stealth test completed!")

if __name__ == "__main__":
    main() 