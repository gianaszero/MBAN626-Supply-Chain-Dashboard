import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import zipfile
from typing import Dict

# ------------------------------------------
# Page Configuration
# ------------------------------------------
st.set_page_config(page_title="DataCo Supply Chain", page_icon="📦", layout="wide")

# ------------------------------------------
# UI ENHANCEMENTS: GLASSMORPHISM CSS
# ------------------------------------------
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    h1, h2, h3, h4, h5 { 
        font-family: 'Inter', sans-serif; 
        color: #0f172a;
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    /* 1. App Background: Subtle Animated Mesh Gradient */
    .stApp { 
        background: linear-gradient(-45deg, #e0e7ff, #f3e8ff, #dbeafe, #ede9fe);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }

    @keyframes gradient {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 2. Style the Sidebar (Glass Panel) */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.5) !important;
    }

    /* 3. Style Metric Containers (Glass Cards) */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.1);
        border: 1px solid rgba(255, 255, 255, 1);
    }
    
    div[data-testid="metric-container"] > div { color: #1e293b !important; }
    div[data-testid="metric-container"] p { color: #475569; font-weight: 500; }

    /* 4. Streamlit Chart Containers (Glass Cards) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.55) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.7) !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07) !important;
        padding: 1.5rem 1.5rem 0.5rem 1.5rem !important;
    /* 5. Custom Sidebar Navigation Buttons (Anchors) */
    .nav-glass-btn {
        display: block;
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 8px;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.5);
        color: #1e293b !important;
        text-decoration: none !important;
        font-weight: 500;
        text-align: center;
        backdrop-filter: blur(5px);
    }
    .nav-glass-btn:hover {
        background: rgba(255, 255, 255, 0.85);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        color: #0f172a !important;
    }

    /* Anchor Target Spacing */
    .anchor-target {
        display: block;
        position: relative;
        top: -20px;
        visibility: hidden;
    }
    
    /* Dataframes - glass effect */
    [data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.4);
        border-radius: 12px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Data Preparation and Loading (Optimized)
# ------------------------------------------
@st.cache_data(show_spinner="Extracting and Optimizing dataset...")
def load_and_clean_data():
    import zipfile
    import os
    
    try:
        # Open the zip file
        with zipfile.ZipFile('DataCoSupplyChainDataset.zip', 'r') as z:
            # Find the actual CSV, strictly ignoring Mac's hidden "ghost" files
            valid_csvs = [
                name for name in z.namelist() 
                if name.endswith('.csv') and '__MACOSX' not in name and not name.split('/')[-1].startswith('._')
            ]
            target_csv = valid_csvs[0]
            
            # Extract it to the Streamlit Cloud server safely
            z.extract(target_csv)
            
        # Read the physically extracted file (bypasses all pandas file-handling errors)
        df = pd.read_csv(target_csv, encoding='latin1')
        
    except Exception as e:
        st.error(f"Error reading file: {e}")

    # Drop heavy unused columns
    cols_to_drop = ['product_description', 'customer_password', 'customer_email', 'product_image', 'customer_fname', 'customer_lname', 'customer_street', 'customer_zipcode', 'order_zipcode']
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns])
    
    # Downcast categorical data to save memory
    for col in ['market', 'order_region', 'shipping_mode', 'category_name', 'delivery_status', 'order_status']:
        if col in df.columns: df[col] = df[col].astype('category')
            
    df['order_date_dateorders'] = pd.to_datetime(df['order_date_dateorders'])
    df['year_month'] = df['order_date_dateorders'].dt.to_period('M').astype(str)
    
    # Feature Engineering
    df['shipping_delay'] = df['days_for_shipping_real'] - df['days_for_shipment_scheduled']
    df['is_fraud'] = (df['order_status'] == 'SUSPECTED_FRAUD').astype(int)
    df['is_canceled'] = (df['order_status'] == 'CANCELED').astype(int)
    return df

df = load_and_clean_data()

# ------------------------------------------
# SCALING FUNCTION
# ------------------------------------------
def apply_feature_scaling(df_input: pd.DataFrame, columns_to_scale: list):
    """
    Applies Min-Max Scaling to normalize features between 0 and 1.
    Formula: (x - min) / (max - min)
    """
    df_scaled = df_input.copy()
    for col in columns_to_scale:
        if col in df_scaled.columns:
            col_min = df_scaled[col].min()
            col_max = df_scaled[col].max()
            # Avoid division by zero
            if col_max - col_min != 0:
                df_scaled[f'{col}_scaled'] = (df_scaled[col] - col_min) / (col_max - col_min)
    return df_scaled


