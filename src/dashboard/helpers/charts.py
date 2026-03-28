import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# PLOTLY STYLING INTEGRATION (Light, Clean, Professional)
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#475569"),
    margin=dict(l=0, r=0, t=20, b=0),
    xaxis=dict(
        gridcolor="#E2E8F0",
        linecolor="#CBD5E1",
        tickfont=dict(size=12, color="#64748B"),
        title_font=dict(family="Inter", size=13, color="#475569"),
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="#E2E8F0",
        linecolor="#CBD5E1",
        tickfont=dict(size=12, color="#64748B"),
        title_font=dict(family="Inter", size=13, color="#475569"),
        zeroline=False,
    ),
    hoverlabel=dict(
        bgcolor="#FFFFFF",
        bordercolor="#CBD5E1",
        font=dict(family="JetBrains Mono, monospace", size=13, color="#0F172A"),
    ),
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#E2E8F0",
        borderwidth=1,
        font=dict(family="Inter", size=12, color="#334155"),
    ),
    colorway=["#2563EB","#3B82F6","#60A5FA","#93C5FD","#EF4444","#F97316","#10B981"],
)

def apply_layout(fig, **extra):
    layout = {**PLOTLY_LAYOUT, **extra}
    fig.update_layout(**layout)
    return fig

def create_step_volume_chart(filtered_df):
    step_grouped = filtered_df.groupby('step').agg(total=('amount', 'count'), fraud=('fraud_flag', 'sum')).reset_index()
    step_grouped = step_grouped.sort_values('step')
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=step_grouped['step'], y=step_grouped['total'],
        name='Total Volume', marker_color='#DBEAFE', opacity=1.0,
        marker_line_width=1, marker_line_color='#93C5FD'
    ))
    fig.add_trace(go.Scatter(
        x=step_grouped['step'], y=step_grouped['fraud'],
        name='Fraud Count', yaxis='y2', mode='lines+markers',
        line=dict(color='#EF4444', width=3),
        marker=dict(size=7, color='#EF4444', line=dict(width=2, color='white')),
    ))
    return apply_layout(fig,
        yaxis=dict(title='Total Volume', gridcolor='#F1F5F9', tickfont=dict(size=11, color='#64748B'), zeroline=False),
        yaxis2=dict(title='Fraud Count', overlaying='y', side='right', gridcolor='transparent', tickfont=dict(size=11, color='#EF4444'), zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, bgcolor='rgba(255,255,255,0)', borderwidth=0),
        hovermode="x unified",
    )

def create_fraud_prob_chart(filtered_df):
    fig = px.histogram(filtered_df, x="fraud_probability", nbins=50, color_discrete_sequence=['#3B82F6'])
    fig.update_traces(marker_line_color='#2563EB', marker_line_width=1, opacity=0.9)
    return apply_layout(fig)

def create_type_rate_chart(filtered_df):
    type_grouped = filtered_df.groupby('type').agg(txs=('amount', 'count'), frauds=('fraud_flag', 'sum')).reset_index()
    type_grouped['rate'] = type_grouped['frauds'] / type_grouped['txs'] * 100
    fig = px.bar(type_grouped, x='type', y='rate', color='type', text_auto='.2f',
                 color_discrete_sequence=['#2563EB','#3B82F6','#60A5FA','#93C5FD','#EF4444'])
    fig.update_traces(marker_line_width=0, textfont_size=12, textfont_color='#1E293B', textposition='outside')
    return apply_layout(fig, showlegend=False)

def create_type_amt_chart(filtered_df):
    fraud_only = filtered_df[filtered_df['fraud_flag'] == True]
    if fraud_only.empty:
        return None
    avg_amt_type = fraud_only.groupby('type')['amount'].mean().reset_index()
    fig = px.bar(avg_amt_type, x='type', y='amount', color_discrete_sequence=['#EF4444'], text_auto='.2f')
    fig.update_traces(marker_line_width=0, textfont_size=12, textfont_color='#1E293B', textposition='outside', opacity=0.9)
    return apply_layout(fig)

def create_risk_pie_chart(filtered_df):
    risk_counts = filtered_df['risk_level'].value_counts().reset_index()
    risk_counts.columns = ['Risk Level', 'Count']
    fig = px.pie(risk_counts, values='Count', names='Risk Level', hole=0.6, color='Risk Level',
                 color_discrete_map={'HIGH': '#EF4444', 'MEDIUM': '#F97316', 'LOW': '#10B981'})
    fig.update_traces(
        textfont_size=13, textfont_color="#FFFFFF",
        marker=dict(line=dict(color='#FFFFFF', width=3)),
        pull=[0.05 if r == 'HIGH' else 0 for r in risk_counts['Risk Level']],
    )
    return apply_layout(fig, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5,
                                    bgcolor='rgba(255,255,255,0)', borderwidth=0))

def create_overlap_chart(filtered_df):
    overlap = filtered_df[filtered_df['fraud_flag'] == True].copy()
    if overlap.empty:
        return None
    def categorize(row):
        if row['model_flag'] and row['rule_engine_flag']: return 'Both'
        if row['model_flag']: return 'Model Only'
        return 'Rule Only'
    overlap['Overlap'] = overlap.apply(categorize, axis=1)
    overlap_counts = overlap['Overlap'].value_counts().reset_index()
    overlap_counts.columns = ['Category', 'Count']
    fig = px.bar(overlap_counts, x='Category', y='Count', color='Category',
                 color_discrete_sequence=['#3B82F6', '#EF4444', '#F97316'])
    fig.update_traces(marker_line_width=0, opacity=0.9)
    return apply_layout(fig, showlegend=False)

def create_origin_scatter_chart(filtered_df):
    fig = px.scatter(
        filtered_df.sample(min(1000, len(filtered_df))),
        x='oldbalanceOrg', y='amount',
        color='fraud_flag', size_max=10, opacity=0.75,
        color_discrete_map={True: '#EF4444', False: '#64748B'},
    )
    fig.update_traces(marker=dict(line=dict(width=1, color='white')))
    return apply_layout(fig, legend=dict(title='Is Fraud', bgcolor='rgba(255,255,255,0.9)',
                                   bordercolor='#E2E8F0', borderwidth=1))
