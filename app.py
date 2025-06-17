import pandas as pd
import numpy as np
import streamlit as st
import altair as alt
import matplotlib.pyplot as plt
import circlify
from io import BytesIO
from matplotlib import cm  # ✅ this one!
from matplotlib.colors import to_hex



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
df["Upload To Hub Date"] = pd.to_datetime(df["Upload To Hub Date"], errors="coerce")
df = df.dropna(subset=["Upload To Hub Date", "Type"])

# --- Sidebar: selection ---
unique_types = df["Type"].unique().tolist()
selected_type = st.selectbox("Highlight a Model Type", ["All"] + unique_types)

# --- Group by count (number of models per type)
grouped = df.groupby("Type", as_index=False).size().rename(columns={"size": "Count"})
grouped = grouped.sort_values("Count", ascending=False).reset_index(drop=True)

values = grouped["Count"].tolist()
type_list = grouped["Type"].tolist()

# --- Color mapping
cmap = cm.get_cmap("tab20", len(type_list))
type_colors = {t: to_hex(cmap(i)) for i, t in enumerate(type_list)}

# --- Circlify layout (area ∝ count)
circles = circlify.circlify(
    values,
    show_enclosure=False,
    target_enclosure=circlify.Circle(x=0, y=0, r=1)
)

# --- Bubble chart (matplotlib)
fig, ax = plt.subplots(figsize=(10, 10))
ax.axis('off')
lim = max(max(abs(c.x) + c.r, abs(c.y) + c.r) for c in circles)
plt.xlim(-lim, lim)
plt.ylim(-lim, lim)

for circle, row in zip(circles, grouped.itertuples()):
    x, y, r = circle.x, circle.y, circle.r
    label = f"{row.Type}\n{row.Count}"
    facecolor = type_colors[row.Type]
    edgecolor = 'black' if selected_type in ["All", row.Type] else 'gray'
    alpha = 1.0 if selected_type in ["All", row.Type] else 0.1
    ax.add_patch(plt.Circle((x, y), r, alpha=alpha, color=facecolor, ec=edgecolor, lw=2))
    if selected_type in ["All", row.Type]:
        ax.text(x, y, label, ha='center', va='center', fontsize=10)

buf = BytesIO()
plt.savefig(buf, format="png", bbox_inches='tight', dpi=200)
buf.seek(0)
st.image(buf, caption="Packed Bubble Chart (Model Count per Type)", use_column_width=True)

# --- Time series chart (still uses CO₂)
df["Month"] = df["Upload To Hub Date"].dt.to_period("M").dt.to_timestamp()
df["CO₂ cost (kg)"] = pd.to_numeric(df["CO₂ cost (kg)"], errors="coerce")
df = df.dropna(subset=["CO₂ cost (kg)"])
monthly = df.groupby(["Month", "Type"])["CO₂ cost (kg)"].sum().reset_index()
monthly["Cumulative CO₂"] = monthly.sort_values("Month").groupby("Type")["CO₂ cost (kg)"].cumsum()

if selected_type != "All":
    monthly = monthly[monthly["Type"] == selected_type]

color_scale = alt.Scale(domain=type_list, range=[type_colors[t] for t in type_list])
zoom = alt.selection_interval(bind="scales")

area_chart = alt.Chart(monthly).mark_area(interpolate="monotone").encode(
    x=alt.X("Month:T", title="Month", axis=alt.Axis(format="%b %Y")),
    y=alt.Y("Cumulative CO₂:Q", title="Cumulative CO₂ Emissions (kg)"),
    color=alt.Color("Type:N", scale=color_scale, legend=None),
    tooltip=[
        alt.Tooltip("Month:T", title="Month", format="%B %Y"),
        alt.Tooltip("Type:N"),
        alt.Tooltip("Cumulative CO₂:Q", format=",.0f")
    ]
).add_params(zoom).properties(
    title="Cumulative CO₂ Emissions Over Time",
    width=800,
    height=400
)

st.altair_chart(area_chart, use_container_width=True)



st.markdown("### Model Type Key")
st.markdown("Learn about the types of models included in this dashboard:")

