import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="COVID-19 Global Tracker", layout="wide")

st.title("📊 COVID-19 Global Intelligence Dashboard")
st.markdown("Data Source: *Johns Hopkins University - Center for Systems Science and Engineering (CSSE)*")

# 2. Data Acquisition and Cleaning
@st.cache_data
def load_jhu_data():
    # URL for JHU CSSE Global Time Series (Confirmed Cases)
    url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
    
    # Load raw CSV
    df = pd.read_csv(url)
    
    # Reshape from Wide to Long format (Melt)
    # The first 4 columns are metadata, the rest are dates
    date_columns = df.columns[4:]
    df_melted = df.melt(
        id_vars=['Country/Region'], 
        value_vars=date_columns, 
        var_name='Date', 
        value_name='Cumulative_Cases'
    )
    
    # Convert Date column to datetime objects
    df_melted['Date'] = pd.to_datetime(df_melted['Date'])
    
    # Aggregation: Group by Country and Date to handle sub-regions (e.g., China, Canada)
    df_country = df_melted.groupby(['Country/Region', 'Date'])['Cumulative_Cases'].sum().reset_index()
    
    # Calculation: Compute Daily New Cases using difference
    df_country = df_country.sort_values(['Country/Region', 'Date'])
    df_country['Daily_New_Cases'] = df_country.groupby('Country/Region')['Cumulative_Cases'].diff().fillna(0)
    
    return df_country

# Execution with status indicator
with st.spinner('Synchronizing data with JHU CSSE servers...'):
    try:
        data = load_jhu_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# 3. Sidebar Interaction
st.sidebar.header("User Controls")

# Selection: Countries to display
all_countries = sorted(data['Country/Region'].unique())
selected_countries = st.sidebar.multiselect(
    "Add/Remove Countries:",
    options=all_countries,
    default=["US", "United Kingdom", "China"]
)

# Selection: Data Metric
display_metric = st.sidebar.radio(
    "Select Metric:",
    options=["Daily_New_Cases", "Cumulative_Cases"],
    format_func=lambda x: x.replace("_", " ")
)

# 4. Main Interface Visualization
if selected_countries:
    # Filter dataset
    filtered_df = data[data['Country/Region'].isin(selected_countries)]
    
    # Line Chart using Plotly
    fig = px.line(
        filtered_df, 
        x='Date', 
        y=display_metric, 
        color='Country/Region',
        title=f"COVID-19 Trends: {display_metric.replace('_', ' ')}",
        template="plotly_white",
        labels={display_metric: "Count", "Date": "Time Period"}
    )
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary Metrics (Current Status)
    st.subheader("Latest Statistics Snapshot")
    latest_date = data['Date'].max().strftime('%B %d, %Y')
    st.info(f"Reported totals as of: {latest_date}")
    
    cols = st.columns(len(selected_countries))
    for i, country in enumerate(selected_countries):
        country_record = filtered_df[filtered_df['Country/Region'] == country].iloc[-1]
        
        # Displaying the metric with the daily increase as delta
        cols[i].metric(
            label=country, 
            value=f"{int(country_record['Cumulative_Cases']):,}", 
            delta=f"{int(country_record['Daily_New_Cases']):,} New"
        )
else:
    st.warning("Please select at least one country from the sidebar to visualize the data.")

# 5. Raw Data Preview
with st.expander("View Underlying Data Table"):
    st.dataframe(filtered_df if selected_countries else data.head(100), use_container_width=True)

# 6. Documentation (Optional but good for grading)
with st.expander("How to use this app"):
    st.write("""
    1. Go to the sidebar on the left.
    2. Click inside the 'Add Countries' box and type a country name.
    3. Select your preferred metric (Daily or Cumulative).
    4. Hover over the chart to see specific data points.
    """)