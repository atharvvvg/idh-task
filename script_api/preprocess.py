import pandas as pd
import os
from glob import glob

# Input and output directories
INPUT_DIR = "output"
OUTPUT_DIR = "processed_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

all_files = glob(os.path.join(INPUT_DIR, "flights_*.xlsx"))
processed_rows = []

def classify_time_block(dep_hour):
    if dep_hour < 11:
        return "Morning"
    elif 11 <= dep_hour < 17:
        return "Afternoon"
    else:
        return "Evening"

for file in all_files:
    df = pd.read_excel(file)

    # Parse datetime columns (don't overwrite)
    df['Departure Date'] = pd.to_datetime(df['Departure Time']).dt.date
    df['Departure Full Time'] = pd.to_datetime(df['Departure Time']).dt.time
    df['Departure Hour'] = pd.to_datetime(df['Departure Time']).dt.hour
    df['Arrival Date'] = pd.to_datetime(df['Arrival Time']).dt.date
    df['Arrival Full Time'] = pd.to_datetime(df['Arrival Time']).dt.time
    df['Arrival Hour'] = pd.to_datetime(df['Arrival Time']).dt.hour

    # Tax and total fare (as new columns)
    df['Tax'] = df['Base Fare'] * 0.05
    df['Total Fare'] = df['Base Fare'] + df['Tax']

    # Time block classification
    df['Time Block'] = df['Departure Hour'].apply(classify_time_block)

    processed_rows.append(df)

# Merge all data into one DataFrame (read-only merge)
df_all = pd.concat(processed_rows, ignore_index=True)

# Save enriched flat file
df_all.to_csv(os.path.join(OUTPUT_DIR, "aggregated_flight_data.csv"), index=False)

# Grouped summary (for frontend dashboard)
summary = df_all.groupby(['Airline Name', 'Departure Date', 'Time Block']).agg({
    'Total Fare': ['mean', 'count']
}).reset_index()

summary.columns = ['Airline Name', 'Date', 'Time Block', 'Avg Price', 'Flight Count']
summary.to_csv(os.path.join(OUTPUT_DIR, "summary_by_airline_time.csv"), index=False)

print("✅ Processing complete. Files saved in /processed_data")
