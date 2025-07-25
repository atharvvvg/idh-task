import streamlit as st
import pandas as pd
import altair as alt

# --- Page Config ---
st.set_page_config(layout="wide")

# --- Load data ---
@st.cache_data
def load_data():
    df = pd.read_csv("processed_data/aggregated_flight_data.csv", parse_dates=["Date", "Departure Full Time", "Arrival Full Time"])
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
        x='Departure Full Time:T',
        y='Total Fare:Q',
        color='Airline Name:N',
        tooltip=['Flight Number', 'Airline Name', 'Departure Full Time', 'Total Fare']
    ).transform_filter(
        combined_filter
    ).properties(
        title="All Flights (click on charts to filter)"
    )
    st.altair_chart(scatter_plot, use_container_width=True)


# --- Data Table with Sorting ---
with st.expander("🔍 Show and Sort Raw Data Table", expanded=True):
    # Apply cross-filters to the DataFrame for the table
    
    # This part is more complex with altair selections; for now, we show the sidebar-filtered data
    # A full client-side cross-filter on the table would require more advanced callbacks.
    
    sort_column = st.selectbox(
        "Sort table by",
        options=filtered_df.columns,
        index=list(filtered_df.columns).index('Total Fare') # Default to Total Fare
    )
    sort_ascending = st.toggle("Ascending", value=True)
    
    sorted_df = filtered_df.sort_values(by=sort_column, ascending=sort_ascending)
    st.dataframe(sorted_df)

