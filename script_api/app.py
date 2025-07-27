import streamlit as st
import pandas as pd
import altair as alt
import os

# --- Page Config ---
st.set_page_config(layout="wide")

# --- Load data ---
@st.cache_data
def load_data():
    # Construct path to the data file relative to the script's location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "processed_data", "aggregated_flight_data.csv")
    df = pd.read_csv(data_path, parse_dates=["Date", "Departure Time", "Arrival Time", "Departure Date", "Arrival Date"])
    df['DateStr'] = df['Date'].dt.strftime('%Y-%m-%d')
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.title("Filters")

# Multi-select for dates
all_dates = sorted(df["DateStr"].unique())
selected_dates = st.sidebar.multiselect("Select Date(s)", all_dates, default=all_dates[:3]) # Default to first 3 dates

# Multi-select for airlines
all_airlines = ["All"] + sorted(df["Airline Name"].unique())
selected_airlines = st.sidebar.multiselect("Select Airline(s)", all_airlines, default=["All"])

# Multi-select for time blocks
all_timeblocks = ["All"] + sorted(df["Time Block"].unique())
selected_timeblocks = st.sidebar.multiselect("Select Time Block(s)", all_timeblocks, default=["All"])

# Price Range Slider
min_price = int(df["Total Fare"].min())
max_price = int(df["Total Fare"].max())
selected_price_range = st.sidebar.slider(
    "Select Price Range (₹)",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price)
)

# Denoising Method Filter
st.sidebar.markdown("---")
st.sidebar.subheader("🔬 Denoising Methods")
all_denoising_methods = ["Raw Mean", "Filtered Mean", "Median", "Trimmed Mean (10%)"]
selected_denoising_methods = st.sidebar.multiselect(
    "Select Denoising Method(s)",
    all_denoising_methods,
    default=all_denoising_methods  # Default to all methods
)


# --- Filtered Data ---
filtered_df = df.copy()

# Apply date filter
if selected_dates:
    filtered_df = filtered_df[filtered_df['DateStr'].isin(selected_dates)]

# Apply airline filter
if "All" not in selected_airlines:
    filtered_df = filtered_df[filtered_df["Airline Name"].isin(selected_airlines)]

# Apply time block filter
if "All" not in selected_timeblocks:
    filtered_df = filtered_df[filtered_df["Time Block"].isin(selected_timeblocks)]
    
# Apply price range filter
filtered_df = filtered_df[
    (filtered_df["Total Fare"] >= selected_price_range[0]) &
    (filtered_df["Total Fare"] <= selected_price_range[1])
]

# --- Title ---
st.title("✈️ Flight Fare Visualizer")
st.caption("Mumbai → Delhi | One-way | Non-stop | Economy")

st.markdown(f"**Total Flights Found:** {len(filtered_df)}")


# --- Selections for Cross-Filtering ---
selection_airline = alt.selection_multi(fields=['Airline Name'], name='airline_selector')
selection_timeblock = alt.selection_multi(fields=['Time Block'], name='timeblock_selector')
selection_hour = alt.selection_interval(encodings=['x'], name='hour_selector')
selection_date = alt.selection_multi(fields=['DateStr'], name='date_selector')


# --- Main Charts ---
st.subheader("📊 Visual Analysis")

col1, col2 = st.columns(2)

with col1:
    # Chart: Average Price by Airline
    airline_chart = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X("Airline Name", sort="-y"),
        y="mean(Total Fare):Q",
        color=alt.condition(selection_airline, alt.value('steelblue'), alt.value('lightgray')),
        tooltip=["Airline Name", "mean(Total Fare):Q"]
    ).add_selection(
        selection_airline
    ).properties(
        title="Average Fare by Airline"
    )
    st.altair_chart(airline_chart, use_container_width=True)

    # Chart: Fare Trend by Departure Hour
    hour_chart = alt.Chart(filtered_df).mark_line(point=True).encode(
        x="Departure Hour:O",
        y="mean(Total Fare):Q",
        color=alt.condition(selection_hour, alt.value('green'), alt.value('lightgray')),
        tooltip=["Departure Hour", "mean(Total Fare):Q"]
    ).add_selection(
        selection_hour
    ).properties(
        title="Average Fare vs Departure Hour"
    )
    st.altair_chart(hour_chart, use_container_width=True)

