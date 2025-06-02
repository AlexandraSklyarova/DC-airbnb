import streamlit as st
import pandas as pd
import altair as alt

# Set wide layout
st.set_page_config(layout="wide")

# Load and clean data
raw_df = pd.read_csv("listings.csv")

# Main cleaned dataset
columns_needed = ['host_neighbourhood', 'price', 'availability_365', 'room_type', 'accommodates', 'bathrooms', 'beds', 'host_since', 'review_scores_rating', 'host_is_superhost']
df = raw_df[columns_needed].dropna()
df = df[df['host_neighbourhood'] != ""]

# Type conversions

# Price
df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)

# Beds, baths, accommodates
df['accommodates'] = df['accommodates'].astype(int)
df['beds'] = pd.to_numeric(df['beds'], errors='coerce')
df['bathrooms'] = pd.to_numeric(df['bathrooms'], errors='coerce')

# Host since year
df['host_since'] = pd.to_datetime(df['host_since'], errors='coerce')
df = df.dropna(subset=['host_since'])
df['host_year'] = df['host_since'].dt.year

# Filter review scores
df = df[df['review_scores_rating'].between(0, 100)]

# Estimated revenue
df['estimated_revenue_365d'] = df['price'] * df['availability_365']

# Title
st.title("🏠 DC Airbnb Data Explorer")

# Layout columns
col1, col2 = st.columns([1.2, 1.0])

# --------------------------
# Column 1: Revenue & Bubble
# --------------------------
with col1:
    st.header("📊 Revenue by Neighborhood")

    metric = st.selectbox("Select revenue metric:", ["Average Revenue", "Total Revenue"])
    top_n = st.slider("Select number of neighborhoods to display:", 5, 100, 30)

    agg_func = 'mean' if metric == "Average Revenue" else 'sum'
    agg_col = 'avg_estimated_revenue' if metric == "Average Revenue" else 'total_estimated_revenue'

    top_neighborhoods = df['host_neighbourhood'].value_counts().nlargest(top_n).index
    df_top = df[df['host_neighbourhood'].isin(top_neighborhoods)]

    df_grouped = df_top.groupby('host_neighbourhood', as_index=False).agg({
        'estimated_revenue_365d': agg_func
    }).rename(columns={'estimated_revenue_365d': agg_col})

    bar_chart = alt.Chart(df_grouped).mark_bar().encode(
        x=alt.X('host_neighbourhood:N', sort='-y', title='Host Neighborhood'),
        y=alt.Y(f'{agg_col}:Q', title=f'{metric} (365d)'),
        tooltip=['host_neighbourhood', f'{agg_col}']
    ).properties(
        width=900,
        height=500,
        title=f'Top {top_n} Neighborhoods by Listing Count: {metric}'
    ).configure_axisX(labelAngle=-45)

    st.altair_chart(bar_chart, use_container_width=True)

    st.markdown("###")
    st.header("🛏️ Room Types: Beds, Baths, Accommodates")

    # Multiselect filter
    available_room_types = df['room_type'].unique().tolist()
    selected_room_types = st.multiselect(
        "Select Room Types to Display:",
        options=available_room_types,
        default=available_room_types
    )

    df_filtered = df[df['room_type'].isin(selected_room_types)]
    room_type_selection = alt.selection_point(fields=['room_type'], bind='legend')

    bubble_chart = alt.Chart(df_filtered).mark_circle().encode(
        x=alt.X('room_type:N', title='Room Type'),
        y=alt.Y('accommodates:Q', title='Accommodates'),
        size=alt.Size('beds:Q', title='Beds'),
        color=alt.Color('bathrooms:Q', title='Bathrooms', scale=alt.Scale(scheme='blues')),
        tooltip=['room_type', 'accommodates', 'beds', 'bathrooms'],
        opacity=alt.condition(room_type_selection, alt.value(1), alt.value(0.3))
    ).add_params(
        room_type_selection
    ).properties(
        width=900,
        height=500,
        title='Beds, Bathrooms, Room Type vs Accommodates'
    ).interactive()

    st.altair_chart(bubble_chart, use_container_width=True)

# --------------------------
# Column 2: Price Scatter + Strip
# --------------------------
with col2:
    st.header("💵 Price vs Number of Listings")

    price_df = df[df['price'] < 1000]
    price_df = price_df.groupby(['price', 'host_neighbourhood']).size().reset_index(name='listing_count')

    highlight = alt.selection_point(fields=['host_neighbourhood'], bind='legend')

    scatter_chart = alt.Chart(price_df).mark_circle(size=60).encode(
        x=alt.X('price:Q', title='Price (USD)'),
        y=alt.Y('listing_count:Q', title='Number of Listings'),
        color=alt.Color('host_neighbourhood:N', title='Neighborhood'),
        tooltip=['host_neighbourhood', 'price', 'listing_count'],
        opacity=alt.condition(highlight, alt.value(1), alt.value(0.2))
    ).add_params(
        highlight
    ).properties(
        width=900,
        height=500,
        title='Listings by Price and Neighborhood'
    ).interactive()

    st.altair_chart(scatter_chart, use_container_width=True)

    st.markdown("###")
    st.header("⭐ Review Scores by Host Year")

    # Link strip plot to same selection
    strip_chart = alt.Chart(df).mark_tick(thickness=2, size=12).encode(
        x=alt.X('host_year:O', title='Host Since (Year)'),
        y=alt.Y('review_scores_rating:Q', title='Review Score Rating'),
        color=alt.Color('host_is_superhost:N',
                        title='Superhost',
                        scale=alt.Scale(domain=['t', 'f'], range=['lightgreen', 'lightcoral'])),
        tooltip=['host_year', 'review_scores_rating', 'host_is_superhost'],
        opacity=alt.condition(highlight, alt.value(1), alt.value(0.2))
    ).add_params(
        highlight
    ).properties(
        width=900,
        height=400,
        title='Review Scores by Host Year and Superhost Status'
    )

    st.altair_chart(strip_chart, use_container_width=True)
