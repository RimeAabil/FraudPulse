import streamlit as st
import pandas as pd
import time

from helpers.data_utils import load_data
import helpers.charts as hc

st.set_page_config(page_title="FraudPulse Dashboard", page_icon="🛡️", layout="wide")

# GLOBAL STYLES & ANIMATIONS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root tokens for Light Professional Theme ── */
:root {
    --c-bg:          #F8FAFC; /* Clean off-white background */
    --c-surface:     #FFFFFF; /* White panels */
    --c-border:      #E2E8F0;
    --c-blue-dark:   #0F172A; /* For high contrast text/headers */
    --c-blue-mid:    #2563EB; /* Primary brand blue */
    --c-blue-light:  #EFF6FF;
    --c-blue-accent: #3B82F6;
    --c-red:         #EF4444; /* Alert red */
    --c-red-light:   #FEF2F2;
    --c-orange:      #F97316; /* Warning orange */
    --c-orange-light:#FFF7ED;
    --c-green:       #10B981; /* Safe green */
    --c-green-light: #ECFDF5;
    --c-gray-100:    #F1F5F9;
    --c-gray-200:    #E2E8F0;
    --c-gray-400:    #94A3B8;
    --c-gray-600:    #475569;
    --c-gray-800:    #1E293B;
    --c-text:        #0F172A;
    --c-text-muted:  #64748B;
    --radius-sm:     8px;
    --radius-md:     12px;
    --radius-lg:     16px;
    --shadow-sm:     0 1px 2px 0 rgba(15, 23, 42, 0.05);
    --shadow-md:     0 4px 6px -1px rgba(15, 23, 42, 0.05), 0 2px 4px -1px rgba(15, 23, 42, 0.03);
    --shadow-lg:     0 10px 15px -3px rgba(15, 23, 42, 0.05), 0 4px 6px -2px rgba(15, 23, 42, 0.03);
    --shadow-hover:  0 14px 24px -4px rgba(15, 23, 42, 0.08), 0 6px 10px -4px rgba(15, 23, 42, 0.04);
    --font-body:     'Inter', sans-serif;
    --font-mono:     'JetBrains Mono', monospace;
    --transition:    all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Page background ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--c-bg) !important;
    font-family: var(--font-body) !important;
    color: var(--c-text) !important;
}

/* ── Subtle Security Grid & Shield Watermark Background ── */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(37, 99, 235, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(37, 99, 235, 0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    background-position: center center;
    pointer-events: none;
    z-index: 0;
}
[data-testid="stAppViewContainer"]::after {
    content: '🛡️';
    position: fixed;
    bottom: -5vh;
    right: -2vw;
    font-size: 40vh;
    opacity: 0.02;
    pointer-events: none;
    z-index: 0;
    transform: rotate(-15deg);
    filter: grayscale(100%);
}

/* ── Main content area ── */
[data-testid="stMain"], .main .block-container {
    background: transparent !important;
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    position: relative;
    z-index: 1;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--c-surface) !important;
    border-right: 1px solid var(--c-border) !important;
    box-shadow: var(--shadow-md) !important;
}
[data-testid="stSidebar"] * {
    color: var(--c-text) !important;
    font-family: var(--font-body) !important;
}
[data-testid="stSidebar"] .stMetric {
    background: var(--c-gray-100) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: var(--radius-md) !important;
    padding: 12px 16px !important;
    margin-bottom: 12px !important;
    transition: var(--transition) !important;
}
[data-testid="stSidebar"] .stMetric:hover {
    background: var(--c-surface) !important;
    transform: translateX(4px);
    box-shadow: var(--shadow-sm);
    border-color: var(--c-blue-accent) !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMultiSelect label,
[data-testid="stSidebar"] .stSlider label {
    color: var(--c-gray-600) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--c-blue-dark) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stSidebar"] .stMarkdown p {
    color: var(--c-text-muted) !important;
    font-size: 13px !important;
}

/* ── KPI metric cards ── */
[data-testid="stMetric"] {
    background: var(--c-surface) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 20px 24px !important;
    box-shadow: var(--shadow-md) !important;
    transition: var(--transition) !important;
    position: relative;
    overflow: hidden;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--c-blue-mid), #8B5CF6);
    opacity: 0.9;
}
[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-hover) !important;
    transform: translateY(-4px);
    border-color: var(--c-blue-light) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: var(--c-gray-500) !important;
}
[data-testid="stMetricValue"] {
    font-size: 32px !important;
    font-weight: 700 !important;
    color: var(--c-blue-dark) !important;
    font-family: var(--font-mono) !important;
    letter-spacing: -0.02em !important;
    margin-top: 4px !important;
}
[data-testid="stMetricDelta"] {
    font-size: 13px !important;
    font-weight: 600 !important;
}

/* ── Plotly chart containers ── */
[data-testid="stPlotlyChart"] {
    background: var(--c-surface) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: var(--radius-lg) !important;
    padding: 20px !important;
    box-shadow: var(--shadow-md) !important;
    transition: var(--transition) !important;
}
[data-testid="stPlotlyChart"]:hover {
    box-shadow: var(--shadow-hover) !important;
    border-color: var(--c-gray-300) !important;
    transform: translateY(-2px);
}

