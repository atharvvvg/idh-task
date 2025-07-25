# Flight Data Fetcher - Setup and Usage

## Quick Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the API key:**

   - Open `config.yaml`
   - Replace `YOUR_RAPIDAPI_KEY_HERE` with your actual RapidAPI key
   - Adjust other parameters as needed

3. **Run the script:**
   ```bash
   python flight_fetcher.py
   ```

## Configuration Options

### API Settings

- `api.key`: Your RapidAPI key for Flight Fare Search
- `api.delay_seconds`: Delay between API calls (default: 2 seconds)

### Route Settings

- `route.from`: Source airport code (default: "BOM" for Mumbai)
- `route.to`: Destination airport code (default: "DEL" for Delhi)

### Search Parameters

- `search_params.num_days`: Number of days to fetch data for (default: 7)
- `search_params.currency`: Currency for prices (default: "INR")
- `search_params.type`: Cabin class (default: "economy")

### Output Settings

- `output.directory`: Output folder name (default: "output")
- `output.format`: File format - "xlsx" or "csv" (default: "xlsx")

## Output Structure

The script creates separate files for each date:

- `output/flights_DD_MM_YYYY.xlsx` (or .csv)

Each file contains columns:

- Flight Number
- Airline Name
- Source City
- Destination City
- Source Airport Code
- Destination Airport Code
- Date
- Departure Time
- Arrival Time
- Base Fare
- Layover Type (filtered to "Non-stop" only)

## Features

- **Modular Design**: Clean separation of concerns with configuration
- **Error Handling**: Graceful handling of API failures
- **Rate Limiting**: Built-in delays to respect API limits
- **Flexible Output**: Support for both Excel and CSV formats
- **Non-stop Filter**: Automatically filters for direct flights only
- **Date Management**: Automatically calculates dates starting 1 week from today

## Customization

You can easily modify the script for different routes or date ranges by updating the `config.yaml` file. No code changes required for basic customizations.
