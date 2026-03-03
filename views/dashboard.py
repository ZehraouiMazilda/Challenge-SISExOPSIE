# views/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# ─────────────────────────────────────────────
# DESIGN SYSTEM (identique à ml_analysis)
# ─────────────────────────────────────────────
STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg-dark:    #0a0e1a;
    --bg-card:    #111827;
    --bg-card2:   #1a2235;
    --accent:     #00d4ff;
    --accent2:    #ff4d6d;
    --accent3:    #7b61ff;
    --text:       #e2e8f0;
    --text-dim:   #8892a4;
    --border:     rgba(0, 212, 255, 0.15);
    --success:    #10b981;
    --warning:    #f59e0b;
}

.stApp { background-color: var(--bg-dark) !important; }
section[data-testid="stSidebar"] { background-color: #080c16 !important; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 3rem !important; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}
h1, h2, h3, h4 { font-family: 'Space Mono', monospace !important; }

.ml-hero {
    background: linear-gradient(135deg, #0d1b2a 0%, #0a0e1a 50%, #1a0a2e 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.ml-hero::before {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.ml-hero h1 {
    font-size: 1.8rem;
    color: var(--accent) !important;
    margin: 0 0 0.5rem 0;
    letter-spacing: -1px;
}
.ml-hero p { color: var(--text-dim); font-size: 0.95rem; margin: 0; max-width: 700px; line-height: 1.7; }

.section-header {
    display: flex; align-items: center; gap: 0.75rem;
    margin-bottom: 1.2rem; padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--border);
}
.section-icon {
    width: 36px; height: 36px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0;
}
.icon-blue   { background: rgba(0,212,255,0.12); }
.icon-red    { background: rgba(255,77,109,0.12); }
.icon-purple { background: rgba(123,97,255,0.12); }
.icon-green  { background: rgba(16,185,129,0.12); }
.icon-orange { background: rgba(245,158,11,0.12); }
.section-title {
    font-family: 'Space Mono', monospace !important;
    font-size: 1rem; font-weight: 700;
    color: var(--text) !important; margin: 0;
}
.section-subtitle { font-size: 0.8rem; color: var(--text-dim); margin: 0; }

.metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem; margin: 1.2rem 0;
}
.metric-box {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 10px; padding: 1rem 1.2rem; text-align: center;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem; font-weight: 700;
    color: var(--accent); display: block;
}
.metric-label {
    font-size: 0.72rem; color: var(--text-dim);
    text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.3rem;
}
.metric-box.red    .metric-value { color: var(--accent2); }
.metric-box.purple .metric-value { color: var(--accent3); }
.metric-box.green  .metric-value { color: var(--success); }

.info-box {
    background: rgba(0,212,255,0.06);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem; font-size: 0.85rem;
    color: var(--text-dim); line-height: 1.6; margin: 0.8rem 0;
}

