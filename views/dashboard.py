# views/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

@st.cache_data
def load_data():
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data_exm.csv')
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    df['hour'] = df['date'].dt.hour
    df['day'] = df['date'].dt.date
    return df


def get_port_category(port):
    """Categorize ports according to RFC 6056"""
    if port < 1024:
        return "System Ports (0-1023)"
    elif port < 49152:
        return "User Ports (1024-49151)"
    else:
        return "Dynamic Ports (49152-65535)"
        

def show():
    st.title("📊 Dashboard Descriptif - Analyse des Flux Réseau")
    st.write("")

    # Load data
    try:
        df = load_data()
        df['port_category'] = df['dest_port'].apply(get_port_category)
        
        st.write("")
        st.header("🚦 Analyse des Flux") 
        st.write("")
       

        # Metrics overview
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            with st.container(border=True):
                st.metric("Total Flux", f"{len(df):,}")
        with col2:
            with st.container(border=True):
                st.metric("IP Sources Uniques", df['ip_source'].nunique())
        with col3:
            with st.container(border=True):
                st.metric("Ports Distincts", df['dest_port'].nunique())
        with col4:
            with st.container(border=True):
                blocked = len(df[df['action'] == 'Deny'])
                st.metric("Flux Bloqués", blocked)
                
        

        filter_col1, filter_col2 = st.columns(2)

        with filter_col1:
            filter_protocol = st.multiselect(
                "Filtrer par protocole:", 
                options=df['protocol'].unique(),
                default=df['protocol'].unique()
            )

        with filter_col2:
            port_range = st.selectbox(
                "Sélectionner une plage de ports:",
                ["Tous les ports", 
                "System Ports (0-1023)", 
                "User Ports (1024-49151)", 
                "Dynamic Ports (49152-65535)",
                "Plage personnalisée"]
            )

        min_port = 0
        max_port = 65535
        if port_range == "Plage personnalisée":
            port_col1, port_col2 = st.columns(2)
            with port_col1:
                min_port = st.number_input("Port min:", 0, 65535, 0)
            with port_col2:
                max_port = st.number_input("Port max:", 0, 65535, 65535)

        # Apply filters
        filtered_df = df[df['protocol'].isin(filter_protocol)].copy()

        if port_range == "System Ports (0-1023)":
            filtered_df = filtered_df[filtered_df['dest_port'] < 1024]
        elif port_range == "User Ports (1024-49151)":
            filtered_df = filtered_df[(filtered_df['dest_port'] >= 1024) & (filtered_df['dest_port'] < 49152)]
        elif port_range == "Dynamic Ports (49152-65535)":
            filtered_df = filtered_df[filtered_df['dest_port'] >= 49152]
        elif port_range == "Plage personnalisée":
            filtered_df = filtered_df[(filtered_df['dest_port'] >= min_port) & (filtered_df['dest_port'] <= max_port)]

        # ========== Bar Chart + Line Chart in Container ==========
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])

            # ========== COLUMN 1: Bar Chart (Protocol Comparison) ==========
            with col1:
                protocol_action = pd.crosstab(filtered_df['protocol'], filtered_df['action'])
                fig_protocol_action = go.Figure()
                
                if 'Permit' in protocol_action.columns:
                    fig_protocol_action.add_trace(go.Bar(
                        name='Autorisé (Permit)',
                        x=protocol_action.index,
                        y=protocol_action['Permit'],
                        marker_color='#00CC66'
                    ))
                
                if 'Deny' in protocol_action.columns:
                    fig_protocol_action.add_trace(go.Bar(
                        name='Rejeté (Deny)',
                        x=protocol_action.index,
                        y=protocol_action['Deny'],
                        marker_color='#FF4444'
                    ))
                
                fig_protocol_action.update_layout(
                    title='Flux Autorisés vs Rejetés par Protocole',
                    barmode='group',
                    xaxis_title='Protocole',
                    yaxis_title='Nombre de flux',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=500
                )
                st.plotly_chart(fig_protocol_action, use_container_width=True)

            # ========== COLUMN 2: Line Chart (Traffic Over Time) ==========
            with col2:
                def categorize_port(port):
                    if port < 1024:
                        return 'System Ports (0-1023)'
                    elif port < 49152:
                        return 'User Ports (1024-49151)'
                    else:
                        return 'Dynamic Ports (49152-65535)'
                
                filtered_df['port_category'] = filtered_df['dest_port'].apply(categorize_port)
                
                daily_data = filtered_df.groupby([filtered_df['date'].dt.date, 'port_category']).size().reset_index(name='count')
                daily_data.columns = ['date', 'port_category', 'count']
                
                min_date = filtered_df['date'].min()
                max_date = filtered_df['date'].max()
                date_range_days = (max_date - min_date).days
                
                fig_time = go.Figure()
                
                for category in daily_data['port_category'].unique():
                    category_data = daily_data[daily_data['port_category'] == category]
                    fig_time.add_trace(go.Scatter(
                        x=category_data['date'],
                        y=category_data['count'],
                        mode='lines+markers',
                        name=category,
                        line=dict(width=3),
                        marker=dict(size=4)
                    ))
                
                # Dynamic range selector buttons based on data length
                buttons = []
                
                if date_range_days >= 7:
                    buttons.append(dict(count=7, label="1 semaine", step="day", stepmode="backward"))
                if date_range_days >= 14:
                    buttons.append(dict(count=14, label="2 semaines", step="day", stepmode="backward"))
                if date_range_days >= 30:
                    buttons.append(dict(count=1, label="1 mois", step="month", stepmode="backward"))
                if date_range_days >= 60:
                    buttons.append(dict(count=2, label="2 mois", step="month", stepmode="backward"))
                
                buttons.append(dict(step="all", label="Tout"))
                
                fig_time.update_layout(
                    title='Volume de Trafic dans le Temps',
                    xaxis_title='Date',
                    yaxis_title='Nombre de flux',
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=500,
                    xaxis=dict(
                        rangeselector=dict(buttons=buttons),
                        rangeslider=dict(visible=True),
                        type="date"
                    )
                )
                st.plotly_chart(fig_time, use_container_width=True)

        
        st.divider()
        
        # === TCP vs UDP DETAILED COMPARISON ===
        st.header("📡 Comparaison Détaillée TCP vs UDP")

        tcp_data = filtered_df[filtered_df['protocol'] == 'TCP']
        udp_data = filtered_df[filtered_df['protocol'] == 'UDP']

        # One big container with border
        with st.container(border=True):
            # Metrics row
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🔵 TCP")
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Total", f"{len(tcp_data):,}")
                with metric_col2:
                    tcp_blocked = len(tcp_data[tcp_data['action'] == 'Deny'])
                    tcp_block_rate = (tcp_blocked / len(tcp_data) * 100) if len(tcp_data) > 0 else 0
                    st.metric("Bloqués", f"{tcp_blocked:,}", f"{tcp_block_rate:.1f}%")

            with col2:
                st.markdown("### 🟢 UDP")
                metric_col1, metric_col2 = st.columns(2)
                with metric_col1:
                    st.metric("Total", f"{len(udp_data):,}")
                with metric_col2:
                    udp_blocked = len(udp_data[udp_data['action'] == 'Deny'])
                    udp_block_rate = (udp_blocked / len(udp_data) * 100) if len(udp_data) > 0 else 0
                    st.metric("Bloqués", f"{udp_blocked:,}", f"{udp_block_rate:.1f}%")
            
            # Charts row
            col1, col2 = st.columns(2)
            
            with col1:
                if len(tcp_data) > 0:
                    top_tcp = tcp_data['dest_port'].value_counts().head(5).reset_index()
                    top_tcp.columns = ['Port', 'Count']
                    top_tcp['Port'] = top_tcp['Port'].astype(str)
                    top_tcp = top_tcp.sort_values('Count', ascending=True)
                    
                    fig_tcp = px.bar(top_tcp, 
                                x='Count', 
                                y='Port', 
                                orientation='h',
                                title="Top 5 Ports TCP",
                                color='Count', 
                                color_continuous_scale='Blues')
                    
                    fig_tcp.update_layout(yaxis_type='category', height=400, coloraxis_showscale=False)
                    st.plotly_chart(fig_tcp, use_container_width=True)
                else:
                    st.info("Aucune donnée TCP")

            with col2:
                if len(udp_data) > 0:
                    top_udp = udp_data['dest_port'].value_counts().head(5).reset_index()
                    top_udp.columns = ['Port', 'Count']
                    top_udp['Port'] = top_udp['Port'].astype(str)
                    top_udp = top_udp.sort_values('Count', ascending=True)
                    
                    fig_udp = px.bar(top_udp, 
                                x='Count', 
                                y='Port', 
                                orientation='h',
                                title="Top 5 Ports UDP",
                                color='Count', 
                                color_continuous_scale='Greens')
                    
                    fig_udp.update_layout(yaxis_type='category', height=400, coloraxis_showscale=False)
                    st.plotly_chart(fig_udp, use_container_width=True)
                else:
                    st.info("Aucune donnée UDP")
        
        st.divider()
        
        # === PORT DISTRIBUTION BY RFC 6056 CATEGORIES ===
        st.header("📊 Distribution des Ports selon RFC 6056")
        with st.container(border=True):
            port_cat_dist = filtered_df['port_category'].value_counts().reset_index()
            port_cat_dist.columns = ['Catégorie', 'Nombre de flux']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_port_cat = px.pie(port_cat_dist, 
                                    values='Nombre de flux', 
                                    names='Catégorie',
                                    title="Répartition par catégorie de ports",
                                    color_discrete_sequence=px.colors.sequential.Plasma)
                
                fig_port_cat.update_traces(
                    textposition='inside',
                    textinfo='label+value',
                    showlegend=False
                )
                
                st.plotly_chart(fig_port_cat, use_container_width=True)
            
            with col2:
                # Port categories with action breakdown
                port_cat_action = pd.crosstab(filtered_df['port_category'], filtered_df['action'])
                
                fig_port_cat_action = go.Figure()
                if 'Permit' in port_cat_action.columns:
                    fig_port_cat_action.add_trace(go.Bar(
                        name='Autorisé',
                        y=port_cat_action.index,
                        x=port_cat_action['Permit'],
                        orientation='h',
                        marker_color='#00CC66'
                    ))
                if 'Deny' in port_cat_action.columns:
                    fig_port_cat_action.add_trace(go.Bar(
                        name='Rejeté',
                        y=port_cat_action.index,
                        x=port_cat_action['Deny'],
                        orientation='h',
                        marker_color='#FF4444'
                    ))
                
                fig_port_cat_action.update_layout(
                    title='Autorisés vs Rejetés par Catégorie',
                    barmode='stack',
                    xaxis_title='Nombre de flux'
                )
                st.plotly_chart(fig_port_cat_action, use_container_width=True)
        
        st.divider()
        
        # === TOP 5 IP SOURCES ===
        st.header("🔝 IP Sources")
        
        with st.container(border=True):
            top_ips = filtered_df['ip_source'].value_counts().head(5).reset_index()
            top_ips.columns = ['IP Source', 'Nombre de connexions']

            col1, col2 = st.columns(2)

            with col1:
                # Bar chart
                fig_ips = px.bar(top_ips, 
                                x='IP Source', 
                                y='Nombre de connexions',
                                color='Nombre de connexions',
                                color_continuous_scale='Blues',
                                title="Top 5 des IP sources les plus actives")
                st.plotly_chart(fig_ips, use_container_width=True)

            with col2:
                ip_bubble_data = filtered_df.groupby('ip_source').agg({
                    'ip_destination': 'nunique',
                }).reset_index()
                ip_bubble_data.columns = ['IP Source', 'Nb Destinations Contactées']
                
                rejected_flows = filtered_df.groupby('ip_source').apply(
                    lambda x: (x['action'] == 'Deny').sum()
                ).reset_index(name='Flux Rejetés')
                
                allowed_flows = filtered_df.groupby('ip_source').apply(
                    lambda x: (x['action'] == 'Permit').sum()
                ).reset_index(name='Flux Autorisés')
                
                ip_bubble_data = ip_bubble_data.merge(rejected_flows, left_on='IP Source', right_on='ip_source', how='left')
                ip_bubble_data = ip_bubble_data.merge(allowed_flows, left_on='IP Source', right_on='ip_source', how='left')
                ip_bubble_data = ip_bubble_data[['IP Source', 'Nb Destinations Contactées', 'Flux Rejetés', 'Flux Autorisés']]
                ip_bubble_data['Total Flux'] = ip_bubble_data['Flux Rejetés'] + ip_bubble_data['Flux Autorisés']
                
                fig_scatter = px.scatter(ip_bubble_data, 
                                        x='Nb Destinations Contactées',
                                        y='Flux Rejetés',
                                        size='Total Flux',
                                        color='Flux Autorisés',
                                        hover_data=['IP Source', 'Flux Autorisés', 'Flux Rejetés', 'Total Flux'],
                                        title="Destinations Contactées vs Flux Rejetés",
                                        labels={
                                            'Nb Destinations Contactées': 'Nombre de destinations contactées',
                                            'Flux Rejetés': 'Nombre de flux rejetés'
                                        },
                                        color_continuous_scale='Greens',
                                        size_max=60)
                
                fig_scatter.update_traces(marker=dict(line=dict(width=1, color='DarkSlateGrey')))
                st.plotly_chart(fig_scatter, use_container_width=True)

            with st.expander("📋 Voir les détails"):
                st.dataframe(top_ips, use_container_width=True)
                
        st.divider()
        
        # === TOP 10 PORTS < 1024 ===
        st.header("🔌 Top 10 Ports Privilégiés (< 1024)")
        
        ports_privileged = filtered_df[filtered_df['dest_port'] < 1024]
        
        if len(ports_privileged) > 0:
            with st.container(border=True):
                top_ports = ports_privileged['dest_port'].value_counts().head(10).reset_index()
                top_ports.columns = ['Port', 'Nombre de connexions']
                
                # Add common port names
                port_names = {
                    20: 'FTP-Data', 21: 'FTP', 22: 'SSH', 23: 'Telnet',
                    25: 'SMTP', 53: 'DNS', 80: 'HTTP', 110: 'POP3',
                    143: 'IMAP', 443: 'HTTPS', 445: 'SMB', 3306: 'MySQL',
                    3389: 'RDP', 8080: 'HTTP-Alt', 5432: 'PostgreSQL', 27017: 'MongoDB'
                }
                top_ports['Service'] = top_ports['Port'].map(port_names).fillna('Autre')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_ports = px.pie(top_ports, 
                                    values='Nombre de connexions', 
                                    names='Port',
                                    title="Répartition des ports privilégiés",
                                    hole=0.4)

                    fig_ports.update_traces(
                        textposition='inside',
                        textinfo='label+value',
                        showlegend=False
                    )

                    st.plotly_chart(fig_ports, use_container_width=True)
                
                with col2:
                    top_ports['Port'] = top_ports['Port'].astype(str)
                    top_ports = top_ports.sort_values('Nombre de connexions', ascending=False)

                    fig_ports_bar = px.bar(top_ports, 
                                        x='Port', 
                                        y='Nombre de connexions',
                                        color='Service',
                                        title="Volume par port")
                    
                    fig_ports_bar.update_xaxes(
                        type='category',
                        categoryorder='array',
                        categoryarray=top_ports['Port'].tolist()
                    )
                    
                    st.plotly_chart(fig_ports_bar, use_container_width=True)
                
                with st.expander("📋 Voir les détails"):
                    st.dataframe(top_ports, use_container_width=True)
        else:
            st.info("Aucun port privilégié (< 1024) dans la plage sélectionnée")
        
        st.divider()
        
        
        # === RAW DATA ===
        st.header("📄 Données Brutes")

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_protocol_raw = st.multiselect("Filtrer par protocole:", 
                                                options=df['protocol'].unique(),  
                                                default=df['protocol'].unique(),  
                                                key="raw_protocol_filter")  
        with col2:
            filter_action = st.multiselect("Filtrer par action:", 
                                        options=df['action'].unique(), 
                                        default=df['action'].unique(),  
                                        key="raw_action_filter")  
        with col3:
            n_rows = st.slider("Nombre de lignes:", 10, 1000, 100)

        final_filtered_df = df[  
            (df['protocol'].isin(filter_protocol_raw)) &  
            (df['action'].isin(filter_action))  
        ].head(n_rows)
        
        st.dataframe(final_filtered_df, use_container_width=True)
        
        # Download button
        csv = final_filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les données filtrées (CSV)",
            data=csv,
            file_name="logs_filtres.csv",
            mime="text/csv"
        )

    except FileNotFoundError:
        st.error("❌ Fichier data_exm.csv introuvable. Vérifiez le chemin du fichier.")
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {str(e)}")

# For standalone testing
if __name__ == "__main__":
    show()