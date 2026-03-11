import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from typing import Dict

# ------------------------------------------
# Page Configuration
# ------------------------------------------
st.set_page_config(page_title="DataCo Supply Chain", page_icon="📦", layout="wide")

# ------------------------------------------
# UI ENHANCEMENTS: CUSTOM CSS
# ------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e6ed;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0px 8px 15px rgba(0, 0, 0, 0.08);
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e6ed;
    }
    h1, h2, h3 { color: #1e293b; font-family: 'Inter', sans-serif; }
    .chart-desc { color: #64748b; font-size: 0.85rem; margin-top: -10px; margin-bottom: 15px; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Data Loading (Optimized)
# ------------------------------------------
@st.cache_data(show_spinner="Optimizing dataset...")
def load_and_clean_data():
    # Pandas is smart enough to open zip files automatically!
    df = pd.read_csv('DataCoSupplyChainDataset.zip', encoding='latin1')
    df.columns = [col.strip().lower().replace(' ', '_').replace('(', '').replace(')', '') for col in df.columns]
    
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
st.sidebar.markdown("## 🧭 Graph Navigation")
graph_view = st.sidebar.radio("Select a deep-dive view:", ["Operational Logistics", "Risk & Threat Analysis"], label_visibility="collapsed")

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

# Chart layout config to remove visual clutter
chart_layout = dict(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

# ==========================================
# PERSISTENT TOP SECTION: EXECUTIVE OVERVIEW 
# ==========================================
st.title("📦 DataCo Global Executive Dashboard")
st.markdown("<p style='color: #64748b; font-size: 1.1rem;'>High-level scorecard and dynamic operational deep-dives.</p>", unsafe_allow_html=True)

analyzer = SupplyChainAnalyzer(df)
kpis = analyzer.get_executive_kpis(exchange_rate=rate)

col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue (RI)", f"{selected_currency} {kpis['revenue']:,.0f}")
col2.metric("Total Net Profit (KPI)", f"{selected_currency} {kpis['profit']:,.0f}")
col3.metric("Avg Profit Margin (KPI)", f"{kpis['margin']:.2f}%")
st.markdown("---") 

# ==========================================
# DYNAMIC BOTTOM SECTION: GRAPHS
# ==========================================

if graph_view == "Operational Logistics":
    st.subheader("🚚 Operational Logistics")
    st.markdown("<p style='color: #64748b; font-size: 1.0rem;'>Performance indicators tracking fulfillment efficiency and volume drivers.</p>", unsafe_allow_html=True)
    
    col_b1, col_b2 = st.columns(2)

    with col_b1:
        with st.container(border=True):
            st.markdown("#### Avg Delay by Shipping Mode")
            st.markdown("<div class='chart-desc'>Measures the average number of days orders are delayed beyond their scheduled shipping date. Higher bars indicate logistical bottlenecks in specific fulfillment tiers.</div>", unsafe_allow_html=True)
            delay_by_mode = df.groupby('shipping_mode')['shipping_delay'].mean().reset_index()
            fig_delay = px.bar(delay_by_mode, x='shipping_mode', y='shipping_delay', text_auto='.1f', color_discrete_sequence=['#3b82f6'])
            fig_delay.update_layout(**chart_layout, yaxis_title="Days Delayed", xaxis_title="")
            st.plotly_chart(fig_delay, use_container_width=True)

        with st.container(border=True):
            st.markdown("#### Top Regions by Sales Volume")
            st.markdown("<div class='chart-desc'>Highlights the geographic order regions driving the highest revenue. Use this to determine where to allocate marketing and inventory resources.</div>", unsafe_allow_html=True)
            geo_sales = df.groupby('order_region')['sales'].sum().reset_index().sort_values('sales', ascending=False).head(10)
            geo_sales['sales'] *= rate # Convert currency
            fig_geo = px.bar(geo_sales, x='sales', y='order_region', orientation='h', color_discrete_sequence=['#0ea5e9'])
            fig_geo.update_layout(**chart_layout, yaxis={'categoryorder': 'total ascending'}, xaxis_title=f"Sales ({selected_currency})", yaxis_title="")
            st.plotly_chart(fig_geo, use_container_width=True)

    with col_b2:
        with st.container(border=True):
            st.markdown("#### Revenue Breakdown by Category")
            st.markdown("<div class='chart-desc'>Displays the proportion of total sales generated by the top 10 product categories. Helps identify over-reliance on specific inventory types.</div>", unsafe_allow_html=True)
            top_cats = df.groupby('category_name')['sales'].sum().reset_index().sort_values('sales', ascending=False).head(10)
            fig_cats = px.pie(top_cats, names='category_name', values='sales', hole=0.5)
            fig_cats.update_layout(**chart_layout)
            fig_cats.update_traces(textposition='inside', textinfo='percent+label', showlegend=False)
            st.plotly_chart(fig_cats, use_container_width=True)


elif graph_view == "Risk & Threat Analysis":
    st.subheader("⚠️ Risk & Threat Analysis")
    st.markdown("<p style='color: #64748b; font-size: 1.0rem;'>Key Risk Indicators (KRIs) serving as early warning signals for operational friction.</p>", unsafe_allow_html=True)
    
    kris = analyzer.get_risk_kpis()
    kri1, kri2, kri3 = st.columns(3)
    kri1.metric("Overall Late Delivery Rate", f"{kris['late_rate']:.1f}%")
    kri2.metric("Overall Fraud Exposure Rate", f"{kris['fraud_rate']:.2f}%")
    kri3.metric("Overall Cancellation Rate", f"{kris['cancel_rate']:.1f}%")
    st.write("")

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        with st.container(border=True):
            st.markdown("#### Late Delivery Risk Trend")
            st.markdown("<div class='chart-desc'>Tracks the percentage of orders at risk of late delivery over time. Upward trends require immediate investigation into warehouse operations.</div>", unsafe_allow_html=True)
            risk_over_time = df.groupby('year_month')['late_delivery_risk'].mean().reset_index()
            risk_over_time['late_delivery_risk'] *= 100
            fig_risk = px.line(risk_over_time, x='year_month', y='late_delivery_risk', markers=True)
            fig_risk.update_traces(line_color='#ef4444', marker=dict(size=8))
            fig_risk.update_layout(**chart_layout, xaxis_title="Month", yaxis_title="Late Risk (%)", yaxis_gridcolor='#e0e6ed')
            st.plotly_chart(fig_risk, use_container_width=True)

    with col_c2:
        with st.container(border=True):
            st.markdown("#### Fraud Exposure by Region")
            st.markdown("<div class='chart-desc'>Displays the percentage of transactions flagged as 'Suspected Fraud' within the top 10 most affected regions. Used to tighten regional payment security.</div>", unsafe_allow_html=True)
            fraud_by_region = df.groupby('order_region')['is_fraud'].mean().reset_index()
            fraud_by_region['is_fraud'] *= 100
            fraud_by_region = fraud_by_region.sort_values('is_fraud', ascending=False).head(10)
            fig_fraud = px.bar(fraud_by_region, x='order_region', y='is_fraud', text_auto='.2f', color_discrete_sequence=['#f97316'])
            fig_fraud.update_layout(**chart_layout, xaxis_title="", yaxis_title="Fraud Rate (%)", yaxis_gridcolor='#e0e6ed')
            fig_fraud.update_xaxes(tickangle=-45)
            st.plotly_chart(fig_fraud, use_container_width=True)