/* ── Section headings ── */
h3, h4, h5 {
    color: var(--c-blue-dark) !important;
    font-family: var(--font-body) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}
h5 {
    font-size: 15px !important;
    color: var(--c-gray-800) !important;
    margin-bottom: 12px !important;
}

/* ── Section title pill (Pulse animations) ── */
.section-header {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: var(--c-blue-light);
    border: 1px solid rgba(37,99,235,0.2);
    border-radius: 100px;
    padding: 6px 16px 6px 12px;
    margin-bottom: 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--c-blue-mid);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    box-shadow: var(--shadow-sm);
}
.section-header .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--c-blue-accent);
    animation: safe-pulse 2s ease-in-out infinite;
}
.section-header.alert-header {
    background: var(--c-red-light);
    border-color: rgba(239, 68, 68, 0.2);
    color: var(--c-red);
}
.section-header.alert-header .dot {
    background: var(--c-red);
    animation: alert-pulse 1.2s ease-in-out infinite;
}
@keyframes safe-pulse {
    0%,100% { opacity:1; transform:scale(1); box-shadow: 0 0 0 0 rgba(59,130,246,0.4); }
    50%      { opacity:0.7; transform:scale(0.85); box-shadow: 0 0 0 4px rgba(59,130,246,0); }
}
@keyframes alert-pulse {
    0%,100% { opacity:1; transform:scale(1); box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
    50%      { opacity:0.8; transform:scale(1.15); box-shadow: 0 0 0 6px rgba(239,68,68,0); }
}

/* ── Dataframe / Alert feed ── */
[data-testid="stDataFrame"] {
    background: var(--c-surface) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: var(--shadow-md) !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] table {
    font-family: var(--font-mono) !important;
    font-size: 13px !important;
    color: var(--c-gray-800) !important;
}
[data-testid="stDataFrame"] thead th {
    background: var(--c-gray-100) !important;
    color: var(--c-gray-600) !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    border-bottom: 2px solid var(--c-border) !important;
    padding: 14px 16px !important;
}
[data-testid="stDataFrame"] tbody tr {
    transition: var(--transition) !important;
}
[data-testid="stDataFrame"] tbody tr:hover {
    background: var(--c-gray-100) !important;
    transform: scale(1.001);
}

/* ── Alert / info / success boxes ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border-left-width: 5px !important;
    font-family: var(--font-body) !important;
    font-size: 15px !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ── Divider ── */
hr {
    border-color: var(--c-gray-200) !important;
    margin: 2rem 0 !important;
}

/* ── UI Element Overrides (Sliders, Selects) ── */
div[data-baseweb="slider"] > div > div {
    background: var(--c-blue-mid) !important;
}
.stCheckbox > label {
    color: var(--c-text) !important;
}

/* ── Streamlit default overrides ── */
.stApp header { background: transparent !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── Smooth Cascade Animation for Elements ── */
@keyframes cascadeUp {
    from { opacity:0; transform:translateY(20px); }
    to   { opacity:1; transform:translateY(0); }
}
.main .block-container > * {
    animation: cascadeUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.main .block-container > *:nth-child(1) { animation-delay: 0.00s; }
.main .block-container > *:nth-child(2) { animation-delay: 0.08s; }
.main .block-container > *:nth-child(3) { animation-delay: 0.16s; }
.main .block-container > *:nth-child(4) { animation-delay: 0.24s; }
.main .block-container > *:nth-child(5) { animation-delay: 0.32s; }
.main .block-container > *:nth-child(6) { animation-delay: 0.40s; }
.main .block-container > *:nth-child(7) { animation-delay: 0.48s; }

/* ── Scrollbar customization ── */
::-webkit-scrollbar { width:8px; height:8px; }
::-webkit-scrollbar-track { background: var(--c-bg); }
::-webkit-scrollbar-thumb { background: var(--c-gray-300); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: var(--c-gray-400); }
</style>
""", unsafe_allow_html=True)

# (Plotly Layout styling logic removed - now isolated in helpers.charts)

df, total_docs = load_data()

if df is None:
    st.stop()

if df.empty:
    st.info("No data available yet. Waiting for transactions stream...")
    time.sleep(10)
    st.rerun()

df['processed_at'] = pd.to_datetime(df['processed_at'])

# SIDEBAR
st.sidebar.title("🛡️ FraudPulse")
st.sidebar.markdown("Real-time fraud detection engine.")

st.sidebar.subheader("Pipeline Status")
st.sidebar.metric("MongoDB Docs", f"{total_docs:,}")
st.sidebar.metric("Latest Update", df['processed_at'].max().strftime("%H:%M:%S"))

st.sidebar.subheader("Filters")
selected_types = st.sidebar.multiselect("Transaction Type", options=df['type'].unique(), default=df['type'].unique())
selected_risk = st.sidebar.multiselect("Risk Level", options=df['risk_level'].unique(), default=df['risk_level'].unique())

min_amt = float(df['amount'].min())
max_amt = float(df['amount'].max())
if max_amt <= 0.0:
    max_amt = 1000.0  # Safe default if all amounts are zero
selected_amount = st.sidebar.slider("Min Amount ($)", min_value=0.0, max_value=max_amt, value=0.0)

min_step = int(df['step'].min())
max_step = int(df['step'].max())
if max_step <= min_step:
    max_step = min_step + 1  # Slider requires max > min
selected_step = st.sidebar.slider("Step Range", min_value=min_step, max_value=max_step, value=(min_step, max_step))

filtered_df = df[
    (df['type'].isin(selected_types)) &
    (df['risk_level'].isin(selected_risk)) &
    (df['amount'] >= selected_amount) &
    (df['step'] >= selected_step[0]) &
    (df['step'] <= selected_step[1])
]

# KPI SECTION
st.markdown("""
<div class="section-header">
  <span class="dot"></span>Live Metrics
</div>
""", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_txs = len(filtered_df)
fraud_txs = len(filtered_df[filtered_df['fraud_flag'] == True])
fraud_rate = (fraud_txs / total_txs * 100) if total_txs > 0 else 0
total_fraud_amt = filtered_df[filtered_df['fraud_flag'] == True]['amount'].sum()
avg_prob = filtered_df['fraud_probability'].mean() if total_txs > 0 else 0

# Calculating real deltas based on the last 5 minutes of data
five_mins_ago = df['processed_at'].max() - pd.Timedelta(minutes=5)
recent_df = filtered_df[filtered_df['processed_at'] >= five_mins_ago]
recent_total_txs = len(recent_df)
recent_fraud_txs = len(recent_df[recent_df['fraud_flag'] == True])
recent_fraud_rate = (recent_fraud_txs / recent_total_txs * 100) if recent_total_txs > 0 else 0

kpi1.metric("Total Transactions", f"{total_txs:,}", delta=f"{recent_total_txs} last 5m")
kpi2.metric("Fraud Rate %", f"{fraud_rate:.2f}%", delta=f"{recent_fraud_rate:.2f}% last 5m")
kpi3.metric("Total Fraudulent Amount", f"${total_fraud_amt:,.2f}")
kpi4.metric("Avg Fraud Probability", f"{avg_prob:.4f}")

st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)

# CHARTS ROW 1
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Tx Volume vs Fraud Count by Step")
    fig1 = hc.create_step_volume_chart(filtered_df)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("##### Fraud Probability Distribution")
    fig2 = hc.create_fraud_prob_chart(filtered_df)
    st.plotly_chart(fig2, use_container_width=True)

# CHARTS ROW 2
col3, col4 = st.columns(2)

with col3:
    st.markdown("##### Fraud Rate by Transaction Type")
    fig3 = hc.create_type_rate_chart(filtered_df)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("##### Avg Fraudulent Amount by Type")
    fig4 = hc.create_type_amt_chart(filtered_df)
    if fig4:
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No fraudulent transactions found.")

# CHARTS ROW 3
col5, col6, col7 = st.columns(3)

with col5:
    st.markdown("##### Risk Level Distribution")
    fig5 = hc.create_risk_pie_chart(filtered_df)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown("##### Model vs Rule Engine Overlap")
    fig6 = hc.create_overlap_chart(filtered_df)
    if fig6:
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.info("No frauds.")

with col7:
    st.markdown("##### Balance Drain (Origin)")
    fig7 = hc.create_origin_scatter_chart(filtered_df)
    st.plotly_chart(fig7, use_container_width=True)


# LIVE ALERT FEED
st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)
st.markdown("""
<div class="section-header alert-header">
  <span class="dot"></span>Live Alert Feed — Last 20 Fraud Transactions
</div>
""", unsafe_allow_html=True)

fraud_feed = df[df['fraud_flag'] == True].head(20).copy()
if not fraud_feed.empty:
    cols_to_show = ['nameOrig', 'nameDest', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig',
                    'fraud_probability', 'risk_level', 'rule_triggered', 'model_flag', 'processed_at']
    def highlight_risk(row):
        if row.risk_level == 'HIGH':
            return [
                'background-color:#FEF2F2; color:#B91C1C; font-weight:700; border-bottom:1px solid #FECACA'
                if c in ['risk_level', 'fraud_probability', 'amount'] else
                'background-color:#FEF2F2; color:#991B1B; border-bottom:1px solid #FECACA'
                for c in row.index
            ]
        elif row.risk_level == 'MEDIUM':
            return [
                'background-color:#FFF7ED; color:#C2410C; font-weight:700; border-bottom:1px solid #FED7AA'
                if c in ['risk_level', 'fraud_probability', 'amount'] else
                'background-color:#FFF7ED; color:#9A3412; border-bottom:1px solid #FED7AA'
                for c in row.index
            ]
        return ['border-bottom:1px solid #E2E8F0'] * len(row)
    
    st.dataframe(
        fraud_feed[cols_to_show].style.apply(highlight_risk, axis=1),
        use_container_width=True,
        height=420,
    )
else:
    st.success("No recent fraud detections.")

time.sleep(10)
st.rerun()