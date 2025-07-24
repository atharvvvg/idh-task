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
    'days_to_scrape': 30,
    'output_dir': os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw')),
    'headless': False,  # Set to True for full automation, False for manual CAPTCHA
}

# Helper to get target dates
def get_target_dates(days):
    today = datetime.today()
    return [(today + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(days)]

# Main scraping logic
def scrape_flights_for_date(playwright, config, dep_date):
    browser = playwright.chromium.launch(headless=config['headless'])
    context = browser.new_context()
    page = context.new_page()
    
    # Construct MakeMyTrip URL for the given date and route
    url = f"https://www.makemytrip.com/flight/search?itinerary={config['source_airport']}-{config['destination_airport']}-{dep_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E&lang=eng"
    page.goto(url)
    time.sleep(random.uniform(5, 8))  # Wait for page to load

    # Handle 'Flight Comparison' popup (GOT IT button)
    try:
        page.click('button:has-text("GOT IT")', timeout=3000)
    except Exception:
        pass

    # Handle other popups (if any)
    try:
        page.click('button[data-cy="closeModal"]', timeout=3000)
    except Exception:
        pass
    try:
        page.click('li[data-cy="account"]', timeout=3000)
    except Exception:
        pass

    # Wait for flight cards to load
    page.wait_for_selector('div.fli-list', timeout=20000)
    time.sleep(random.uniform(2, 4))

    # Extract flight data
    flights = []
    cards = page.query_selector_all('div.fli-list')
    for card in cards:
        try:
            airline = card.query_selector('span.airlineInfo-sctn .airlineName').inner_text().strip()
            flight_number = card.query_selector('span.flightNo').inner_text().strip()
            dep_time = card.query_selector('div.depart-time').inner_text().strip()
            arr_time = card.query_selector('div.reach-time').inner_text().strip()
            source = config['source_city']
            destination = config['destination_city']
            layover = card.query_selector('p.flt-stp').inner_text().strip()
            fare_text = card.query_selector('div.blackText.fontSize18.blackFont.white-space-no-wrap').inner_text().strip()
            total_fare = int(''.join(filter(str.isdigit, fare_text)))
            # Tax/Base fare not always available, set as None
            base_fare = None
            tax = None
            flights.append({
                'Flight_Number': flight_number,
                'Source_City': source,
                'Destination_City': destination,
                'Source_Airport': config['source_airport'],
                'Destination_Airport': config['destination_airport'],
                'Date': dep_date,
                'Departure_Time': dep_time,
                'Arrival_Time': arr_time,
                'Base_Fare': base_fare,
                'Tax': tax,
                'Total_Fare': total_fare,
                'Layover': layover,
                'Airline_Name': airline
            })
        except Exception as e:
            continue
    context.close()
    browser.close()
    return flights

def main(config=default_config):
    os.makedirs(config['output_dir'], exist_ok=True)
    dates = get_target_dates(config['days_to_scrape'])
    with sync_playwright() as playwright:
        for dep_date in dates:
            out_path = os.path.join(config['output_dir'], f"{dep_date}.parquet")
            if os.path.exists(out_path):
                print(f"Skipping {dep_date}, already scraped.")
                continue
            print(f"Scraping for {dep_date}...")
            flights = scrape_flights_for_date(playwright, config, dep_date)
            if flights:
                df = pd.DataFrame(flights)
                df.to_parquet(out_path, index=False)
                print(f"Saved {len(df)} flights to {out_path}")
            else:
                print(f"No flights found for {dep_date}")
            # Throttle to avoid anti-bot
            time.sleep(random.uniform(10, 20))

if __name__ == "__main__":
    main() 