# ------------------------------------------
# Business Logic Classes
# ------------------------------------------
class SupplyChainAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.total_orders = len(data)

    def get_executive_kpis(self, exchange_rate: float = 1.0) -> Dict[str, float]:
        if self.total_orders == 0: return {'revenue': 0.0, 'profit': 0.0, 'margin': 0.0}
        revenue = self.data['sales'].sum() * exchange_rate
        profit = self.data['order_profit_per_order'].sum() * exchange_rate
        margin = self.data['order_item_profit_ratio'].mean() * 100
        return {'revenue': revenue, 'profit': profit, 'margin': margin}

    def get_risk_kpis(self) -> Dict[str, float]:
        if self.total_orders == 0: return {'late_rate': 0.0, 'fraud_rate': 0.0, 'cancel_rate': 0.0}
        return {
            'late_rate': (self.data['late_delivery_risk'].sum() / self.total_orders) * 100,
            'fraud_rate': (self.data['is_fraud'].sum() / self.total_orders) * 100,
            'cancel_rate': (self.data['is_canceled'].sum() / self.total_orders) * 100
        }

# ------------------------------------------
# SIDEBAR: Navigation & Controls
# ------------------------------------------
st.sidebar.markdown("## 🧭 Navigation")
st.sidebar.markdown(f"""
    <a href="#executive-overview" class="nav-glass-btn">🏠 Executive Overview</a>
    <a href="#operational-logistics" class="nav-glass-btn">🚚 Operational Logistics</a>
    <a href="#risk-threat-analysis" class="nav-glass-btn">⚠️ Risk Analysis</a>
    <a href="#statistical-profile" class="nav-glass-btn">📈 Statistical Profile</a>
    <a href="#predictive-insights" class="nav-glass-btn">🔮 Predictive Insights</a>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("## ⚙️ Global Filters")

market_options = ["All Markets"] + list(df['market'].dropna().unique())
selected_market = st.sidebar.selectbox("Select Market", market_options)
if selected_market != "All Markets": df = df[df['market'] == selected_market]

currency_options = ['USD', 'EUR', 'GBP', 'JPY']
selected_currency = st.sidebar.selectbox("Select Currency", currency_options)

def get_rate(curr):
    if curr == 'USD': return 1.0
    try: return requests.get(f"https://api.frankfurter.app/latest?from=USD&to={curr}", timeout=2).json()['rates'][curr]
    except: return 1.0
rate = get_rate(selected_currency)

# Chart layout config to remove visual clutter and match CSS
chart_layout = dict(
    margin=dict(l=20, r=20, t=30, b=20), 
    paper_bgcolor="rgba(0,0,0,0)", 
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#334155", size=12)
)

# ==========================================
# FULL DASHBOARD PAGE
# ==========================================
st.markdown('<div id="executive-overview" class="anchor-target"></div>', unsafe_allow_html=True)
st.title("📦 DataCo Global Executive Dashboard")
st.markdown("<p style='color: #64748b; font-size: 1.1rem;'>High-level scorecard and dynamic operational deep-dives.</p>", unsafe_allow_html=True)

analyzer = SupplyChainAnalyzer(df)
kpis = analyzer.get_executive_kpis(exchange_rate=rate)

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"{selected_currency} {kpis['revenue']:,.0f}")
col2.metric("Total Net Profit", f"{selected_currency} {kpis['profit']:,.0f}")
col3.metric("Avg Profit Margin", f"{kpis['margin']:.2f}%")

st.divider()

# 🚚 1. OPERATIONAL LOGISTICS
st.markdown('<div id="operational-logistics" class="anchor-target"></div>', unsafe_allow_html=True)
st.subheader("🚚 Operational Logistics")
st.markdown("<p class='chart-desc'>Performance indicators tracking fulfillment efficiency and volume drivers.</p>", unsafe_allow_html=True)

col_b1, col_b2 = st.columns(2)

with col_b1:
    with st.container(border=True):
        st.markdown("#### Avg Delay by Shipping Mode")
        st.markdown("<div class='chart-desc'>Measures the average number of days orders are delayed beyond their scheduled shipping date.</div>", unsafe_allow_html=True)
        delay_by_mode = df.groupby('shipping_mode')['shipping_delay'].mean().reset_index()
        fig_delay = px.bar(delay_by_mode, x='shipping_mode', y='shipping_delay', text_auto='.1f', color_discrete_sequence=['#3b82f6'])
        fig_delay.update_layout(**chart_layout, yaxis_title="Days Delayed", xaxis_title="")
        st.plotly_chart(fig_delay, use_container_width=True)

    with st.container(border=True):
        st.markdown("#### Top Regions by Sales Volume")
        st.markdown("<div class='chart-desc'>Highlights the geographic order regions driving the highest revenue.</div>", unsafe_allow_html=True)
        geo_sales = df.groupby('order_region')['sales'].sum().reset_index().sort_values('sales', ascending=False).head(10)
        geo_sales['sales'] *= rate # Convert currency
        fig_geo = px.bar(geo_sales, x='sales', y='order_region', orientation='h', color_discrete_sequence=['#0ea5e9'])
        fig_geo.update_layout(**chart_layout, yaxis={'categoryorder': 'total ascending'}, xaxis_title=f"Sales ({selected_currency})", yaxis_title="")
        st.plotly_chart(fig_geo, use_container_width=True)

with col_b2:
    with st.container(border=True):
        st.markdown("#### Revenue Breakdown by Category")
        st.markdown("<div class='chart-desc'>Displays the proportion of total sales generated by the top 10 product categories.</div>", unsafe_allow_html=True)
        top_cats = df.groupby('category_name')['sales'].sum().reset_index().sort_values('sales', ascending=False).head(10)
        fig_cats = px.pie(top_cats, names='category_name', values='sales', hole=0.5)
        fig_cats.update_layout(**chart_layout)
        fig_cats.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
        st.plotly_chart(fig_cats, use_container_width=True)

st.divider()

# ⚠️ 2. RISK & THREAT ANALYSIS
st.markdown('<div id="risk-threat-analysis" class="anchor-target"></div>', unsafe_allow_html=True)
st.subheader("⚠️ Risk & Threat Analysis")
st.markdown("<p class='chart-desc'>Key Risk Indicators (KRIs) serving as early warning signals for operational friction.</p>", unsafe_allow_html=True)

risk_data_obj = analyzer.get_risk_kpis()
kri1, kri2, kri3 = st.columns(3)
kri1.metric("Overall Late Delivery Rate", f"{risk_data_obj['late_rate']:.1f}%")
kri2.metric("Overall Fraud Exposure Rate", f"{risk_data_obj['fraud_rate']:.2f}%")
kri3.metric("Overall Cancellation Rate", f"{risk_data_obj['cancel_rate']:.1f}%")

col_c1, col_c2 = st.columns(2)
with col_c1:
    with st.container(border=True):
        st.markdown("#### Late Delivery Risk Trend")
        st.markdown("<div class='chart-desc'>Tracks the percentage of orders at risk of late delivery over time.</div>", unsafe_allow_html=True)
        risk_over_time = df.groupby('year_month')['late_delivery_risk'].mean().reset_index()
        risk_over_time['late_delivery_risk'] *= 100
        fig_risk = px.line(risk_over_time, x='year_month', y='late_delivery_risk', markers=True)
        fig_risk.update_traces(line_color='#ef4444', marker=dict(size=8))
        fig_risk.update_layout(**chart_layout, xaxis_title="Month", yaxis_title="Late Risk (%)", yaxis_gridcolor='#e0e6ed')
        st.plotly_chart(fig_risk, use_container_width=True)

with col_c2:
    with st.container(border=True):
        st.markdown("#### Fraud Exposure by Region")
        st.markdown("<div class='chart-desc'>Percentage of transactions flagged as 'Suspected Fraud' within the top 10 regions.</div>", unsafe_allow_html=True)
        fraud_by_region = df.groupby('order_region')['is_fraud'].mean().reset_index()
        fraud_by_region['is_fraud'] *= 100
        fraud_by_region = fraud_by_region.sort_values('is_fraud', ascending=False).head(10)
        fig_fraud = px.bar(fraud_by_region, x='order_region', y='is_fraud', text_auto='.2f', color_discrete_sequence=['#f97316'])
        fig_fraud.update_layout(**chart_layout, xaxis_title="", yaxis_title="Fraud Rate (%)", yaxis_gridcolor='#e0e6ed')
        fig_fraud.update_xaxes(tickangle=-45)
        st.plotly_chart(fig_fraud, use_container_width=True)

st.divider()

# 📈 3. STATISTICAL PROFILE
st.markdown('<div id="statistical-profile" class="anchor-target"></div>', unsafe_allow_html=True)
st.subheader("📈 Statistical Profile & Preprocessing")
st.markdown("<p class='chart-desc'>Analyzing data distributions and the impact of Feature Scaling.</p>", unsafe_allow_html=True)

features_list = ['sales', 'order_item_quantity', 'days_for_shipping_real', 'order_profit_per_order']
use_scaling_sidebar = st.sidebar.toggle("Apply Global Scaling Preview (Min-Max)", value=False)

plot_df_scaled = df.copy()
if use_scaling_sidebar:
    plot_df_scaled = apply_feature_scaling(df, features_list)
    features_list = [f"{f}_scaled" for f in features_list]
    st.success("Feature Scaling Applied: Variables normalized between 0 and 1.")

col_s1, col_s2 = st.columns(2)
with col_s1:
    with st.container(border=True):
        st.markdown(f"#### Distribution of {features_list[0].title()}")
        fig_hist = px.histogram(plot_df_scaled, x=features_list[0], nbins=50, color_discrete_sequence=['#636EFA'], marginal="rug")
        fig_hist.update_layout(**chart_layout)
        st.plotly_chart(fig_hist, use_container_width=True)
        
with col_s2:
    with st.container(border=True):
        st.markdown("#### Multivariate Comparison")
        fig_box = px.box(plot_df_scaled, y=features_list, title="Feature Range Comparison")
        fig_box.update_layout(**chart_layout)
        st.plotly_chart(fig_box, use_container_width=True)

st.divider()

# 🔮 4. PREDICTIVE INSIGHTS
st.markdown('<div id="predictive-insights" class="anchor-target"></div>', unsafe_allow_html=True)
st.subheader("🔮 Predictive Fraud & Delivery Risk Insights")
st.markdown("<p class='chart-desc'>Machine learning readiness view: Normalized risk scores based on shipping history.</p>", unsafe_allow_html=True)

# Calculation
scaled_pred_data = apply_feature_scaling(df, ['shipping_delay', 'late_delivery_risk'])
df['risk_score'] = (scaled_pred_data['shipping_delay_scaled'] * 0.7) + (scaled_pred_data['late_delivery_risk_scaled'] * 0.3)

avg_risk_score = df['risk_score'].mean()
high_risk_lim = 0.7
total_high_risk_count = len(df[df['risk_score'] >= high_risk_lim])

col_p1, col_p2, col_p3 = st.columns(3)
col_p1.metric("Average System Risk Score", f"{avg_risk_score:.3f}")
col_p2.metric("Critical Risk Orders", f"{total_high_risk_count:,}")
col_p3.metric("Max Recorded Risk Score", f"{df['risk_score'].max():.3f}")

col_pct1, col_pct2 = st.columns(2)
with col_pct1:
    with st.container(border=True):
        st.markdown("#### Risk Score Distribution")
        fig_r_dist = px.histogram(df, x='risk_score', nbins=40, color_discrete_sequence=['#8b5cf6'])
        fig_r_dist.update_layout(**chart_layout)
        st.plotly_chart(fig_r_dist, use_container_width=True)
        
    with st.container(border=True):
        st.markdown("#### Risk Trend Over Time")
        risk_trend_m = df.groupby('year_month')['risk_score'].mean().reset_index()
        fig_r_time = px.line(risk_trend_m, x='year_month', y='risk_score', markers=True)
        fig_r_time.update_traces(line_color='#d946ef', marker=dict(size=8))
        fig_r_time.update_layout(**chart_layout)
        st.plotly_chart(fig_r_time, use_container_width=True)

with col_pct2:
    with st.container(border=True):
        st.markdown("#### High-Risk Product Categories")
        cat_risk_m = df.groupby('category_name')['risk_score'].mean().reset_index().sort_values('risk_score', ascending=False).head(10)
        fig_c_risk = px.bar(cat_risk_m, x='risk_score', y='category_name', orientation='h', color_discrete_sequence=['#f43f5e'])
        fig_c_risk.update_layout(**chart_layout, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_c_risk, use_container_width=True)

# Data Table
st.subheader("🚨 Top 100 Highest Risk Orders")
disp_cols_f = ['order_id', 'market', 'order_region', 'category_name', 'shipping_mode', 'shipping_delay', 'risk_score']
avail_cols_f = [c for c in disp_cols_f if c in df.columns]
hr_disp = df.sort_values(by='risk_score', ascending=False)[avail_cols_f].head(100)
if 'risk_score' in hr_disp.columns: hr_disp['risk_score'] = hr_disp['risk_score'].round(4)
st.dataframe(hr_disp, use_container_width=True, hide_index=True, height=400)
st.info("**Why scale?** Without scaling, 'Sales' (max ~2000) would completely overwhelm 'Shipping Days' (max ~6) in a machine learning model. Scaling brings them to a comparable range.")
