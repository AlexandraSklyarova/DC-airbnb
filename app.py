import streamlit as st
import pandas as pd
import altair as alt

# Set page layout to wide
st.set_page_config(layout="wide")

# --- Load and clean data ---
df = pd.read_csv("listings.csv")

# --- Common cleaning ---
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

# Extract year from host_since
df['host_year'] = df['host_since'].dt.year

# Title
st.title("\U0001F3E0 DC Airbnb Data Explorer")

# Sidebar controls
st.sidebar.header("Filters")
top_n = st.sidebar.slider("Select number of neighborhoods to display:", min_value=5, max_value=100, value=30)
selected_neighborhoods = df['host_neighbourhood'].value_counts().nlargest(top_n).index.tolist()
df = df[df['host_neighbourhood'].isin(selected_neighborhoods)]

# =======================
# Layout: Two columns
# =======================
col1, col2 = st.columns([1.2, 1.0])

with col1:
    st.header("\U0001F4CA Revenue by Neighborhood")
    metric = st.selectbox("Select revenue metric:", options=["Average Revenue", "Total Revenue"])
    agg_func = 'mean' if metric == "Average Revenue" else 'sum'
    agg_col = 'avg_estimated_revenue' if metric == "Average Revenue" else 'total_estimated_revenue'

    df_grouped = df.groupby('host_neighbourhood', as_index=False).agg(
        {'estimated_revenue_365d': agg_func}
    ).rename(columns={'estimated_revenue_365d': agg_col})

    bar_chart = alt.Chart(df_grouped).mark_bar().encode(
        x=alt.X('host_neighbourhood:N', sort='-y', title='Host Neighborhood'),
        y=alt.Y(f'{agg_col}:Q', title=f'{metric} (365d)'),
        tooltip=['host_neighbourhood', f'{agg_col}']
    ).properties(
        width=900,
        height=600,
        title=f'Top {top_n} Neighborhoods by Listing Count: {metric}'
    ).configure_axisX(labelAngle=-45)

    st.altair_chart(bar_chart, use_container_width=True)

    st.markdown("###")
    st.header("\U0001F6CC Room Types: Beds, Baths, Accommodates")

    selected_room_types = st.multiselect("Select Room Types:", options=df['room_type'].unique(), default=df['room_type'].unique())
    df_filtered = df[df['room_type'].isin(selected_room_types)]

    bubble_chart = alt.Chart(df_filtered).mark_circle().encode(
        x=alt.X('room_type:N', title='Room Type'),
        y=alt.Y('accommodates:Q', title='Accommodates'),
        size=alt.Size('beds:Q', title='Beds'),
        color=alt.Color('bathrooms:Q', title='Bathrooms', scale=alt.Scale(scheme='blues')),
        tooltip=['room_type', 'accommodates', 'beds', 'bathrooms']
    ).properties(
        width=900,
        height=600,
        title='Beds, Bathrooms, Room Type vs Accommodates'
    ).interactive()

    st.altair_chart(bubble_chart, use_container_width=True)

with col2:
    st.header("\U0001F4B5 Price vs Number of Listings")

    df_price_plot = df[df['price'] < 1000]  # Filter for reasonable prices
    df_price_plot = df_price_plot.groupby(['price', 'host_neighbourhood']).size().reset_index(name='listing_count')

    highlight = alt.selection_point(fields=['host_neighbourhood'], bind='legend', name="Neighborhood")

    scatter_chart = alt.Chart(df_price_plot).mark_circle(size=60).encode(
        x=alt.X('price:Q', title='Price (USD)'),
        y=alt.Y('listing_count:Q', title='Number of Listings'),
        color=alt.Color('host_neighbourhood:N', title='Neighborhood'),
        tooltip=['host_neighbourhood', 'price', 'listing_count'],
        opacity=alt.condition(highlight, alt.value(1), alt.value(0.15))
    ).add_params(
        highlight
    ).properties(
        width=900,
        height=600,
        title='Listings by Price and Neighborhood'
    ).interactive()

    st.altair_chart(scatter_chart, use_container_width=True)

    st.markdown("###")
    st.header("\U0001F4CB Review Scores by Host Year")

    df_strip = df[df['review_scores_rating'].between(0, 100)]

    strip_chart = alt.Chart(df_strip).mark_tick(thickness=2, size=12).encode(
        x=alt.X('host_year:O', title='Host Since (Year)'),
        y=alt.Y('review_scores_rating:Q', title='Review Score Rating'),
        color=alt.Color('host_is_superhost:N', title='Superhost',
                        scale=alt.Scale(domain=['t', 'f'], range=['lightgreen', 'lightcoral'])),
        tooltip=['host_year', 'review_scores_rating', 'host_is_superhost'],
        opacity=alt.condition(highlight, alt.value(1), alt.value(0.1))
    ).add_params(
        highlight
    ).properties(
        width=900,
        height=500,
        title='Review Scores by Host Year and Superhost Status'
    ).interactive()

    st.altair_chart(strip_chart, use_container_width=True)
