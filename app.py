import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import matplotlib.pyplot as plt
import circlify
from io import BytesIO



# Set page layout to wide
st.set_page_config(layout="wide")

# --- Load and clean data ---
df = pd.read_csv("listings.csv")
df = df[['host_neighbourhood', 'price', 'availability_365', 'room_type', 'accommodates', 'bathrooms', 'beds', 'host_since', 'review_scores_rating', 'host_is_superhost']].dropna()
df = df[df['host_neighbourhood'] != ""]

# Convert columns
df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)
df['accommodates'] = df['accommodates'].astype(int)
df['beds'] = pd.to_numeric(df['beds'], errors='coerce')
df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')
df['host_since'] = pd.to_datetime(df['host_since'], errors='coerce')
df = df.dropna()

# Calculate estimated revenue
df['estimated_revenue_365d'] = df['price'] * df['availability_365']
df['host_year'] = df['host_since'].dt.year

# --- Title ---
st.title("DC Airbnb Data Explorer")

# --- Sidebar Filters ---
st.sidebar.header("Filters")
top_n = st.sidebar.slider("Select number of neighborhoods to display:", min_value=5, max_value=100, value=30)

# Neighborhood filter
top_neighborhoods = df['host_neighbourhood'].value_counts().nlargest(top_n).index.tolist()
selected_neighborhoods = st.sidebar.multiselect(
    "Filter neighborhoods: (optional)",
    options=top_neighborhoods,
    default=top_neighborhoods
)

# Filter dataset
df_filtered = df[df['host_neighbourhood'].isin(selected_neighborhoods)]

# --- Metric Selection (Above Bar Chart) ---
st.subheader("Metric by Neighborhood")
metric = st.selectbox(
    "Select metric:",
    options=["Average Revenue", "Total Revenue", "Average Price", "Total Listings"]
)

# Determine aggregation
if metric == "Average Revenue":
    agg_col = "avg_estimated_revenue"
    df_grouped = df_filtered.groupby('host_neighbourhood', as_index=False).agg(
        { 'estimated_revenue_365d': 'mean' }
    ).rename(columns={'estimated_revenue_365d': agg_col})

elif metric == "Total Revenue":
    agg_col = "total_estimated_revenue"
    df_grouped = df_filtered.groupby('host_neighbourhood', as_index=False).agg(
        { 'estimated_revenue_365d': 'sum' }
    ).rename(columns={'estimated_revenue_365d': agg_col})

elif metric == "Average Price":
    agg_col = "avg_price"
    df_grouped = df_filtered.groupby('host_neighbourhood', as_index=False).agg(
        { 'price': 'mean' }
    ).rename(columns={'price': agg_col})

elif metric == "Total Listings":
    agg_col = "total_listings"
    df_grouped = df_filtered.groupby('host_neighbourhood').size().reset_index(name=agg_col)

# --- Bar Chart ---
bar_chart = alt.Chart(df_grouped).mark_bar().encode(
    x=alt.X('host_neighbourhood:N', sort='-y', title='Host Neighborhood'),
    y=alt.Y(f'{agg_col}:Q', title=metric),
    tooltip=['host_neighbourhood', f'{agg_col}']
).properties(
    width=900,
    height=500,
    title=f'{metric} by Neighborhood'
).configure_axisX(
    labelAngle=-45
)

st.altair_chart(bar_chart, use_container_width=True)

# --- Bubble Chart ---
st.header("Room Types: Beds, Baths, Accommodates")
room_types = df_filtered['room_type'].unique().tolist()
selected_room_types = st.multiselect("Select room types:", options=room_types, default=room_types)
df_bubble = df_filtered[df_filtered['room_type'].isin(selected_room_types)]

bubble_chart = alt.Chart(df_bubble).mark_circle().encode(
    x=alt.X('room_type:N', title='Room Type'),
    y=alt.Y('accommodates:Q', title='Accommodates'),
    size=alt.Size('beds:Q', title='Beds'),
    color=alt.Color('bathrooms:Q', title='Bathrooms', scale=alt.Scale(scheme='blues')),
    tooltip=['room_type', 'accommodates', 'beds', 'bathrooms']
).properties(
    width=900,
    height=500,
    title='Beds, Bathrooms, Room Type vs Accommodates'
).interactive()

st.altair_chart(bubble_chart, use_container_width=True)

# --- Scatter Plot: Price vs Availability ---
st.header("Price vs Availability")

df_price_plot = df_filtered[df_filtered['price'] < 1000][['host_neighbourhood', 'price', 'availability_365']].copy()

# Selection that toggles on click (not mouseout)
highlight = alt.selection_point(
    fields=['host_neighbourhood'],
    toggle=True,
    nearest=True,
    on="click"
)

