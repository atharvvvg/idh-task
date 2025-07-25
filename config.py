"""
Configuration Helper for Flight Fare Analysis Pipeline
Modify these settings to change routes, dates, or scraping behavior
"""

from datetime import datetime, timedelta

# ========== ROUTE CONFIGURATIONS ==========

# Primary route (Mumbai to Delhi)
MUMBAI_DELHI = {
    'source_city': 'Mumbai',
    'destination_city': 'Delhi',
    'source_airport': 'BOM',
    'destination_airport': 'DEL',
}

# Alternative popular routes (uncomment to use)
DELHI_MUMBAI = {
    'source_city': 'Delhi', 
    'destination_city': 'Mumbai',
    'source_airport': 'DEL',
    'destination_airport': 'BOM',
}

MUMBAI_BANGALORE = {
    'source_city': 'Mumbai',
    'destination_city': 'Bangalore', 
    'source_airport': 'BOM',
    'destination_airport': 'BLR',
}

DELHI_BANGALORE = {
    'source_city': 'Delhi',
    'destination_city': 'Bangalore',
    'source_airport': 'DEL', 
    'destination_airport': 'BLR',
}

# ========== SCRAPING CONFIGURATIONS ==========

# Standard configuration for 30-day analysis
STANDARD_CONFIG = {
    'days_to_scrape': 30,
    'headless': False,      # Set to True for fully automated runs
    'delay_min': 10,        # Minimum delay between requests (seconds)
    'delay_max': 20,        # Maximum delay between requests (seconds)
}

# Quick test configuration (only 3 days)
QUICK_TEST_CONFIG = {
    'days_to_scrape': 3,
    'headless': False,
    'delay_min': 5,
    'delay_max': 10,
}

# Automated configuration (for unattended runs)
AUTOMATED_CONFIG = {
    'days_to_scrape': 30,
    'headless': True,       # Fully automated - may fail on CAPTCHAs
    'delay_min': 15,        # Longer delays for better anti-bot avoidance
    'delay_max': 30,
}

# ========== ACTIVE CONFIGURATION ==========
# Change these to modify the pipeline behavior

# Select your route
ACTIVE_ROUTE = MUMBAI_DELHI

# Select your scraping config  
ACTIVE_SCRAPING = STANDARD_CONFIG

# ========== HELPER FUNCTIONS ==========

def get_pipeline_config():
    """Get the complete pipeline configuration"""
    import os
    
    config = {}
    config.update(ACTIVE_ROUTE)
    config.update(ACTIVE_SCRAPING)
    
    # Add directory configuration
    config['output_dir'] = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data/raw'))
    
    return config

def print_config_summary():
    """Print current configuration summary"""
    config = get_pipeline_config()
    print("Current Pipeline Configuration:")
    print(f"  Route: {config['source_city']} → {config['destination_city']}")
    print(f"  Airports: {config['source_airport']} → {config['destination_airport']}")
    print(f"  Days to scrape: {config['days_to_scrape']}")
    print(f"  Headless mode: {config['headless']}")
    print(f"  Delay range: {config['delay_min']}-{config['delay_max']} seconds")

if __name__ == "__main__":
    print_config_summary() 