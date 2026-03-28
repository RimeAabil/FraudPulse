import streamlit as st
import pandas as pd
import time

from helpers.data_utils import load_data
import helpers.charts as hc

st.set_page_config(page_title="FraudPulse | Network Integrity", page_icon="🛡️", layout="wide")

# ── ADVANCED SAAS DESIGN SYSTEM ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --brand-primary: #2563EB;
    --brand-secondary: #475569;
    --bg-main: #FFFFFF;
    --bg-subtle: #F8FAFC;
    --border-color: #E2E8F0;
    --text-main: #1E293B; /* Elegant Slate Blue */
    --text-bold: #0F172A;
    --text-muted: #64748B;
    --success: #059669;
    --warning: #D97706;
    --danger: #DC2626;
}

/* Base resets & typography */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-main) !important;
    font-family: 'Inter', sans-serif !important;
}

/* High Contrast & Elegance */
p, span, li, h1, h2, h3, h4, h5, h6, div {
    color: var(--text-main);
}
b, strong {
    color: var(--text-bold);
}

/* Force Filter Tags to Blue (Professional) */
[data-baseweb="tag"] {
    background-color: var(--brand-primary) !important;
    color: white !important;
}
[data-baseweb="tag"] span {
    color: white !important;
}

/* Sidebar Radio Labels Visibility */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: var(--text-bold) !important;
    font-weight: 700 !important;
}

/* Professional Metric Cards */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    padding: 1.25rem !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--text-muted) !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stMetricValue"] {
    color: var(--text-bold) !important;
    font-weight: 800 !important;
}

/* Section Header styling */
.section-header {
    font-size: 0.8rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--brand-primary) !important;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2.5rem 0 1rem 0;
}
.section-header .dot {
    width: 6px; height: 6px; border-radius: 50%; background: var(--brand-primary);
}

/* Force light theme for all internal components */
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #FFFFFF !important;
}

/* Pastel Blue Sidebar */
[data-testid="stSidebar"] {
    background-color: #F1F5F9 !important; /* Light Slate / Pastel Blue */
    border-right: 1px solid var(--border-color) !important;
}

/* Sidebar Reset for Lightness */
[data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
    color: var(--text-bold) !important;
}

/* Decisive Dataframe Overrides (Pure White) */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    background-color: #FFFFFF !important;
    border: 1px solid var(--border-color) !important;
}
[data-testid="stDataFrame"] div, [data-testid="stDataFrame"] span {
    color: var(--text-main) !important;
}

/* Elegant Table Header Override */
.stDataFrame thead th {
    background-color: #F8FAFC !important;
    color: var(--text-bold) !important;
    font-weight: 700 !important;
}