.stSelectbox label, .stSlider label, .stRadio label,
.stMultiSelect label, .stNumberInput label {
    color: var(--text-dim) !important;
    font-size: 0.82rem !important;
    text-transform: uppercase; letter-spacing: 0.05em;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: var(--bg-card2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
.stDataFrame { background: var(--bg-card2) !important; }
.stAlert { border-radius: 8px !important; }
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }
</style>
"""

PLOTLY_TEMPLATE = dict(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font=dict(color="#e2e8f0", family="DM Sans"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True),
    margin=dict(t=40, b=40, l=40, r=20),
    colorway=["#00d4ff", "#ff4d6d", "#7b61ff", "#10b981", "#f59e0b"],
)

def section_header(icon, title, subtitle, icon_class="icon-blue"):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-icon {icon_class}">{icon}</div>
        <div>
            <p class="section-title">{title}</p>
            <p class="section-subtitle">{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def metrics_row(items):
    cols = st.columns(len(items))
    for col, (label, value, cls) in zip(cols, items):
        col.markdown(f"""
        <div class="metric-box {cls}">
            <span class="metric-value">{value}</span>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

def info_box(text):
    st.markdown(f'<div class="info-box">ℹ️ {text}</div>', unsafe_allow_html=True)

def apply_template(fig, **kwargs):
    """Apply PLOTLY_TEMPLATE safely, allowing xaxis/yaxis overrides."""
    exclude = [k for k in kwargs if k in ('xaxis', 'yaxis')]
    base = {k: v for k, v in PLOTLY_TEMPLATE.items() if k not in exclude}
    fig.update_layout(**base, **kwargs)

# ─────────────────────────────────────────────
# DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_exm.csv')
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    df['hour'] = df['date'].dt.hour
    df['day']  = df['date'].dt.date
    return df

def get_port_category(port):
    if port < 1024:
        return "System Ports (0-1023)"
    elif port < 49152:
        return "User Ports (1024-49151)"
    else:
        return "Dynamic Ports (49152-65535)"

# ─────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────
def show():
    st.markdown(STYLE, unsafe_allow_html=True)

    st.markdown("""
    <div class="ml-hero">
        <h1>📊 Dashboard Descriptif</h1>
        <p>
            Analyse interactive des flux réseau issus des logs pare-feu Iptables.
            Filtrage par protocole et plage de ports selon la RFC 6056,
            comparaison TCP / UDP, distribution des ports privilégiés et exploration des données brutes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    try:
        df = load_data()
        df['port_category'] = df['dest_port'].apply(get_port_category)

        # ── SECTION 1 : VUE D'ENSEMBLE ──────────────────────────────
        section_header("🚦", "Vue d'Ensemble des Flux",
                       "Indicateurs globaux sur l'ensemble des données chargées", "icon-blue")

        blocked  = len(df[df['action'] == 'Deny'])
        permitted = len(df[df['action'] == 'Permit'])
        metrics_row([
            ("Total des flux",          f"{len(df):,}",              ""),
            ("Flux autorisés",          f"{permitted:,}",            "green"),
            ("Flux bloqués",            f"{blocked:,}",              "red"),
            ("Adresses IP sources",     f"{df['ip_source'].nunique():,}", "purple"),
            ("Ports distincts",         f"{df['dest_port'].nunique():,}", ""),
        ])

        st.markdown("---")

        # ── SECTION 2 : FILTRES ─────────────────────────────────────
        section_header("🔧", "Filtres Interactifs",
                       "Protocole et plage de ports selon la RFC 6056", "icon-purple")

        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_protocol = st.multiselect(
                "Filtrer par protocole",
                options=df['protocol'].unique(),
                default=df['protocol'].unique()
            )
        with filter_col2:
            port_range = st.selectbox(
                "Sélectionner une plage de ports (RFC 6056)",
                ["Tous les ports",
                 "System Ports (0-1023)",
                 "User Ports (1024-49151)",
                 "Dynamic Ports (49152-65535)",
                 "Plage personnalisée"]
            )

        min_port, max_port = 0, 65535
        if port_range == "Plage personnalisée":
            port_col1, port_col2 = st.columns(2)
            with port_col1:
                min_port = st.number_input("Port minimum", 0, 65535, 0)
            with port_col2:
                max_port = st.number_input("Port maximum", 0, 65535, 65535)

        filtered_df = df[df['protocol'].isin(filter_protocol)].copy()
        if port_range == "System Ports (0-1023)":
            filtered_df = filtered_df[filtered_df['dest_port'] < 1024]
        elif port_range == "User Ports (1024-49151)":
            filtered_df = filtered_df[(filtered_df['dest_port'] >= 1024) & (filtered_df['dest_port'] < 49152)]
        elif port_range == "Dynamic Ports (49152-65535)":
            filtered_df = filtered_df[filtered_df['dest_port'] >= 49152]
        elif port_range == "Plage personnalisée":
            filtered_df = filtered_df[(filtered_df['dest_port'] >= min_port) & (filtered_df['dest_port'] <= max_port)]

        filtered_df['port_category'] = filtered_df['dest_port'].apply(get_port_category)

        info_box(f"Résultat du filtre : <strong>{len(filtered_df):,} flux</strong> sur {len(df):,} au total "
                 f"({len(filtered_df)/len(df)*100:.1f}%)")

        st.markdown("---")

        # ── SECTION 3 : ANALYSE DES FLUX ────────────────────────────
        section_header("📈", "Analyse des Flux par Protocole et dans le Temps",
                       "Distribution Permit / Deny et évolution temporelle du trafic", "icon-blue")

        col1, col2 = st.columns([1, 2])

        with col1:
            protocol_action = pd.crosstab(filtered_df['protocol'], filtered_df['action'])
            fig_proto = go.Figure()
            if 'Permit' in protocol_action.columns:
                fig_proto.add_trace(go.Bar(
                    name='Autorisé', x=protocol_action.index,
                    y=protocol_action['Permit'], marker_color='#10b981'
                ))
            if 'Deny' in protocol_action.columns:
                fig_proto.add_trace(go.Bar(
                    name='Rejeté', x=protocol_action.index,
                    y=protocol_action['Deny'], marker_color='#ff4d6d'
                ))
            apply_template(fig_proto,
                title='Flux Autorisés vs Rejetés par Protocole',
                barmode='group', height=440,
                xaxis=dict(title='Protocole', gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title='Nombre de flux', gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_proto, use_container_width=True)

        with col2:
            daily_data = (
                filtered_df
                .groupby([filtered_df['date'].dt.date, 'port_category'])
                .size().reset_index(name='count')
            )
            daily_data.columns = ['date', 'port_category', 'count']

            date_range_days = (filtered_df['date'].max() - filtered_df['date'].min()).days
            buttons = []
            if date_range_days >= 7:
                buttons.append(dict(count=7,  label="1 semaine", step="day",   stepmode="backward"))
            if date_range_days >= 14:
                buttons.append(dict(count=14, label="2 semaines", step="day",  stepmode="backward"))
            if date_range_days >= 30:
                buttons.append(dict(count=1,  label="1 mois",    step="month", stepmode="backward"))
            if date_range_days >= 60:
                buttons.append(dict(count=2,  label="2 mois",    step="month", stepmode="backward"))
            buttons.append(dict(step="all", label="Tout"))

            fig_time = go.Figure()
            for category in daily_data['port_category'].unique():
                cat_data = daily_data[daily_data['port_category'] == category]
                fig_time.add_trace(go.Scatter(
                    x=cat_data['date'], y=cat_data['count'],
                    mode='lines+markers', name=category,
                    line=dict(width=2), marker=dict(size=4)
                ))
            apply_template(fig_time,
                title='Volume de Trafic dans le Temps',
                hovermode='x unified', height=440,
                xaxis=dict(
                    title='Date', type='date',
                    gridcolor='rgba(255,255,255,0.05)',
                    rangeselector=dict(buttons=buttons),
                    rangeslider=dict(visible=True)
                ),
                yaxis=dict(title='Nombre de flux', gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_time, use_container_width=True)

        st.markdown("---")

        # ── SECTION 4 : TCP vs UDP ───────────────────────────────────
        section_header("📡", "Comparaison Détaillée TCP vs UDP",
                       "Métriques et top 5 ports par protocole", "icon-green")

        tcp_data = filtered_df[filtered_df['protocol'] == 'TCP']
        udp_data = filtered_df[filtered_df['protocol'] == 'UDP']

        col1, col2 = st.columns(2)
        with col1:
            tcp_blocked   = len(tcp_data[tcp_data['action'] == 'Deny'])
            tcp_block_rate = (tcp_blocked / len(tcp_data) * 100) if len(tcp_data) > 0 else 0
            metrics_row([
                ("Total TCP",        f"{len(tcp_data):,}", ""),
                ("TCP bloqués",      f"{tcp_blocked:,}",   "red"),
                ("Taux de blocage",  f"{tcp_block_rate:.1f}%", "purple"),
            ])
        with col2:
            udp_blocked   = len(udp_data[udp_data['action'] == 'Deny'])
            udp_block_rate = (udp_blocked / len(udp_data) * 100) if len(udp_data) > 0 else 0
            metrics_row([
                ("Total UDP",        f"{len(udp_data):,}", ""),
                ("UDP bloqués",      f"{udp_blocked:,}",   "red"),
                ("Taux de blocage",  f"{udp_block_rate:.1f}%", "purple"),
            ])

        col1, col2 = st.columns(2)
        with col1:
            if len(tcp_data) > 0:
                top_tcp = tcp_data['dest_port'].value_counts().head(5).reset_index()
                top_tcp.columns = ['Port', 'Count']
                top_tcp['Port'] = top_tcp['Port'].astype(str)
                top_tcp = top_tcp.sort_values('Count', ascending=True)
                fig_tcp = px.bar(
                    top_tcp, x='Count', y='Port', orientation='h',
                    title="Top 5 Ports TCP",
                    color='Count',
                    color_continuous_scale=[[0, '#1a2235'], [1, '#00d4ff']]
                )
                apply_template(fig_tcp,
                    height=360, coloraxis_showscale=False,
                    yaxis=dict(type='category', gridcolor='rgba(255,255,255,0.05)'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig_tcp, use_container_width=True)
            else:
                st.info("Aucune donnée TCP dans la sélection.")

        with col2:
            if len(udp_data) > 0:
                top_udp = udp_data['dest_port'].value_counts().head(5).reset_index()
                top_udp.columns = ['Port', 'Count']
                top_udp['Port'] = top_udp['Port'].astype(str)
                top_udp = top_udp.sort_values('Count', ascending=True)
                fig_udp = px.bar(
                    top_udp, x='Count', y='Port', orientation='h',
                    title="Top 5 Ports UDP",
                    color='Count',
                    color_continuous_scale=[[0, '#1a2235'], [1, '#10b981']]
                )
                apply_template(fig_udp,
                    height=360, coloraxis_showscale=False,
                    yaxis=dict(type='category', gridcolor='rgba(255,255,255,0.05)'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig_udp, use_container_width=True)
            else:
                st.info("Aucune donnée UDP dans la sélection.")

        st.markdown("---")

        # ── SECTION 5 : DISTRIBUTION DES PORTS RFC 6056 ─────────────
        section_header("📊", "Distribution des Ports selon la RFC 6056",
                       "Répartition des catégories de ports et actions associées", "icon-orange")

        port_cat_dist = filtered_df['port_category'].value_counts().reset_index()
        port_cat_dist.columns = ['Catégorie', 'Nombre de flux']

        col1, col2 = st.columns(2)
        with col1:
            fig_pie = px.pie(
                port_cat_dist, values='Nombre de flux', names='Catégorie',
                title="Répartition par catégorie de ports",
                color_discrete_sequence=['#00d4ff', '#7b61ff', '#ff4d6d']
            )
            fig_pie.update_traces(textposition='inside', textinfo='label+percent', showlegend=False)
            fig_pie.update_layout(
                plot_bgcolor="#111827", paper_bgcolor="#111827",
                font=dict(color="#e2e8f0", family="DM Sans"),
                margin=dict(t=40, b=40, l=40, r=20), height=340
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            port_cat_action = pd.crosstab(filtered_df['port_category'], filtered_df['action'])
            fig_cat = go.Figure()
            if 'Permit' in port_cat_action.columns:
                fig_cat.add_trace(go.Bar(
                    name='Autorisé', y=port_cat_action.index,
                    x=port_cat_action['Permit'], orientation='h', marker_color='#10b981'
                ))
            if 'Deny' in port_cat_action.columns:
                fig_cat.add_trace(go.Bar(
                    name='Rejeté', y=port_cat_action.index,
                    x=port_cat_action['Deny'], orientation='h', marker_color='#ff4d6d'
                ))
            apply_template(fig_cat,
                title='Autorisés vs Rejetés par Catégorie',
                barmode='stack', height=340,
                xaxis=dict(title='Nombre de flux', gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_cat, use_container_width=True)

        st.markdown("---")

        # ── SECTION 6 : TOP IP SOURCES ──────────────────────────────
        section_header("🔝", "Adresses IP Sources",
                       "Top 5 IP les plus actives et analyse destinations vs rejets", "icon-red")

        top_ips = filtered_df['ip_source'].value_counts().head(5).reset_index()
        top_ips.columns = ['IP Source', 'Nombre de connexions']

        col1, col2 = st.columns(2)
        with col1:
            fig_ips = px.bar(
                top_ips, x='IP Source', y='Nombre de connexions',
                color='Nombre de connexions',
                color_continuous_scale=[[0, '#1a2235'], [1, '#00d4ff']],
                title="Top 5 des adresses IP sources les plus actives"
            )
            apply_template(fig_ips,
                coloraxis_showscale=False, height=360,
                xaxis=dict(title='Adresse IP Source', gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title='Connexions', gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_ips, use_container_width=True)

        with col2:
            ip_bubble = filtered_df.groupby('ip_source').agg(
                Nb_Destinations=('ip_destination', 'nunique')
            ).reset_index()
            ip_bubble.columns = ['IP Source', 'Nb Destinations Contactées']

            rejected = filtered_df.groupby('ip_source').apply(
                lambda x: (x['action'] == 'Deny').sum()
            ).reset_index(name='Flux Rejetés')
            allowed = filtered_df.groupby('ip_source').apply(
                lambda x: (x['action'] == 'Permit').sum()
            ).reset_index(name='Flux Autorisés')

            ip_bubble = (
                ip_bubble
                .merge(rejected, left_on='IP Source', right_on='ip_source', how='left')
                .merge(allowed,  left_on='IP Source', right_on='ip_source', how='left')
            )[['IP Source', 'Nb Destinations Contactées', 'Flux Rejetés', 'Flux Autorisés']]
            ip_bubble['Total Flux'] = ip_bubble['Flux Rejetés'] + ip_bubble['Flux Autorisés']

            fig_scatter = px.scatter(
                ip_bubble,
                x='Nb Destinations Contactées', y='Flux Rejetés',
                size='Total Flux', color='Flux Autorisés',
                hover_data=['IP Source', 'Flux Autorisés', 'Flux Rejetés', 'Total Flux'],
                title="Destinations Contactées vs Flux Rejetés",
                color_continuous_scale=[[0, '#1a2235'], [1, '#10b981']],
                size_max=60
            )
            fig_scatter.update_traces(marker=dict(line=dict(width=1, color='#00d4ff')))
            apply_template(fig_scatter,
                height=360,
                xaxis=dict(title='Nombre de destinations contactées', gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title='Nombre de flux rejetés', gridcolor='rgba(255,255,255,0.05)')
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with st.expander("📋 Voir le détail des Top 5 IP"):
            st.dataframe(top_ips, use_container_width=True)

        st.markdown("---")

        # ── SECTION 7 : TOP 10 PORTS PRIVILÉGIÉS ────────────────────
        section_header("🔌", "Top 10 Ports Privilégiés (inférieurs à 1024)",
                       "Services les plus sollicités dans la plage des ports système", "icon-green")

        ports_privileged = filtered_df[filtered_df['dest_port'] < 1024]

        if len(ports_privileged) > 0:
            top_ports = ports_privileged['dest_port'].value_counts().head(10).reset_index()
            top_ports.columns = ['Port', 'Nombre de connexions']
            port_names = {
                20: 'FTP-Data', 21: 'FTP', 22: 'SSH', 23: 'Telnet',
                25: 'SMTP', 53: 'DNS', 80: 'HTTP', 110: 'POP3',
                143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 3306: 'MySQL',
            }
            top_ports['Service'] = top_ports['Port'].map(port_names).fillna('Autre')

            col1, col2 = st.columns(2)
            with col1:
                fig_pie2 = px.pie(
                    top_ports, values='Nombre de connexions', names='Port',
                    title="Répartition des ports privilégiés", hole=0.4,
                    color_discrete_sequence=['#00d4ff','#7b61ff','#ff4d6d',
                                             '#10b981','#f59e0b','#60a5fa',
                                             '#f472b6','#34d399','#fb923c','#a78bfa']
                )
                fig_pie2.update_traces(textposition='inside', textinfo='label+percent', showlegend=False)
                fig_pie2.update_layout(
                    plot_bgcolor="#111827", paper_bgcolor="#111827",
                    font=dict(color="#e2e8f0", family="DM Sans"),
                    margin=dict(t=40, b=40, l=40, r=20), height=360
                )
                st.plotly_chart(fig_pie2, use_container_width=True)

            with col2:
                top_ports_bar = top_ports.copy()
                top_ports_bar['Port'] = top_ports_bar['Port'].astype(str)
                top_ports_bar = top_ports_bar.sort_values('Nombre de connexions', ascending=False)

                fig_ports_bar = px.bar(
                    top_ports_bar, x='Port', y='Nombre de connexions',
                    color='Service', title="Volume par port",
                    color_discrete_sequence=['#00d4ff','#7b61ff','#ff4d6d',
                                             '#10b981','#f59e0b','#60a5fa',
                                             '#f472b6','#34d399','#fb923c','#a78bfa']
                )
                fig_ports_bar.update_xaxes(
                    type='category',
                    categoryorder='array',
                    categoryarray=top_ports_bar['Port'].tolist()
                )
                apply_template(fig_ports_bar, height=360,
                    xaxis=dict(title='Port', gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(title='Connexions', gridcolor='rgba(255,255,255,0.05)')
                )
                st.plotly_chart(fig_ports_bar, use_container_width=True)

            with st.expander("📋 Voir le tableau complet des ports"):
                st.dataframe(top_ports, use_container_width=True)
        else:
            st.info("Aucun port privilégié (inférieur à 1024) dans la plage sélectionnée.")

        st.markdown("---")

        # ── SECTION 8 : DONNÉES BRUTES ───────────────────────────────
        section_header("📄", "Exploration des Données Brutes",
                       "Filtrage et téléchargement des logs avec renderDataTable", "icon-purple")

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_protocol_raw = st.multiselect(
                "Filtrer par protocole",
                options=df['protocol'].unique(),
                default=df['protocol'].unique(),
                key="raw_protocol_filter"
            )
        with col2:
            filter_action = st.multiselect(
                "Filtrer par action",
                options=df['action'].unique(),
                default=df['action'].unique(),
                key="raw_action_filter"
            )
        with col3:
            n_rows = st.slider("Nombre de lignes à afficher", 10, 1000, 100)

        final_filtered_df = df[
            (df['protocol'].isin(filter_protocol_raw)) &
            (df['action'].isin(filter_action))
        ].head(n_rows)

        st.dataframe(final_filtered_df, use_container_width=True)

        csv = final_filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les données filtrées (CSV)",
            data=csv,
            file_name="logs_filtres.csv",
            mime="text/csv"
        )

    except FileNotFoundError:
        st.error("❌ Fichier data_exm.csv introuvable. Vérifiez que le dossier `data/` est bien présent.")
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données : {str(e)}")

if __name__ == "__main__":
    show()