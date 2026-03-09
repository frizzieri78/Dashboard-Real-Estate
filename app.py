import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Real Estate Portfolio Steering",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA GENERATION (MOCK DATA)
# -----------------------------------------------------------------------------
@st.cache_data
def generate_mock_data(n_rows=50):
    """Generates mock data if Excel files are not present."""
    
    regions = ['EMEA', 'AMER', 'APAC']
    countries = {
        'EMEA': ['UK', 'Germany', 'France', 'Netherlands'],
        'AMER': ['USA', 'Canada', 'Brazil'],
        'APAC': ['Singapore', 'Japan', 'Australia', 'India']
    }
    cities = {
        'UK': ['London', 'Manchester'], 'Germany': ['Berlin', 'Munich'],
        'France': ['Paris', 'Lyon'], 'Netherlands': ['Amsterdam'],
        'USA': ['New York', 'San Francisco', 'Austin', 'Chicago'],
        'Canada': ['Toronto', 'Vancouver'], 'Brazil': ['Sao Paulo'],
        'Singapore': ['Singapore'], 'Japan': ['Tokyo'],
        'Australia': ['Sydney', 'Melbourne'], 'India': ['Bangalore', 'Mumbai']
    }
    
    data_details = []
    data_finance = []
    
    for i in range(n_rows):
        loc_id = f"LOC-{1000+i}"
        region = np.random.choice(regions)
        country = np.random.choice(countries[region])
        city = np.random.choice(cities[country])
        
        # Physical Data
        sqm = np.random.randint(500, 5000)
        workstations = int(sqm / np.random.uniform(8, 15)) # Approx 10-12 sqm per desk
        headcount = int(workstations * np.random.uniform(0.6, 1.1)) # 60% to 110% utilization
        
        # Dates
        today = datetime.now()
        days_offset = np.random.randint(-365, 365*5)
        expiry_date = today + timedelta(days=days_offset)
        
        data_details.append({
            "Location_ID": loc_id,
            "Region": region,
            "Country": country,
            "City": city,
            "Address": f"{np.random.randint(1,999)} {city} Blvd",
            "Property_Type": np.random.choice(['Office', 'Warehouse', 'Retail'], p=[0.8, 0.1, 0.1]),
            "Square_Meters": sqm,
            "Workstations": workstations,
            "Current_Headcount": headcount,
            "Lease_Expiry_Date": expiry_date,
            # Adding Lat/Lon for Map visualization (Mock coordinates)
            "lat": np.random.uniform(-50, 60), 
            "lon": np.random.uniform(-120, 140)
        })
        
        # Financial Data
        annual_budget = sqm * np.random.uniform(300, 800) # Cost per sqm
        # YTD is roughly proportional to how far we are in the year (assuming 50% for mock)
        actual_ytd = annual_budget * np.random.uniform(0.4, 0.6) 
        
        # Cost Breakdown
        rent = actual_ytd * 0.6
        maint = actual_ytd * 0.15
        util = actual_ytd * 0.15
        clean = actual_ytd * 0.1
        
        data_finance.append({
            "Location_ID": loc_id,
            "Annual_Budget": round(annual_budget, 2),
            "Actual_YTD_Costs": round(actual_ytd, 2),
            "Rent_Cost": round(rent, 2),
            "Maintenance_Cost": round(maint, 2),
            "Utilities_Cost": round(util, 2),
            "Cleaning_Cost": round(clean, 2)
        })
        
    df_details = pd.DataFrame(data_details)
    df_finance = pd.DataFrame(data_finance)
    
    return df_details, df_finance

# -----------------------------------------------------------------------------
# 3. DATA INGESTION & MERGING
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    """
    Attempts to load from Excel. Falls back to mock data if files are missing.
    Returns a merged DataFrame.
    """
    try:
        df_details = pd.read_excel("Portfolio_Details.xlsx")
        df_finance = pd.read_excel("Financial_Budget.xlsx")
        st.toast("Data loaded successfully from Excel files!", icon="📂")
    except FileNotFoundError:
        st.warning("Excel files not found. Generating Mock Data for demonstration.", icon="⚠️")
        df_details, df_finance = generate_mock_data()
    except Exception as e:
        st.error(f"An error occurred loading data: {e}")
        return pd.DataFrame()

    # Merge Data
    df_merged = pd.merge(df_details, df_finance, on="Location_ID", how="inner")
    
    # Ensure Date format
    df_merged["Lease_Expiry_Date"] = pd.to_datetime(df_merged["Lease_Expiry_Date"])
    
    # Calculated Fields for Global Use
    df_merged["Utilization_Rate"] = (df_merged["Current_Headcount"] / df_merged["Workstations"]) * 100
    df_merged["Budget_Variance"] = df_merged["Annual_Budget"] - df_merged["Actual_YTD_Costs"]
    df_merged["Cost_Per_SQM"] = df_merged["Actual_YTD_Costs"] / df_merged["Square_Meters"]
    
    return df_merged

# Load the data
df_master = load_data()

if df_master.empty:
    st.stop()

