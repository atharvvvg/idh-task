# Flight Fare Analysis Pipeline

Automated pipeline for scraping and analyzing flight fare data from MakeMyTrip. Collects 30 days of flight data for Mumbai → Delhi route (configurable) and generates dashboard-ready insights.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the Complete Pipeline
```bash
python main_pipeline.py
```

This will:
- Scrape flight data for the next 30 days
- Clean and process the data 
- Generate dashboard-ready summaries

## 📁 Output Files

After completion, you'll find:

```
data/
├── raw/                    # Raw scraped data (one file per day)
│   ├── 2025-01-15.parquet
│   └── ...
└── processed/              # Dashboard-ready data
    ├── all_flights_cleaned.parquet         # Complete cleaned dataset
    ├── monthly_summary_by_airline.csv      # Average fares by airline
    └── monthly_summary_by_segment.csv      # Average fares by time of day
```

## ⚙️ Configuration

### Change Routes
Edit `config.py` to modify the route:

```python
# Available routes
ACTIVE_ROUTE = MUMBAI_DELHI      # Default
# ACTIVE_ROUTE = DELHI_MUMBAI
# ACTIVE_ROUTE = MUMBAI_BANGALORE
# ACTIVE_ROUTE = DELHI_BANGALORE
```

### Change Scraping Settings
```python
# Available configurations
ACTIVE_SCRAPING = STANDARD_CONFIG   # 30 days, manual CAPTCHA
# ACTIVE_SCRAPING = QUICK_TEST_CONFIG # 3 days for testing
# ACTIVE_SCRAPING = AUTOMATED_CONFIG  # Fully automated (may fail on CAPTCHAs)
```

## 🔧 Manual Usage

### Run Only Scraping
```bash
python scripts/scraper.py
```

### Run Only Processing
```bash
python scripts/processor.py
```

### Check Current Config
```bash
python config.py
```

## 📊 Data Schema

### Raw Data Fields
- `Flight_Number`: Flight identifier (e.g., "6E-123")
- `Source_City`, `Destination_City`: City names
- `Source_Airport`, `Destination_Airport`: Airport codes (BOM, DEL, etc.)
- `Date`: Departure date (YYYY-MM-DD)
- `Departure_Time`, `Arrival_Time`: Time strings (HH:MM format)
- `Total_Fare`: Total price in INR
- `Layover`: "non-stop" or connection info
- `Airline_Name`: Carrier name

### Processed Data Additions
- `Departure_Segment`: Morning (<11AM), Afternoon (11AM-5PM), Evening (>5PM)
- `DayOfWeek`: Monday, Tuesday, etc.
- `IsWeekend`: Boolean flag

## 🛠️ Technical Details

### Anti-Bot Measures
- Random delays between requests (10-20 seconds)
- Non-headless mode for manual CAPTCHA solving
- Respectful throttling to avoid rate limits

### Data Quality
- IQR-based outlier removal per airline
- Missing data handling
- Duplicate detection and removal

## 🚨 Important Notes

1. **Manual Intervention**: Set `headless=False` in config for CAPTCHA solving
2. **Runtime**: Full 30-day scrape takes 10-20 minutes depending on delays
3. **Resumability**: Script skips already-scraped dates automatically
4. **Rate Limiting**: Increase delays if you encounter blocking

## 🎯 Next Steps

After getting the data:
1. Import processed data into your visualization tool
2. Create dashboards using the CSV summaries
3. Analyze price trends and patterns
4. Set up automated scheduling if needed

## 📝 Troubleshooting

**"Invalid date" errors**: Ensure your system date/time is correct
**CAPTCHA blocks**: Run with `headless=False` and solve manually
**No data found**: Check if the route/date combination has flights
**Selector errors**: MakeMyTrip may have changed their UI (update selectors)

---

Built for the aviation pricing case study. Easily extensible for other routes and date ranges. 