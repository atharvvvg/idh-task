import os
import sys
import time
import random
from datetime import datetime, timedelta
import pandas as pd
from playwright.sync_api import sync_playwright

# Configurable parameters
default_config = {
    'source_city': 'Mumbai',
    'destination_city': 'Delhi',
    'source_airport': 'BOM',
    'destination_airport': 'DEL',
    'days_to_scrape': 7, 
    'output_dir': os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw')),
    'headless': False,  # True for full automation, False for manual CAPTCHA
    'delay_min': 15,    
    'delay_max': 30,  
}

# Helper to get target dates
def get_target_dates(days):
    today = datetime.today()
    return [(today + timedelta(days=i+1)) for i in range(days)]

# Convert date to MakeMyTrip format (DD/MM/YYYY)
def format_date_for_mmt(date_obj):
    return date_obj.strftime('%d/%m/%Y')

# Main scraping logic
def scrape_flights_for_date(playwright, config, dep_date_obj):
    # Create browser with more realistic settings
    browser = playwright.chromium.launch(
        headless=config['headless'],
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
    )
    
    # Create context with realistic settings
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1366, 'height': 768},
        locale='en-US',
        timezone_id='Asia/Kolkata'
    )
    
    # Remove webdriver property
    context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
    """)
    
    page = context.new_page()
    
    # Format date properly for MakeMyTrip URL
    dep_date_mmt = format_date_for_mmt(dep_date_obj)
    dep_date_str = dep_date_obj.strftime('%Y-%m-%d')  # For filename
    
    # Construct MakeMyTrip URL with correct date format
    url = f"https://www.makemytrip.com/flight/search?itinerary={config['source_airport']}-{config['destination_airport']}-{dep_date_mmt}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
    
    print(f"  Accessing URL: {url}")
    
    try:
        # Navigate to page with longer timeout
        page.goto(url, wait_until='domcontentloaded', timeout=90000)
        time.sleep(random.uniform(5, 8))
        
        if page.locator('text=NETWORK PROBLEM').is_visible():
            print("  ⚠️ Network problem detected, trying refresh...")
            try:
                page.click('button:has-text("REFRESH")', timeout=5000)
                time.sleep(random.uniform(5, 8))
            except:
                page.reload(wait_until='domcontentloaded')
                time.sleep(random.uniform(5, 8))
        
        if page.locator('text=NETWORK PROBLEM').is_visible():
            print("  ❌ Still getting network problem, skipping this date")
            context.close()
            browser.close()
            return []

        print("  Handling popups...")
        try:
            # to close "GOT IT" popup
            popup_button = page.locator('button:has-text("GOT IT")')
            if popup_button.is_visible(timeout=5000):
                popup_button.click()
                print("  ✓ Closed Flight Comparison popup")
                time.sleep(2)
        except Exception:
            print("  No Flight Comparison popup found")
        try:
            close_modal = page.locator('button[data-cy="closeModal"]')
            if close_modal.is_visible(timeout=3000):
                close_modal.click()
                time.sleep(1)
        except Exception:
            pass

        print("  Waiting for flight results...")
        try:
            page.wait_for_selector('div.listingCard, div.timingOptionOuter', timeout=45000)
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            print(f"Timeout waiting for flight results: {e}")
            context.close()
            browser.close()
            return []

        flights = []
        
        cards = page.query_selector_all('div.listingCard')
        if not cards:
            cards = page.query_selector_all('div.timingOptionOuter')
        
        print(f"  Found {len(cards)} flight cards")
        
        if len(cards) == 0:
            print("No flight cards found with current selectors")
            print("Page title:", page.title())
            context.close()
            browser.close()
            return []
        
        for i, card in enumerate(cards):
            try:
                # Extract airline name
                airline = None
                try:
                    airline_elem = card.query_selector('p.airlineName, .airlineName')
                    if airline_elem:
                        airline = airline_elem.inner_text().strip()
                except:
                    pass
                
                # Extract flight number
                flight_number = None
                try:
                    flight_elem = card.query_selector('p.fliCode, .fliCode')
                    if flight_elem:
                        flight_number = flight_elem.inner_text().strip()
                except:
                    pass

                # Extract departure time
                dep_time = None
                try:
                    dep_elem = card.query_selector('.timeInfoLeft .flightTimeInfo span, .timeInfoLeft span')
                    if dep_elem:
                        dep_time = dep_elem.inner_text().strip()
                except:
                    pass

                # Extract arrival time
                arr_time = None
                try:
                    arr_elem = card.query_selector('.timeInfoRight .flightTimeInfo span, .timeInfoRight span')
                    if arr_elem:
                        arr_time = arr_elem.inner_text().strip()
                except:
                    pass

                # Extract layover info
                layover = "non-stop"
                try:
                    layover_elem = card.query_selector('p.flightsLayoverInfo, .flightsLayoverInfo')
                    if layover_elem:
                        layover = layover_elem.inner_text().strip()
                except:
                    pass

                # Extract fare
                total_fare = None
                fare_selectors = [
                    'span.fontSize18.blackFont',
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
                        'Flight_Number': flight_number or f"Unknown-{i+1}",
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
                    print(f"Extracted: {flight_number or 'N/A'} | {airline} | {dep_time}-{arr_time} | ₹{total_fare}")
                else:
                    print(f"Missing essential data for flight {i+1} (airline: {airline}, fare: {total_fare})")
                    
                    # Debug missing data
                    if not airline:
                        print(f"      Missing airline - tried selectors: p.airlineName, .airlineName")
                    if not total_fare:
                        print(f"      Missing fare - tried multiple fare selectors")
                    
            except Exception as e:
                print(f"Error extracting flight {i+1}: {e}")
                continue
                
    except Exception as e:
        print(f"Error loading page: {e}")
        context.close()
        browser.close()
        return []
        
    context.close()
    browser.close()
    return flights

def main(config=None):
    if config is None:
        config = default_config
    
    # Create output directory
    os.makedirs(config['output_dir'], exist_ok=True)
    
    # Get target dates
    dates = get_target_dates(config['days_to_scrape'])
    
    print(f"Starting scrape for {len(dates)} days from {config['source_city']} to {config['destination_city']}")
    print(f"Route: {config['source_airport']} → {config['destination_airport']}")
    print(f"Output directory: {config['output_dir']}")
    print(f"Delay range: {config['delay_min']}-{config['delay_max']} seconds")
    print("-" * 60)
    
    with sync_playwright() as playwright:
        for i, dep_date_obj in enumerate(dates, 1):
            dep_date_str = dep_date_obj.strftime('%Y-%m-%d')
            out_path = os.path.join(config['output_dir'], f"{dep_date_str}.parquet")
            
            if os.path.exists(out_path):
                print(f"[{i}/{len(dates)}] Skipping {dep_date_str}, already scraped.")
                continue
                
            print(f"[{i}/{len(dates)}] Scraping for {dep_date_str}...")
            
            try:
                flights = scrape_flights_for_date(playwright, config, dep_date_obj)
                if flights:
                    df = pd.DataFrame(flights)
                    df.to_parquet(out_path, index=False)
                    print(f"  ✅ Saved {len(df)} flights to {out_path}")
                else:
                    print(f"  ⚠ No flights found for {dep_date_str}")
            except Exception as e:
                print(f"  ✗ Error scraping {dep_date_str}: {e}")
                continue
            
            # Throttle to avoid anti-bot measures
            if i < len(dates): 
                wait_time = random.uniform(config['delay_min'], config['delay_max'])
                print(f"  Waiting {wait_time:.1f}s before next request...")
                time.sleep(wait_time)
    
    print("-" * 60)
    print("Scraping completed!")

if __name__ == "__main__":
    main() 