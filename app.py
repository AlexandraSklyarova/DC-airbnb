import streamlit as st
import pandas as pd
import altair as alt

alt.data_transformers.disable_max_rows()

# Load and clean data
df = pd.read_csv("listings.csv")

# Shared Cleaning
df['price'] = df['price'].replace('[\$,]', '', regex=True).astype(float)
df['estimated_revenue_365d'] = df['price'] * df['availability_365']

# === Layout: Two Columns ===
col1, col2 = st.columns(2)

# === COLUMN 1: Revenue Bar Chart ===
with col1:
    st.header("Neighborhood Revenue")

    df_revenue = df[['host_neighbourhood', 'price', 'availability_365']].dropna()
    df_revenue = df_revenue[df_revenue['host_neighbourhood'] != ""]

    metric = st.selectbox(
        "Select revenue metric:",
        options=["Average Revenue", "Total Revenue"]
    )

    top_n = st.slider(
        "Select number of neighborhoods to display:",
        min_value=5, max_value=100, value=30
    )

    agg_func = 'mean' if metric == "Average Revenue" else 'sum'
    agg_col = 'avg_estimated_revenue' if metric == "Average Revenue" else 'total_estimated_revenue'

    top_neighborhoods = df_revenue['host_neighbourhood'].value_counts().nlargest(top_n).index
    df_top = df_revenue[df_revenue['host_neighbourhood'].isin(top_neighborhoods)]

    df_grouped = df_top.groupby('host_neighbourhood', as_index=False).agg(
        {
            'estimated_revenue_365d': agg_func
        }
    ).rename(columns={'estimated_revenue_365d': agg_col})

    chart1 = alt.Chart(df_grouped).mark_bar().encode(
        x=alt.X('host_neighbourhood:N', sort='-y', title='Host Neighborhood'),
        y=alt.Y(f'{agg_col}:Q', title=f'{metric} (365d)'),
        tooltip=['host_neighbourhood', f'{agg_col}']
    ).properties(
        width=350,
        height=400,
        title=f'Top {top_n} Neighborhoods: {metric}'
    ).configure_axisX(
        labelAngle=-45
    )

    st.altair_chart(chart1, use_container_width=True)


# === COLUMN 2: Interactive Scatter ===
with col2:
    st.header("Room Type vs Capacity")

    df_viz = df[['room_type', 'accommodates', 'bathrooms', 'beds']].dropna()
    df_viz['accommodates'] = df_viz['accommodates'].astype(int)
    df_viz['beds'] = pd.to_numeric(df_viz['beds'], errors='coerce')
    df_viz['bathrooms'] = pd.to_numeric(df_viz['bathrooms'], errors='coerce')
    df_viz = df_viz.dropna()

    room_types = st.multiselect(
        "Select Room Types:",
        options=sorted(df_viz['room_type'].unique()),
        default=sorted(df_viz['room_type'].unique())
    )

    min_accom = int(df_viz['accommodates'].min())
    max_accom = int(df_viz['accommodates'].max())
    accommodates_range = st.slider(
        "Accommodates Range:",
        min_value=min_accom,
        max_value=max_accom,
        value=(min_accom, max_accom)
    )

    df_filtered = df_viz[
        (df_viz['room_type'].isin(room_types)) &
        (df_viz['accommodates'].between(*accommodates_range))
    ]

    selection = alt.selection_multi(fields=['room_type'], bind='legend')

    chart2 = alt.Chart(df_filtered).mark_circle().encode(
        x=alt.X('room_type:N', title='Room Type'),
        y=alt.Y('accommodates:Q', title='Accommodates'),
        size=alt.Size('beds:Q', title='Beds'),
        color=alt.Color('bathrooms:Q', title='Bathrooms', scale=alt.Scale(scheme='viridis')),
        tooltip=[
            alt.Tooltip('room_type:N'),
            alt.Tooltip('accommodates:Q'),
            alt.Tooltip('beds:Q', format=".1f"),
            alt.Tooltip('bathrooms:Q', format=".1f")
        ],
        opacity=alt.condition(selection, alt.value(1), alt.value(0.1))
    ).add_selection(
        selection
    ).properties(
        width=350,
        height=400,
        title='Room Type vs Beds & Baths'
    )

    st.altair_chart(chart2, use_container_width=True)