/* Top bar styling */
.top-bar {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 0; border-bottom: 2px solid var(--border-color);
    margin-bottom: 2.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── LOGIC: DATA & STATE ──
df, total_docs = load_data()
if df is None: st.stop()
if df.empty:
    st.info("Initializing Network Stream...")
    time.sleep(5)
    st.rerun()

df['processed_at'] = pd.to_datetime(df['processed_at'])

# ── HYBRID NAVIGATION ──
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092202.png", width=60) # Shield icon
    st.markdown("### FraudPulse **PRO**")
    st.caption("Network Integrity Engine v2.4")
    st.markdown("<br>", unsafe_allow_html=True)
    
    page = st.radio("MAIN NAVIGATION", 
                    ["OVERVIEW", "ANALYTICS", "EXPLORER", "ALERTS"],
                    index=0, label_visibility="collapsed")
    
    st.markdown("---")
    st.markdown("#### ACTIVE FILTERS")
    f_type = st.multiselect("TRANS. TYPE", options=df['type'].unique(), default=df['type'].unique())
    f_risk = st.multiselect("RISK THRESHOLD", options=['HIGH', 'MEDIUM', 'LOW'], default=['HIGH', 'MEDIUM', 'LOW'])
    
    st.markdown("---")
    st.markdown("#### PIPELINE OPS")
    st.info(f"⚡ Live: {total_docs:,} events indexed")

# Global Filter Application
filtered_df = df[
    (df['type'].isin(f_type)) &
    (df['risk_level'].isin(f_risk))
]

# ── TOP BAR COMPONENT ──
st.markdown(f"""
<div class="top-bar">
    <div style="font-weight: 800; color: #0F172A; font-family: 'Inter', sans-serif;">
        <span class="pulse-indicator"></span> NETWORK STATUS: <span style="color: #059669;">OPERATIONAL</span>
    </div>
    <div style="font-size: 0.85rem; color: #475569; font-weight: 600;">
        LAST SYNC: {df['processed_at'].max().strftime('%H:%M:%S')}
    </div>
</div>
""", unsafe_allow_html=True)

# ── PAGE ROUTING ──
content_area = st.container()

with content_area:
    if page == "OVERVIEW":
        # Custom Risk Gauge (SVG)
        avg_score = filtered_df['fraud_probability'].mean()
        gauge_color = "#059669" if avg_score < 0.3 else "#D97706" if avg_score < 0.7 else "#DC2626"
        
        st.markdown(f"""
        <div style="display: flex; gap: 2rem; align-items: center; background: #FFFFFF; padding: 2rem; border-radius: 16px; border: 2px solid #E2E8F0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="flex: 1;">
                <div class="section-header"><span class="dot"></span>Global Risk Index</div>
                <h1 style="font-size: 4rem; margin: 0; color: {gauge_color} !important; font-weight: 900;">{avg_score:.2%}</h1>
                <p style="color: #0F172A !important; font-weight: 700; font-size: 1.1rem; margin: 0;">Aggregated threat probability across active streams.</p>
            </div>
            <div style="flex: 0 0 300px;">
                 <svg viewBox="0 0 100 50" width="100%">
                    <path d="M 10 45 A 35 35 0 0 1 90 45" fill="none" stroke="#F1F5F9" stroke-width="8" stroke-linecap="round"/>
                    <path d="M 10 45 A 35 35 0 0 1 90 45" fill="none" stroke="{gauge_color}" stroke-width="8" stroke-dasharray="{avg_score * 125}, 1000" stroke-linecap="round"/>
                 </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Executive KPIs
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Throughput", f"{len(filtered_df):,}")
        fraud_count = len(filtered_df[filtered_df['fraud_flag'] == True])
        kpi2.metric("Identified Threats", f"{fraud_count:,}", delta=f"{(fraud_count/max(1,len(filtered_df))):.1%}", delta_color="inverse")
        total_val = filtered_df[filtered_df['fraud_flag'] == True]['amount'].sum()
        kpi3.metric("Capital at Risk", f"${total_val:,.0f}")

        st.markdown('<div class="section-header"><span class="dot"></span>Stream Trajectory</div>', unsafe_allow_html=True)
        st.plotly_chart(hc.create_step_volume_chart(filtered_df), use_container_width=True)

    elif page == "ANALYTICS":
        st.markdown('<div class="section-header"><span class="dot"></span>Behavioral Intelligence</div>', unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["💰 LOSS ANALYSIS", "🕵️ ENGINE OVERLAP"])
        
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### Threat Density by Type")
                st.plotly_chart(hc.create_type_rate_chart(filtered_df), use_container_width=True)
            with c2:
                st.markdown("##### Average Exposure per Case")
                fig = hc.create_type_amt_chart(filtered_df)
                if fig: st.plotly_chart(fig, use_container_width=True)
                else: st.info("No data in current view.")

        with tab2:
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("##### Detector Overlap (ML vs Rules)")
                fig_ov = hc.create_overlap_chart(filtered_df)
                if fig_ov: st.plotly_chart(fig_ov, use_container_width=True)
            with c4:
                st.markdown("##### Confidence Clusters")
                st.plotly_chart(hc.create_fraud_prob_chart(filtered_df), use_container_width=True)

        st.markdown("---")
        st.markdown("##### Forensic Origin Mapping")
        st.plotly_chart(hc.create_origin_scatter_chart(filtered_df), use_container_width=True)

    elif page == "EXPLORER":
        st.markdown('<div class="section-header"><span class="dot"></span>Forensic Explorer</div>', unsafe_allow_html=True)
        st.caption("Investigate every transaction with millisecond precision.")
        
        explorer_df = filtered_df.sort_values('processed_at', ascending=False).head(100).copy()
        
        # Elegant Investigator Style (Slate & Crimson)
        def investigator_style(row):
            if row.fraud_flag:
                return ['color: #991B1B !important; font-weight: 700; background-color: #FEF2F2 !important'] * len(row)
            return ['color: #334155 !important; font-weight: 500'] * len(row)

        st.dataframe(
            explorer_df.style.apply(investigator_style, axis=1)
                       .format({"amount": "${:,.2f}", "fraud_probability": "{:.4f}"}),
            use_container_width=True,
            height=700
        )

    elif page == "ALERTS":
        st.markdown('<div class="section-header alert-header"><span class="dot"></span>Live Threat Feed</div>', unsafe_allow_html=True)
        
        threats = df[df['fraud_flag'] == True].sort_values('processed_at', ascending=False).head(30).copy()
        
        if threats.empty:
            st.success("No critical threats detected in current stream buffer.")
        else:
            for idx, row in threats.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div style="background: white; border: 1px solid #E2E8F0; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border-left: 6px solid #DC2626; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <span style="font-size: 0.85rem; color: #475569 !important; font-weight: 700; font-family: 'JetBrains Mono', monospace;">ID: {row.nameOrig}</span>
                                <h4 style="margin: 0.5rem 0; color: #0F172A !important; font-weight: 800; font-size: 1.25rem;">{row.type} ATTEMPT</h4>
                                <p style="margin: 0; font-size: 1rem; color: #334155 !important; font-weight: 600;">Node: <span style="font-family: 'JetBrains Mono'; color: #0F172A !important;">{row.nameDest}</span> | Risk Score: <span style="color: #DC2626 !important; font-weight: 800;">{row.fraud_probability:.2%}</span></p>
                            </div>
                            <div style="text-align: right;">
                                <h2 style="margin: 0; color: #B91C1C !important; font-weight: 900;">${row.amount:,.2f}</h2>
                                <span style="font-size: 0.85rem; color: #64748B !important; font-weight: 700;">{row.processed_at.strftime('%H:%M:%S')}</span>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

# ── AUTO-REFRESH ──
time.sleep(10)
st.rerun()