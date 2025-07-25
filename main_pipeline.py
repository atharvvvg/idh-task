#!/usr/bin/env python3
"""
Flight Fare Analysis Pipeline
Main orchestrator script for scraping and processing flight data from MakeMyTrip
"""

import os
import sys
from datetime import datetime

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

# Import pipeline components
from scraper import main as scrape_main
from processor import main as process_main

# Import configuration
from config import get_pipeline_config

def print_pipeline_info():
    """Print pipeline configuration and summary"""
    config = get_pipeline_config()
    print("=" * 70)
    print("    FLIGHT FARE ANALYSIS PIPELINE")
    print("=" * 70)
    print(f"Route: {config['source_city']} → {config['destination_city']}")
    print(f"Airports: {config['source_airport']} → {config['destination_airport']}")
    print(f"Days to scrape: {config['days_to_scrape']}")
    print(f"Headless mode: {config['headless']}")
    print(f"Delay range: {config['delay_min']}-{config['delay_max']} seconds")
    print(f"Data directory: {config['output_dir']}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

def run_scraping_phase():
    """Execute the data scraping phase"""
    print("\n🔍 PHASE 1: DATA SCRAPING")
    print("-" * 40)
    print("Starting flight data scraping from MakeMyTrip...")
    
    config = get_pipeline_config()
    if not config['headless']:
        print("Note: Manual CAPTCHA solving may be required (headless=False)")
    print()
    
    try:
        scrape_main(config)
        print("\n✅ Scraping phase completed successfully!")
        return True
    except Exception as e:
        print(f"\n❌ Scraping phase failed: {e}")
        return False

def run_processing_phase():
    """Execute the data processing and aggregation phase"""
    print("\n🔧 PHASE 2: DATA PROCESSING")
    print("-" * 40)
    print("Processing raw data: cleaning, outlier removal, and aggregation...")
    
    try:
        process_main()
        print("\n✅ Processing phase completed successfully!")
        print("\nDashboard-ready files created:")
        processed_dir = os.path.join(os.path.dirname(__file__), 'data/processed')
        print(f"  📊 {os.path.join(processed_dir, 'all_flights_cleaned.parquet')}")
        print(f"  📈 {os.path.join(processed_dir, 'monthly_summary_by_airline.csv')}")
        print(f"  📈 {os.path.join(processed_dir, 'monthly_summary_by_segment.csv')}")
        return True
    except Exception as e:
        print(f"\n❌ Processing phase failed: {e}")
        return False

def main():
    """Main pipeline orchestrator"""
    print_pipeline_info()
    
    # Phase 1: Scraping
    scraping_success = run_scraping_phase()
    
    if not scraping_success:
        print("\n⚠️  Pipeline stopped due to scraping failure.")
        print("You can manually run processing later with: python scripts/processor.py")
        return
    
    # Phase 2: Processing  
    processing_success = run_processing_phase()
    
    if processing_success:
        print("\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Review the processed data files in data/processed/")
        print("2. Use the clean data for dashboard creation or further analysis")
        print("3. Consider running the pipeline again for updated data")
        print("\nTo change routes or settings, edit config.py")
    else:
        print("\n⚠️  Scraping completed but processing failed.")
        print("You can manually run processing with: python scripts/processor.py")

if __name__ == "__main__":
    main() 