import streamlit as st
import pandas as pd
import altair as alt

# Load and clean data
df = pd.read_csv("listings.csv")
df = df[['host_neighbourhood', 'price', 'availability_365']].dropna()
df = df[df['host_neighbourhood'] != ""]

# Convert price to numeric
df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)

# Compute estimated revenue
df['estimated_revenue_365d'] = df['price'] * df['availability_365']

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

# Create bar chart
chart = alt.Chart(df_grouped).mark_bar().encode(
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

st.altair_chart(chart, use_container_width=True)

