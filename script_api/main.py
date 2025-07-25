import requests
import pandas as pd
import yaml
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import time


class FlightDataFetcher:
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize with configuration from YAML file"""
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.api_key = self.config['api']['key']
        self.api_host = self.config['api']['host']
        self.base_url = self.config['api']['base_url']
        
        # Create output directory
        os.makedirs(self.config['output']['directory'], exist_ok=True)
    
    def get_flight_data(self, from_code: str, to_code: str, date: str) -> List[Dict]:
        """Fetch flight data for a specific route and date"""
        url = self.base_url
        
        querystring = {
            "from": from_code,
            "to": to_code,
            "date": date,
            "adult": str(self.config['search_params']['adult']),
            "type": self.config['search_params']['type'],
            "currency": self.config['search_params']['currency']
        }
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": self.api_host
        }
        
        try:
            print(f"Making request to: {url}")
            print(f"Query params: {querystring}")
            
            response = requests.get(url, headers=headers, params=querystring)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            data = response.json()
            print(f"API Response keys: {data.keys()}")
            
            return data.get('results', [])
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {date}: {e}")
            print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
            return []
    
    def process_flight_data(self, raw_data: List[Dict], date: str) -> List[Dict]:
        """Process raw API data into structured format"""
        processed_flights = []
        
        for flight in raw_data:
            # Filter for non-stop flights only
            stops = flight.get('stops', '').lower()
            if stops not in ['direct', 'non stop', 'nonstop']:
                continue
                
            flight_info = {
                'Flight Number': flight.get('flight_code', ''),
                'Airline Name': flight.get('flight_name', ''),
                'Source City': flight.get('departureAirport', {}).get('city', ''),
                'Destination City': flight.get('arrivalAirport', {}).get('city', ''),
                'Source Airport Code': flight.get('departureAirport', {}).get('code', ''),
                'Destination Airport Code': flight.get('arrivalAirport', {}).get('code', ''),
                'Date': date,
                'Departure Time': flight.get('departureAirport', {}).get('time', ''),
                'Arrival Time': flight.get('arrivalAirport', {}).get('time', ''),
                'Base Fare': flight.get('totals', {}).get('base', flight.get('totals', {}).get('total', 0)),
                'Layover Type': 'Non-stop'
            }
            processed_flights.append(flight_info)
        
        return processed_flights
    
    def save_to_file(self, data: List[Dict], date: str):
        """Save data to Excel/CSV file"""
        if not data:
            print(f"No data to save for {date}")
            return
        
        df = pd.DataFrame(data)
        
        # Generate filename
        file_format = self.config['output']['format']
        filename = f"flights_{date.replace('-', '_')}.{file_format}"
        filepath = os.path.join(self.config['output']['directory'], filename)
        
        # Save based on format
        if file_format == 'xlsx':
            df.to_excel(filepath, index=False)
        else:  # csv
            df.to_csv(filepath, index=False)
        
        print(f"Saved {len(data)} flights to {filepath}")
    
    def fetch_multiple_days(self, start_date: str, num_days: int):
        """Fetch flight data for multiple consecutive days"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        
        for i in range(num_days):
            current_date = start_dt + timedelta(days=i)
            # date format YYYY-MM-DD for API
            date_str = current_date.strftime('%Y-%m-%d') 
            
            print(f"Fetching data for {date_str}...")
            
            raw_data = self.get_flight_data(
                self.config['route']['from'], 
                self.config['route']['to'], 
                date_str
            )
            
            processed_data = self.process_flight_data(raw_data, date_str)
            self.save_to_file(processed_data, date_str)
            
            # delay between requests to respect rate limits
            if i < num_days - 1:
                time.sleep(self.config['api']['delay_seconds'])


def main():
    fetcher = FlightDataFetcher()
    
    # Get start date (time delta can be set manually) in yyyy-mm-dd format
    start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # Fetch data for specified number of days
    num_days = fetcher.config['search_params']['num_days']
    
    print(f"Starting data collection from {start_date} for {num_days} days...")
    fetcher.fetch_multiple_days(start_date, num_days)
    print("Data collection completed!")


if __name__ == "__main__":
    main()