with col2:
    # Chart: Average Price by Time Block
    time_chart = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X("Time Block", sort=["Morning", "Afternoon", "Evening", "Night"]),
        y="mean(Total Fare):Q",
        color=alt.condition(selection_timeblock, alt.value('orange'), alt.value('lightgray')),
        tooltip=["Time Block", "mean(Total Fare):Q"]
    ).add_selection(
        selection_timeblock
    ).properties(
        title="Average Fare by Time Block"
    )
    st.altair_chart(time_chart, use_container_width=True)
    
    # Combined filter for the scatter plot
    combined_filter = selection_airline & selection_timeblock & selection_hour
    
    # Scatter plot
    scatter_plot = alt.Chart(filtered_df).mark_circle(size=60).encode(
        x='Departure Time:T',
        y='Total Fare:Q',
        color='Airline Name:N',
        tooltip=['Flight Number', 'Airline Name', 'Departure Time', 'Total Fare']
    ).transform_filter(
        combined_filter
    ).properties(
        title="All Flights (click on charts to filter)"
    )
    st.altair_chart(scatter_plot, use_container_width=True)


# --- Price vs Date Chart ---
st.subheader("📅 Average Fare by Date")

date_trend_chart = alt.Chart(filtered_df).mark_line(point=True, strokeWidth=3).encode(
    x=alt.X("DateStr:O", title="Date", axis=alt.Axis(labelAngle=-45)),
    y=alt.Y("mean(Total Fare):Q", title="Average Fare (₹)"),
    color=alt.condition(selection_date, alt.value('red'), alt.value('lightcoral')),
    tooltip=["DateStr:O", "mean(Total Fare):Q", "count():Q"]
).add_selection(
    selection_date
).properties(
    title="Average Fare Trend by Date",
    height=400
)

st.altair_chart(date_trend_chart, use_container_width=True)


# --- Data Table with Sorting ---
with st.expander("🔍 Show and Sort Raw Data Table", expanded=True):
    # Apply cross-filters to the DataFrame for the table
    
    # This part is more complex with altair selections; for now, we show the sidebar-filtered data
    # A full client-side cross-filter on the table would require more advanced callbacks.
    
    # Reorder and select columns for a cleaner view
    display_columns = [
         'Flight Number', 'Airline Name', 'Source City', 
         'Destination City', 'Departure Date', 'Departure Time', 'Arrival Date', 'Arrival Time',
         'Base Fare', 'Tax', 'Total Fare', 'Time Block', 'Layover Type'
    ]
    
    # Filter out columns that might not exist in the dataframe
    existing_display_columns = [col for col in display_columns if col in filtered_df.columns]

    sort_column = st.selectbox(
        "Sort table by",
        options=existing_display_columns,
        index=existing_display_columns.index('Total Fare') # Default to Total Fare
    )
    sort_ascending = st.toggle("Ascending", value=True)
    
    sorted_df = filtered_df.sort_values(by=sort_column, ascending=sort_ascending)
    
    # --- Prepare and Format DataFrame for Display ---
    display_df = sorted_df.copy()

    # Format date and time columns
    display_df['Departure Date'] = display_df['Departure Date'].dt.strftime('%d-%m-%Y')
    display_df['Arrival Date'] = display_df['Arrival Date'].dt.strftime('%d-%m-%Y')
    display_df['Departure Time'] = display_df['Departure Time'].dt.strftime('%H:%M:%S')
    display_df['Arrival Time'] = display_df['Arrival Time'].dt.strftime('%H:%M:%S')
    
    st.dataframe(display_df[existing_display_columns])


