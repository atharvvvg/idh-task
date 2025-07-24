import os
import pandas as pd
import numpy as np
from glob import glob

def load_all_raw_data(raw_dir):
    files = glob(os.path.join(raw_dir, '*.parquet'))
    dfs = [pd.read_parquet(f) for f in files]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

def clean_data(df):
    # Convert Total_Fare to numeric (should already be int, but just in case)
    df['Total_Fare'] = pd.to_numeric(df['Total_Fare'], errors='coerce')
    # Parse Departure_Time to hour
    df['Dep_Hour'] = pd.to_datetime(df['Departure_Time'], format='%I:%M %p', errors='coerce').dt.hour
    # Bucket departure time
    def bucket_time(hour):
        if pd.isna(hour): return 'Unknown'
        if hour < 11: return 'Morning'
        elif hour < 17: return 'Afternoon'
        else: return 'Evening'
    df['Departure_Segment'] = df['Dep_Hour'].apply(bucket_time)
    # Day of week
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['DayOfWeek'] = df['Date'].dt.day_name()
    df['IsWeekend'] = df['DayOfWeek'].isin(['Saturday', 'Sunday'])
    return df

def remove_outliers_iqr(df):
    # Remove outliers per airline using IQR
    def iqr_filter(group):
        q1 = group['Total_Fare'].quantile(0.25)
        q3 = group['Total_Fare'].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return group[(group['Total_Fare'] >= lower) & (group['Total_Fare'] <= upper)]
    return df.groupby('Airline_Name', group_keys=False).apply(iqr_filter)

def aggregate(df):
    by_airline = df.groupby('Airline_Name')['Total_Fare'].mean().reset_index().rename(columns={'Total_Fare': 'Avg_Fare'})
    by_segment = df.groupby('Departure_Segment')['Total_Fare'].mean().reset_index().rename(columns={'Total_Fare': 'Avg_Fare'})
    return by_airline, by_segment

def main():
    raw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw'))
    processed_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/processed'))
    os.makedirs(processed_dir, exist_ok=True)
    df = load_all_raw_data(raw_dir)
    if df.empty:
        print('No data found.')
        return
    df = clean_data(df)
    df = remove_outliers_iqr(df)
    df.to_parquet(os.path.join(processed_dir, 'all_flights_cleaned.parquet'), index=False)
    by_airline, by_segment = aggregate(df)
    by_airline.to_csv(os.path.join(processed_dir, 'monthly_summary_by_airline.csv'), index=False)
    by_segment.to_csv(os.path.join(processed_dir, 'monthly_summary_by_segment.csv'), index=False)
    print('Processing complete. Dashboard-ready files saved.')

if __name__ == '__main__':
    main() 