scatter_chart = alt.Chart(df_price_plot).mark_circle(size=60).encode(
    x=alt.X('price:Q', title='Price (USD)'),
    y=alt.Y('availability_365:Q', title='Availability (Days per Year)'),
    color=alt.Color('host_neighbourhood:N', title='Neighborhood'),
    tooltip=['host_neighbourhood', 'price', 'availability_365'],
    opacity=alt.condition(highlight, alt.value(1), alt.value(0.075))
).add_params(
    highlight
).properties(
    width=900,
    height=500,
    title='Availability vs Price by Neighborhood (Click to Filter Neighborhoods)'
).interactive()

st.altair_chart(scatter_chart, use_container_width=True)

# --- Linked Strip Chart ---
st.header("Review Scores by Host Year and Superhost Status")

strip_chart = alt.Chart(df_filtered).mark_tick(thickness=2, size=12).encode(
    x=alt.X('host_year:O', title='Host Since (Year)'),
    y=alt.Y('review_scores_rating:Q', title='Review Score Rating'),
    color=alt.Color('host_is_superhost:N',
                    title='Superhost',
                    scale=alt.Scale(domain=['t', 'f'],
                                    range=['lightgreen', 'lightcoral'])),
    tooltip=['host_year', 'review_scores_rating', 'host_is_superhost', 'host_neighbourhood'],
    opacity=alt.condition(highlight, alt.value(1), alt.value(0.075))
).add_params(
    highlight
).properties(
    width=900,
    height=500,
    title='Review Scores by Host Year and Superhost Status (Click to Filter by Neighborhood)'
)

st.altair_chart(strip_chart, use_container_width=True)






df = pd.read_csv("open-llm-leaderboards.csv")



df.columns = df.columns.str.strip()
df = df.rename(columns={"Average ⬆️": "Average"})
df["CO₂ cost (kg)"] = pd.to_numeric(df["CO₂ cost (kg)"], errors="coerce")
df["Upload To Hub Date"] = pd.to_datetime(df["Upload To Hub Date"], errors="coerce")
df = df.dropna(subset=["CO₂ cost (kg)", "Upload To Hub Date", "Type"])

# --- Group for bubble chart ---
grouped = df.groupby("Type", as_index=False)["CO₂ cost (kg)"].mean()
grouped = grouped.sort_values("CO₂ cost (kg)", ascending=False).reset_index(drop=True)

# --- Circlify for bubble positions ---
circles = circlify.circlify(
    grouped["CO₂ cost (kg)"].tolist(),
    show_enclosure=False,
    target_enclosure=circlify.Circle(x=0, y=0, r=1)
)

# --- Plot with Matplotlib ---
fig, ax = plt.subplots(figsize=(10, 10))
ax.axis('off')
lim = max(max(abs(c.x) + c.r, abs(c.y) + c.r) for c in circles)
plt.xlim(-lim, lim)
plt.ylim(-lim, lim)

# Color palette
colors = plt.cm.tab20.colors
type_colors = {t: colors[i % len(colors)] for i, t in enumerate(grouped["Type"])}

# Draw bubbles
for circle, row in zip(circles, grouped.itertuples()):
    x, y, r = circle.x, circle.y, circle.r
    label = f"{row.Type}\n{row._2:,.0f}"  # _2 is CO₂ cost from namedtuple
    ax.add_patch(plt.Circle((x, y), r, alpha=0.6, linewidth=2, color=type_colors[row.Type]))
    ax.text(x, y, label, ha='center', va='center', fontsize=10)

# Save to in-memory buffer
buf = BytesIO()
plt.savefig(buf, format="png", bbox_inches='tight')
buf.seek(0)

# --- Display in Streamlit ---
st.image(buf, caption="Packed Bubble Chart: Avg CO₂ Cost per Model Type", use_column_width=True)

# --- Area chart data ---
df["Month"] = df["Upload To Hub Date"].dt.to_period("M").dt.to_timestamp()
monthly = df.groupby(["Month", "Type"])["CO₂ cost (kg)"].sum().reset_index()
monthly["Cumulative CO₂"] = monthly.sort_values("Month").groupby("Type")["CO₂ cost (kg)"].cumsum()

# --- Altair interactive chart ---
type_selection = alt.selection_point(fields=["Type"], bind="legend")
zoom = alt.selection_interval(bind="scales")

area_chart = alt.Chart(monthly).mark_area(interpolate="monotone").encode(
    x=alt.X("Month:T", title="Month", axis=alt.Axis(format="%b %Y")),
    y=alt.Y("Cumulative CO₂:Q", title="Cumulative CO₂ Emissions (kg)"),
    color=alt.Color("Type:N", legend=alt.Legend(title="Model Type")),
    opacity=alt.condition(type_selection, alt.value(1.0), alt.value(0.15)),
    tooltip=[
        alt.Tooltip("Month:T", title="Month", format="%B %Y"),
        alt.Tooltip("Type:N"),
        alt.Tooltip("Cumulative CO₂:Q", format=",.0f")
    ]
).add_params(type_selection, zoom).properties(
    title="Cumulative CO₂ Emissions Over Time",
    width=800,
    height=400
)

st.altair_chart(area_chart, use_container_width=True)
