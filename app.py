# app.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Gold Price Tracker - Hyderabad",
    page_icon="💰",
    layout="wide"
)

# Load data
@st.cache_data(ttl=3600)
def load_data():
    conn = sqlite3.connect('gold_prices.db')
    query = '''
        SELECT date, timestamp, price_per_10g
        FROM gold_prices
        ORDER BY timestamp DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

df = load_data()

# Header
st.title("💰 22K Gold Price Tracker - Hyderabad")
st.markdown("### Tracking 22 Karat Gold Price per 10 grams in INR")

# Current Price
if not df.empty:
    current_price = df.iloc[0]['price_per_10g']
    previous_price = df.iloc[1]['price_per_10g'] if len(df) > 1 else current_price
    change = current_price - previous_price
    change_percent = (change / previous_price * 100) if previous_price else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Current Price (10g)",
            value=f"₹{current_price:,.2f}",
            delta=f"₹{change:+,.2f} ({change_percent:+.2f}%)"
        )

    with col2:
        today_avg = df[df['date'] == df.iloc[0]['date']]['price_per_10g'].mean()
        st.metric(
            label="Today's Average",
            value=f"₹{today_avg:,.2f}"
        )

    with col3:
        week_avg = df[df['timestamp'] >= datetime.now() - timedelta(days=7)]['price_per_10g'].mean()
        st.metric(
            label="7-Day Average",
            value=f"₹{week_avg:,.2f}"
        )

    with col4:
        month_avg = df[df['timestamp'] >= datetime.now() - timedelta(days=30)]['price_per_10g'].mean()
        st.metric(
            label="30-Day Average",
            value=f"₹{month_avg:,.2f}"
        )

# Chart
st.subheader("Price Trend")

# Date range selector
col1, col2 = st.columns(2)
with col1:
    days = st.selectbox(
        "Select time range",
        [7, 14, 30, 90, 180, 365],
        index=2,
        format_func=lambda x: f"Last {x} days"
    )

# Filter data
start_date = datetime.now() - timedelta(days=days)
filtered_df = df[df['timestamp'] >= start_date]

# Create chart
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=filtered_df['timestamp'],
    y=filtered_df['price_per_10g'],
    mode='lines+markers',
    name='Gold Price',
    line=dict(color='gold', width=2),
    marker=dict(size=6)
))

fig.update_layout(
    title=f"22K Gold Price Trend - Last {days} Days",
    xaxis_title="Date",
    yaxis_title="Price (₹ per 10g)",
    hovermode='x unified',
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Statistics
st.subheader("Price Statistics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Highest", f"₹{filtered_df['price_per_10g'].max():,.2f}")

with col2:
    st.metric("Lowest", f"₹{filtered_df['price_per_10g'].min():,.2f}")

with col3:
    volatility = filtered_df['price_per_10g'].std()
    st.metric("Volatility (Std Dev)", f"₹{volatility:,.2f}")

# Historical data table
st.subheader("Recent Updates")
st.dataframe(
    filtered_df.head(20)[['timestamp', 'price_per_10g']].rename(
        columns={
            'timestamp': 'Date & Time',
            'price_per_10g': 'Price (₹/10g)'
        }
    ),
    use_container_width=True
)

# Download data
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="Download Data as CSV",
    data=csv,
    file_name=f"gold_prices_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.markdown("""
**Note:** Prices are indicative and may vary from actual market rates.  
Last updated: {}
""".format(df.iloc[0]['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if not df.empty else 'N/A'))