# -----------------------------------------------------------------------------
# 4. SIDEBAR NAVIGATION & FILTERS
# -----------------------------------------------------------------------------
st.sidebar.title("🏢 Portfolio Steering")

# Navigation
page = st.sidebar.radio("Go to", [
    "Executive Overview", 
    "Financial Performance", 
    "Space Utilization", 
    "Lease Management"
])

st.sidebar.markdown("---")
st.sidebar.header("Global Filters")

# Filters
selected_region = st.sidebar.multiselect(
    "Region", options=df_master["Region"].unique(), default=df_master["Region"].unique()
)

# Filter Country based on Region selection
available_countries = df_master[df_master["Region"].isin(selected_region)]["Country"].unique()
selected_country = st.sidebar.multiselect(
    "Country", options=available_countries, default=available_countries
)

# Filter Property Type
selected_type = st.sidebar.multiselect(
    "Property Type", options=df_master["Property_Type"].unique(), default=df_master["Property_Type"].unique()
)

# Apply Filters
df_filtered = df_master[
    (df_master["Region"].isin(selected_region)) &
    (df_master["Country"].isin(selected_country)) &
    (df_master["Property_Type"].isin(selected_type))
]

st.sidebar.markdown("---")
st.sidebar.caption(f"Total Locations: {len(df_filtered)}")

# -----------------------------------------------------------------------------
# 5. PAGE IMPLEMENTATIONS
# -----------------------------------------------------------------------------