# --- FILTERED DENOISING CHARTS SECTION ---
if selected_denoising_methods:
    st.subheader("📈 Filtered Denoising Comparison")
    st.caption(f"Showing selected methods: {', '.join(selected_denoising_methods)}")
    
    # Import required libraries for denoising (moved up here)
    import holidays
    from scipy import stats
    import numpy as np
    
    # Create a copy for denoising analysis
    filter_denoise_df = filtered_df.copy()
    
    # Add weekday/weekend flags
    filter_denoise_df['IsWeekend'] = filter_denoise_df['Date'].dt.dayofweek >= 5
    
    # Add holiday flags using Indian holidays
    india_holidays = holidays.IN()
    filter_denoise_df['IsHoliday'] = filter_denoise_df['Date'].dt.date.apply(lambda x: x in india_holidays)
    
    # Calculate daily aggregates for filtered view
    filter_daily_stats = []
    
    for date_str in sorted(filter_denoise_df['DateStr'].unique()):
        date_data = filter_denoise_df[filter_denoise_df['DateStr'] == date_str]
        
        if len(date_data) > 0:
            fares = date_data['Total Fare'].values
            
            # Calculate all methods but only include selected ones
            methods_data = {}
            
            # Method 1: Raw Mean
            if "Raw Mean" in selected_denoising_methods:
                methods_data['Raw Mean'] = np.mean(fares)
            
            # Method 2: Filtered Mean (exclude weekend/holiday flights)
            if "Filtered Mean" in selected_denoising_methods:
                # Filter out flights from weekends and holidays across all data
                business_day_data = filter_denoise_df[
                    (filter_denoise_df['IsWeekend'] == False) & 
                    (filter_denoise_df['IsHoliday'] == False)
                ]
                
                if len(business_day_data) > 0:
                    # Calculate mean from business days only for the current date
                    current_date_business = business_day_data[business_day_data['DateStr'] == date_str]
                    if len(current_date_business) > 0:
                        methods_data['Filtered Mean'] = np.mean(current_date_business['Total Fare'].values)
                    else:
                        # If current date has no business day flights, use overall business day average
                        methods_data['Filtered Mean'] = np.mean(business_day_data['Total Fare'].values)
                else:
                    methods_data['Filtered Mean'] = np.mean(fares)  # Fallback to raw mean
            
            # Method 3: Median
            if "Median" in selected_denoising_methods:
                methods_data['Median'] = np.median(fares)
            
            # Method 4: Trimmed Mean
            if "Trimmed Mean (10%)" in selected_denoising_methods:
                if len(fares) >= 5:
                    methods_data['Trimmed Mean (10%)'] = stats.trim_mean(fares, 0.1)
                else:
                    methods_data['Trimmed Mean (10%)'] = np.mean(fares)
            
            # Add to stats with date info
            for method, value in methods_data.items():
                filter_daily_stats.append({
                    'Date': date_str,
                    'Method': method,
                    'Average Fare': value,
                    'Flight Count': len(date_data)
                })
    
    # Create filtered chart
    if filter_daily_stats:
        filter_plot_data = pd.DataFrame(filter_daily_stats)
        
        # Define consistent colors for each method
        method_colors = {
            'Raw Mean': '#e74c3c',      # Red
            'Filtered Mean': '#3498db',  # Blue  
            'Median': '#2ecc71',        # Green
            'Trimmed Mean (10%)': '#f39c12'  # Orange
        }
        
        # Create color scale for selected methods only
        selected_colors = [method_colors[method] for method in selected_denoising_methods]
        
        filtered_denoising_chart = alt.Chart(filter_plot_data).mark_line(
            point=True, 
            strokeWidth=3,
            opacity=0.8
        ).encode(
            x=alt.X('Date:O', title='Date', axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Average Fare:Q', title='Average Fare (₹)'),
            color=alt.Color(
                'Method:N',
                scale=alt.Scale(
                    domain=selected_denoising_methods,
                    range=selected_colors
                ),
                legend=alt.Legend(title="Denoising Method", orient="top")
            ),
            tooltip=['Date:O', 'Method:N', 'Average Fare:Q', 'Flight Count:Q']
        ).properties(
            title=f'Fare Comparison: {len(selected_denoising_methods)} Selected Method(s)',
            height=400
        )
        
        st.altair_chart(filtered_denoising_chart, use_container_width=True)
        
        # Show summary statistics for selected methods
        if len(selected_denoising_methods) > 1:
            st.subheader("📊 Method Comparison Summary")
            
            # Calculate statistics for each selected method
            comparison_stats = {}
            for method in selected_denoising_methods:
                method_data = filter_plot_data[filter_plot_data['Method'] == method]['Average Fare']
                comparison_stats[method] = {
                    'Mean': method_data.mean(),
                    'Std Dev': method_data.std(),
                    'Min': method_data.min(),
                    'Max': method_data.max()
                }
            
            # Display in columns
            cols = st.columns(len(selected_denoising_methods))
            for i, (method, stats) in enumerate(comparison_stats.items()):
                with cols[i]:
                    st.markdown(f"**{method}**")
                    st.metric("Average", f"₹{stats['Mean']:,.0f}")
                    st.metric("Std Dev", f"₹{stats['Std Dev']:,.0f}")
                    st.metric("Range", f"₹{stats['Min']:,.0f} - ₹{stats['Max']:,.0f}")
        
    else:
        st.warning("No data available for the selected denoising methods with current filters.")

else:
    st.info("👈 Please select at least one denoising method from the sidebar to view comparison charts.")


# --- NEW SECTION: Denoising Analysis ---
st.subheader("🔬 Monthly Fare Denoising Analysis")
st.caption("Comparing different statistical methods to reduce noise in daily fare data")

# Import required libraries for denoising
import holidays
from scipy import stats
import numpy as np

# Create a copy for denoising analysis (to avoid altering original charts)
denoise_df = filtered_df.copy()

# Add weekday/weekend flags
denoise_df['IsWeekend'] = denoise_df['Date'].dt.dayofweek >= 5

# Add holiday flags using Indian holidays
india_holidays = holidays.IN()
denoise_df['IsHoliday'] = denoise_df['Date'].dt.date.apply(lambda x: x in india_holidays)

# Calculate daily aggregates using different denoising methods
daily_stats = []

for date_str in sorted(denoise_df['DateStr'].unique()):
    date_data = denoise_df[denoise_df['DateStr'] == date_str]
    
    if len(date_data) > 0:
        fares = date_data['Total Fare'].values
        
        # Method 1: Raw Mean (no filtering)
        raw_mean = np.mean(fares)
        
        # Method 2: Filtered Mean (exclude weekend/holiday flights)
        # Filter out flights from weekends and holidays across all data
        business_day_data = denoise_df[
            (denoise_df['IsWeekend'] == False) & 
            (denoise_df['IsHoliday'] == False)
        ]
        
        if len(business_day_data) > 0:
            # Calculate mean from business days only for the current date
            current_date_business = business_day_data[business_day_data['DateStr'] == date_str]
            if len(current_date_business) > 0:
                filtered_mean = np.mean(current_date_business['Total Fare'].values)
            else:
                # If current date has no business day flights, use overall business day average
                filtered_mean = np.mean(business_day_data['Total Fare'].values)
        else:
            filtered_mean = raw_mean  # Fallback to raw mean
        
        # Method 3: Median (robust to outliers)
        median_fare = np.median(fares)
        
        # Method 4: Trimmed Mean (10% trimming on each side)
        if len(fares) >= 5:  # Need at least 5 data points for 10% trimming
            trimmed_mean = stats.trim_mean(fares, 0.1)
        else:
            trimmed_mean = raw_mean
        
        # Get weekend/holiday status for the current date
        is_weekend = date_data['IsWeekend'].iloc[0]
        is_holiday = date_data['IsHoliday'].iloc[0]
        
        daily_stats.append({
            'Date': date_str,
            'Raw Mean': raw_mean,
            'Filtered Mean': filtered_mean,
            'Median': median_fare,
            'Trimmed Mean (10%)': trimmed_mean,
            'Flight Count': len(date_data),
            'IsWeekend': is_weekend,
            'IsHoliday': is_holiday
        })

# Convert to DataFrame for plotting
daily_stats_df = pd.DataFrame(daily_stats)

# Create comparison chart
if not daily_stats_df.empty:
    # Reshape data for Altair (melt the dataframe)
    plot_data = daily_stats_df.melt(
        id_vars=['Date', 'Flight Count', 'IsWeekend', 'IsHoliday'],
        value_vars=['Raw Mean', 'Filtered Mean', 'Median', 'Trimmed Mean (10%)'],
        var_name='Method',
        value_name='Average Fare'
    )
    
    # Create the comparison chart with consistent colors
    denoising_chart = alt.Chart(plot_data).mark_line(
        point=True, 
        strokeWidth=3,
        opacity=0.9
    ).encode(
        x=alt.X('Date:O', title='Date', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Average Fare:Q', title='Average Fare (₹)'),
        color=alt.Color('Method:N', 
                       scale=alt.Scale(
                           domain=['Raw Mean', 'Filtered Mean', 'Median', 'Trimmed Mean (10%)'],
                           range=['#e74c3c', '#3498db', '#2ecc71', '#f39c12']  # Red, Blue, Green, Orange
                       ),
                       legend=alt.Legend(title="Denoising Method", orient="top")),
        tooltip=['Date:O', 'Method:N', 'Average Fare:Q', 'Flight Count:Q']
    ).properties(
        title='Daily Average Fare: Raw vs. Denoised Methods (All Methods)',
        height=400
    )
    
    st.altair_chart(denoising_chart, use_container_width=True)
    
    # Calculate and display monthly summary statistics
    st.subheader("📈 Monthly Summary Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Overall Monthly Averages:**")
        monthly_averages = {
            'Raw Mean': daily_stats_df['Raw Mean'].mean(),
            'Filtered Mean': daily_stats_df['Filtered Mean'].mean(),
            'Median': daily_stats_df['Median'].mean(),
            'Trimmed Mean (10%)': daily_stats_df['Trimmed Mean (10%)'].mean()
        }
        
        for method, avg_fare in monthly_averages.items():
            st.metric(f"{method}", f"₹{avg_fare:,.0f}")
    
    with col2:
        st.write("**Variability Analysis (Standard Deviation):**")
        variability = {
            'Raw Mean': daily_stats_df['Raw Mean'].std(),
            'Filtered Mean': daily_stats_df['Filtered Mean'].std(),
            'Median': daily_stats_df['Median'].std(),
            'Trimmed Mean (10%)': daily_stats_df['Trimmed Mean (10%)'].std()
        }
        
        for method, std_fare in variability.items():
            st.metric(f"{method}", f"₹{std_fare:.0f}")
    
    # Method recommendation
    st.subheader("💡 Method Recommendation")
    
    # Find the method with lowest standard deviation (most stable)
    most_stable_method = min(variability.items(), key=lambda x: x[1])
    
    st.info(f"""
    **Most Stable Method:** {most_stable_method[0]} (σ = ₹{most_stable_method[1]:.0f})
    
    **Method Explanations:**
    - **Raw Mean**: Simple average of all flights per day
    - **Filtered Mean**: Excludes weekend/holiday data to reduce demand spikes
    - **Median**: Middle value, robust against extreme outliers
    - **Trimmed Mean (10%)**: Removes top/bottom 10% of fares before averaging
    
    *Lower standard deviation indicates more consistent day-to-day pricing.*
    """)
    
    # Show the detailed daily statistics table
    with st.expander("📊 View Daily Statistics Details"):
        st.dataframe(
            daily_stats_df.round(0).style.format({
                'Raw Mean': '₹{:,.0f}',
                'Filtered Mean': '₹{:,.0f}',
                'Median': '₹{:,.0f}',
                'Trimmed Mean (10%)': '₹{:,.0f}'
            })
        )

else:
    st.warning("No data available for denoising analysis with current filters.")