model_type_explanations = {
    "🟢 Pretrained Model": """
**Pretrained Model**
- Newly trained from scratch using masked or causal language modeling.
- Trained on large corpora like Common Crawl, Wikipedia, books, etc.
- Forms the backbone of more advanced fine-tuned or merged models.
""",
    "🟩 Continuously Pretrained Model": """
**Continuously Pretrained Model**
- Built from existing pretrained models.
- Further trained on more recent or curated corpora.
- May include instruction tuning, domain-specific datasets, or chat data.
""",
    "🔶 Fine-Tuned on Domain-Specific Datasets": """
**Fine-Tuned Model**
- Pretrained models adapted to specific domains (e.g., medical, legal).
- Fine-tuned on additional data without modifying architecture.
- Usually boosts performance on target tasks at the cost of generality.
""",
    "💬 Chat Models (RLHF, DPO, IFT…)": """
**Chat Models**
- Trained using **Instruction-Following Tuning (IFT)**, **Reinforcement Learning with Human Feedback (RLHF)**, or **Direct Preference Optimization (DPO)**.
- Tailored for natural conversation, task following, and user preference alignment.
- Can output safer, more controllable text in interactive settings.
""",
    "🤝 Base Merges and MoErges": """
**Merged Models (Base Merges / MoErges)**
- Created by combining weights from multiple base or fine-tuned models.
- May use **merge techniques** like addition, interpolation, or LoRA stacking.
- Usually *not* trained further after merging.
- Useful for combining capabilities or styles.
""",
    "🌸 Multimodal Models": """
**Multimodal Models**
- Can process inputs from different modalities like **text**, **images**, **audio**, or **video**.
- Examples include image captioning, vision-language models, and audio reasoning.
- Represent the next frontier in general AI capabilities.
"""
}

evaluation_summary = {
    "IFEval": {
        "Description": """
**IFEval** checks whether a model can follow explicit formatting instructions.

- Focuses on format adherence, not correctness  
- Includes tasks like:  
  - *“Include the keyword X”*  
  - *“Respond using format Y”*  
- Useful for evaluating models as tools in pipeline-style workflows
"""
    },
    "BBH": {
        "Description": """
**BBH** (Beyond the Imitation Game Benchmark) is a challenging reasoning benchmark.

- Covers 23 BigBench tasks including:  
  - Logic puzzles  
  - Math word problems  
  - Symbolic reasoning  
- Highly correlated with human preference judgments
"""
    },
    "MATH Lvl 5": {
        "Description": """
**MATH Lvl 5** consists of high school math competition problems.

- Includes problems from contests like AMC and AIME  
- Requires exact formatting (LaTeX, Asymptote)  
- Emphasizes correctness, clarity, and structured output
"""
    },
    "GPQA": {
        "Description": """
**GPQA** is a graduate-level STEM question set vetted by domain experts.

- Topics include:  
  - Biology  
  - Chemistry  
  - Physics  
- Designed to avoid test-set contamination  
- Emphasizes true conceptual depth over pattern matching
"""
    },
    "MuSR": {
        "Description": """
**MuSR** (Multistep Structured Reasoning) features long-context challenges.

- Includes:  
  - Logic puzzles  
  - Mystery reasoning  
  - Logistics chains  
- Tests the model's ability to track dependencies over long input
"""
    },
    "MMLU-Pro": {
        "Description": """
**MMLU-Pro** is a professional-grade variant of MMLU.

- Differences from original MMLU:  
  - 10 multiple-choice options (harder)  
  - Expert-reviewed and cleaned  
  - Harder distractors and fewer flaws  
- Emphasizes nuanced world knowledge and test-taking skill
"""
    }
}

# Outer dropdown
with st.expander("📘 Learn About Model Types and Evaluation Benchmarks"):
    st.markdown("#### Model Types")
    for label, description in model_type_explanations.items():
        with st.expander(label):
            st.markdown(description)

    st.markdown("#### Evaluation Benchmarks")
    for eval_name, content in evaluation_summary.items():
        with st.expander(eval_name):
            st.markdown(content["Description"])