# --- PAGE 1: EXECUTIVE OVERVIEW ---
if page == "Executive Overview":
    st.title("🌍 Executive Overview")
    
    # Top Row KPIs
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_sqm = df_filtered["Square_Meters"].sum()
    total_workstations = df_filtered["Workstations"].sum()
    total_headcount = df_filtered["Current_Headcount"].sum()
    
    # Avoid division by zero
    global_util = (total_headcount / total_workstations * 100) if total_workstations > 0 else 0
    
    total_budget = df_filtered["Annual_Budget"].sum()
    total_actual = df_filtered["Actual_YTD_Costs"].sum()
    
    kpi1.metric("Total SQM", f"{total_sqm:,.0f}")
    kpi2.metric("Workstations", f"{total_workstations:,.0f}")
    kpi3.metric("Global Headcount", f"{total_headcount:,.0f}")
    kpi4.metric("Blended Utilization", f"{global_util:.1f}%")
    kpi5.metric("Budget vs Actual", f"${total_actual:,.0f}", delta=f"${total_budget - total_actual:,.0f} Remaining")

    st.markdown("---")
    
    # Visuals Row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Global Portfolio Map")
        # Note: In a real scenario, you need valid Lat/Lon or ISO codes. 
        # Mock data includes random Lat/Lon for demo purposes.
        if 'lat' in df_filtered.columns:
            fig_map = px.scatter_geo(
                df_filtered,
                lat="lat", lon="lon",
                size="Square_Meters",
                color="Budget_Variance",
                hover_name="City",
                hover_data=["Region", "Annual_Budget"],
                color_continuous_scale="RdYlGn",
                projection="natural earth",
                title="Portfolio Distribution (Size=SQM, Color=Budget Variance)"
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Lat/Lon data missing for map.")

    with col2:
        st.subheader("SQM by Region")
        fig_donut = px.pie(
            df_filtered, 
            names="Region", 
            values="Square_Meters", 
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_donut, use_container_width=True)

# --- PAGE 2: FINANCIAL PERFORMANCE ---
elif page == "Financial Performance":
    st.title("💰 Financial Performance")
    
    # KPIs
    kpi1, kpi2 = st.columns(2)
    
    avg_cost_sqm = df_filtered["Actual_YTD_Costs"].sum() / df_filtered["Square_Meters"].sum() if df_filtered["Square_Meters"].sum() > 0 else 0
    avg_cost_desk = df_filtered["Actual_YTD_Costs"].sum() / df_filtered["Workstations"].sum() if df_filtered["Workstations"].sum() > 0 else 0
    
    kpi1.metric("Avg Cost per SQM (YTD)", f"${avg_cost_sqm:,.2f}")
    kpi2.metric("Avg Cost per Workstation (YTD)", f"${avg_cost_desk:,.2f}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Budget vs Actuals (Top 10 Cities)")
        # Group by City
        city_fin = df_filtered.groupby("City")[["Annual_Budget", "Actual_YTD_Costs"]].sum().reset_index()
        city_fin = city_fin.sort_values("Annual_Budget", ascending=False).head(10)
        
        # Melt for side-by-side bar chart
        city_fin_melt = city_fin.melt(id_vars="City", var_name="Type", value_name="Amount")
        
        fig_bar = px.bar(
            city_fin_melt, 
            x="City", 
            y="Amount", 
            color="Type", 
            barmode="group",
            color_discrete_map={"Annual_Budget": "#1f77b4", "Actual_YTD_Costs": "#ff7f0e"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col2:
        st.subheader("Cost Breakdown by Region")
        # Melt cost columns
        cost_cols = ["Rent_Cost", "Maintenance_Cost", "Utilities_Cost", "Cleaning_Cost"]
        region_costs = df_filtered.groupby("Region")[cost_cols].sum().reset_index()
        region_melt = region_costs.melt(id_vars="Region", var_name="Cost_Type", value_name="Amount")
        
        fig_stack = px.bar(
            region_melt, 
            x="Region", 
            y="Amount", 
            color="Cost_Type", 
            title="Operational Expenses Breakdown"
        )
        st.plotly_chart(fig_stack, use_container_width=True)
        
    st.subheader("🚨 Over-Budget Locations")
    over_budget_df = df_filtered[df_filtered["Actual_YTD_Costs"] > df_filtered["Annual_Budget"]].copy()
    over_budget_df["Variance"] = over_budget_df["Actual_YTD_Costs"] - over_budget_df["Annual_Budget"]
    
    display_cols = ["Location_ID", "City", "Region", "Annual_Budget", "Actual_YTD_Costs", "Variance"]
    
    st.dataframe(
        over_budget_df[display_cols].style.format({
            "Annual_Budget": "${:,.0f}",
            "Actual_YTD_Costs": "${:,.0f}",
            "Variance": "${:,.0f}"
        }).background_gradient(subset=["Variance"], cmap="Reds"),
        use_container_width=True
    )

# --- PAGE 3: SPACE UTILIZATION ---
elif page == "Space Utilization":
    st.title("🏢 Space Utilization & Efficiency")
    
    kpi1, kpi2 = st.columns(2)
    
    avg_density = df_filtered["Square_Meters"].sum() / df_filtered["Workstations"].sum() if df_filtered["Workstations"].sum() > 0 else 0
    vacant_desks = df_filtered["Workstations"].sum() - df_filtered["Current_Headcount"].sum()
    
    kpi1.metric("Avg Density (SQM/Desk)", f"{avg_density:.1f} m²")
    kpi2.metric("Total Vacant Desks", f"{vacant_desks:,.0f}")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Capacity vs Demand (Headcount)")
        
        fig_scatter = px.scatter(
            df_filtered,
            x="Workstations",
            y="Current_Headcount",
            color="Region",
            size="Square_Meters",
            hover_data=["City", "Utilization_Rate"],
            title="Workstations vs Headcount (Line = 100% Utilization)"
        )
        
        # Add 1:1 Line
        max_val = max(df_filtered["Workstations"].max(), df_filtered["Current_Headcount"].max())
        fig_scatter.add_shape(
            type="line", line=dict(dash="dash", color="gray"),
            x0=0, y0=0, x1=max_val, y1=max_val
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with col2:
        st.subheader("Utilization by Country")
        country_util = df_filtered.groupby("Country")[["Workstations", "Current_Headcount"]].sum().reset_index()
        country_util["Rate"] = (country_util["Current_Headcount"] / country_util["Workstations"]) * 100
        
        fig_util_bar = px.bar(
            country_util,
            x="Country",
            y="Rate",
            color="Rate",
            color_continuous_scale="RdYlGn",
            range_y=[0, 120],
            title="Avg Utilization Rate (%)"
        )
        fig_util_bar.add_hline(y=100, line_dash="dot", annotation_text="Max Capacity")
        st.plotly_chart(fig_util_bar, use_container_width=True)

# --- PAGE 4: LEASE MANAGEMENT ---
elif page == "Lease Management":
    st.title("📅 Lease Management & Risk")
    
    st.info("Visualizing lease expiries to aid renewal or exit strategies.")
    
    # Timeline
    st.subheader("Lease Expiry Timeline")
    
    # Sort by date for better visualization
    df_sorted = df_filtered.sort_values("Lease_Expiry_Date")
    
    fig_timeline = px.timeline(
        df_sorted,
        x_start="Lease_Expiry_Date",
        x_end=df_sorted["Lease_Expiry_Date"] + pd.to_timedelta(30, unit='D'), # Artificial width for visibility
        y="City",
        color="Region",
        hover_data=["Address", "Lease_Expiry_Date"],
        title="Lease Expiry Dates by City"
    )
    # Fix axis to show dates properly
    fig_timeline.update_yaxes(autorange="reversed") 
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Urgent Expiries Table
    st.subheader("⚠️ Critical Actions: Expiries in Next 18 Months")
    
    today = pd.Timestamp.now()
    cutoff_date = today + pd.DateOffset(months=18)
    
    urgent_leases = df_filtered[
        (df_filtered["Lease_Expiry_Date"] > today) & 
        (df_filtered["Lease_Expiry_Date"] <= cutoff_date)
    ].sort_values("Lease_Expiry_Date")
    
    urgent_leases["Days_Remaining"] = (urgent_leases["Lease_Expiry_Date"] - today).dt.days
    
    st.dataframe(
        urgent_leases[["City", "Address", "Region", "Lease_Expiry_Date", "Days_Remaining"]].style.format({
            "Lease_Expiry_Date": "{:%Y-%m-%d}"
        }),
        use_container_width=True
    )
