import streamlit as st
import pandas as pd
import altair as alt

# --- Load and clean data ---
df = pd.read_csv("listings.csv")

# --- Common cleaning ---
df = df[['host_neighbourhood', 'price', 'availability_365', 'room_type', 'accommodates', 'bathrooms', 'beds']].dropna()
df = df[df['host_neighbourhood'] != ""]

# Convert columns
df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)
df['accommodates'] = df['accommodates'].astype(int)
df['beds'] = pd.to_numeric(df['beds'], errors='coerce')
df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')
df = df.dropna()

# Calculate estimated revenue
df['estimated_revenue_365d'] = df['price'] * df['availability_365']


# =======================
# 1. Revenue Bar Chart
# =======================

st.title("DC Airbnb Data Explorer")

st.header("📊 Revenue by Neighborhood")

# Sidebar inputs
metric = st.selectbox(
    "Select revenue metric:",
    options=["Average Revenue", "Total Revenue"]
)

top_n = st.slider(
    "Select number of neighborhoods to display:",
    min_value=5, max_value=100, value=30
)

# Determine aggregation
agg_func = 'mean' if metric == "Average Revenue" else 'sum'
agg_col = 'avg_estimated_revenue' if metric == "Average Revenue" else 'total_estimated_revenue'

# Get top neighborhoods by count
top_neighborhoods = df['host_neighbourhood'].value_counts().nlargest(top_n).index
df_top = df[df['host_neighbourhood'].isin(top_neighborhoods)]

# Group and aggregate
df_grouped = df_top.groupby('host_neighbourhood', as_index=False).agg(
    {
        'estimated_revenue_365d': agg_func
    }
).rename(columns={'estimated_revenue_365d': agg_col})

# Bar chart
bar_chart = alt.Chart(df_grouped).mark_bar().encode(
    x=alt.X('host_neighbourhood:N', sort='-y', title='Host Neighborhood'),
    y=alt.Y(f'{agg_col}:Q', title=f'{metric} (365d)'),
    tooltip=['host_neighbourhood', f'{agg_col}']
).properties(
    width=700,
    height=400,
    title=f'Top {top_n} Neighborhoods by Listing Count: {metric}'
).configure_axisX(
    labelAngle=-45
)

st.altair_chart(bar_chart, use_container_width=True)


# =======================
# 2. Bubble Chart
# =======================

st.header("🛏️ Room Types: Beds, Baths, Accommodates")

# Create chart
bubble_chart = alt.Chart(df).mark_circle().encode(
    x=alt.X('room_type:N', title='Room Type'),
    y=alt.Y('accommodates:Q', title='Accommodates'),
    size=alt.Size('beds:Q', title='Beds'),
    color=alt.Color('bathrooms:Q', title='Bathrooms', scale=alt.Scale(scheme='blues')),
    tooltip=['room_type', 'accommodates', 'beds', 'bathrooms']
).properties(
    width=700,
    height=400,
    title='Beds, Bathrooms, Room Type vs Accommodates'
)

st.altair_chart(bubble_chart, use_container_width=True)


# =======================
# 3. Price vs Listings Scatter
# =======================

st.header("💵 Price vs Number of Listings (by Neighborhood)")

# Prep data
df_price_plot = df[['host_neighbourhood', 'price']].copy()
df_price_plot = df_price_plot[df_price_plot['price'] < 1000]  # Filter out high outliers

# Count listings per price point and neighborhood
df_price_plot = df_price_plot.groupby(['price', 'host_neighbourhood']).size().reset_index(name='listing_count')

# Selection for highlighting
highlight = alt.selection_point(fields=['host_neighbourhood'], bind='legend')

# Scatter chart
scatter_chart = alt.Chart(df_price_plot).mark_circle(size=60).encode(
    x=alt.X('price:Q', title='Price (USD)'),
    y=alt.Y('listing_count:Q', title='Number of Listings'),
    color=alt.Color('host_neighbourhood:N', title='Neighborhood'),
    tooltip=['host_neighbourhood', 'price', 'listing_count'],
    opacity=alt.condition(highlight, alt.value(1), alt.value(0.2))
).add_params(
    highlight
).properties(
    width=700,
    height=400,
    title='Listings by Price and Neighborhood'
).interactive()

st.altair_chart(scatter_chart, use_container_width=True)
