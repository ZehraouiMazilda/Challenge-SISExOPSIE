import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import LocalOutlierFactor
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.cluster import KMeans
from sklearn.metrics import (
    confusion_matrix, classification_report, roc_curve, auc,
    ConfusionMatrixDisplay, silhouette_score
)
from sklearn.pipeline import Pipeline

import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# STYLES GLOBAUX
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

/* Reset Streamlit */
.stApp { background-color: var(--bg-dark) !important; }
section[data-testid="stSidebar"] { background-color: #080c16 !important; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 3rem !important; }

/* Typographie */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}

/* En-têtes */
h1, h2, h3, h4 { font-family: 'Space Mono', monospace !important; }

/* Hero banner */
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
    top: -50%;
    right: -10%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
    pointer-events: none;
}
.ml-hero h1 {
    font-size: 1.8rem;
    color: var(--accent) !important;
    margin: 0 0 0.5rem 0;
    letter-spacing: -1px;
}
.ml-hero p {
    color: var(--text-dim);
    font-size: 0.95rem;
    margin: 0;
    max-width: 700px;
    line-height: 1.7;
}

/* Carte de section */
.section-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
}
.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid var(--border);
}
.section-icon {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.icon-blue  { background: rgba(0,212,255,0.12); }
.icon-red   { background: rgba(255,77,109,0.12); }
.icon-purple{ background: rgba(123,97,255,0.12); }
.icon-green { background: rgba(16,185,129,0.12); }
.icon-orange{ background: rgba(245,158,11,0.12); }
.section-title {
    font-family: 'Space Mono', monospace !important;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text) !important;
    margin: 0;
}
.section-subtitle {
    font-size: 0.8rem;
    color: var(--text-dim);
    margin: 0;
}

/* Métriques */
.metrics-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1.2rem 0;
}
.metric-box {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    text-align: center;
}
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent);
    display: block;
}
.metric-label {
    font-size: 0.72rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
}
.metric-box.red   .metric-value { color: var(--accent2); }
.metric-box.purple .metric-value { color: var(--accent3); }
.metric-box.green  .metric-value { color: var(--success); }

/* Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.7rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-info    { background: rgba(0,212,255,0.15); color: var(--accent); border: 1px solid rgba(0,212,255,0.3); }
.badge-danger  { background: rgba(255,77,109,0.15); color: var(--accent2); border: 1px solid rgba(255,77,109,0.3); }
.badge-success { background: rgba(16,185,129,0.15); color: var(--success); border: 1px solid rgba(16,185,129,0.3); }

/* Tableau de bord navigation */
.nav-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

/* Info box custom */
.info-box {
    background: rgba(0,212,255,0.06);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    font-size: 0.85rem;
    color: var(--text-dim);
    line-height: 1.6;
    margin: 0.8rem 0;
}
.warn-box {
    background: rgba(245,158,11,0.06);
    border-left: 3px solid var(--warning);
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    font-size: 0.85rem;
    color: var(--text-dim);
    line-height: 1.6;
    margin: 0.8rem 0;
}
.success-box {
    background: rgba(16,185,129,0.06);
    border-left: 3px solid var(--success);
    border-radius: 0 8px 8px 0;
    padding: 0.9rem 1.2rem;
    font-size: 0.85rem;
    color: var(--text-dim);
    line-height: 1.6;
    margin: 0.8rem 0;
}

/* Streamlit overrides */
.stSelectbox label, .stSlider label, .stRadio label,
.stMultiSelect label, .stNumberInput label {
    color: var(--text-dim) !important;
    font-size: 0.82rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    background-color: var(--bg-card2) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
}
.stDataFrame { background: var(--bg-card2) !important; }
.stAlert { border-radius: 8px !important; }

/* Séparateur */
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

/* Code block */
pre { background: #0d1321 !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
</style>
"""

# ─────────────────────────────────────────────
# HELPERS UI
# ─────────────────────────────────────────────
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

def info_box(text): st.markdown(f'<div class="info-box">ℹ️ {text}</div>', unsafe_allow_html=True)
def warn_box(text): st.markdown(f'<div class="warn-box">⚠️ {text}</div>', unsafe_allow_html=True)
def success_box(text): st.markdown(f'<div class="success-box">✅ {text}</div>', unsafe_allow_html=True)

def metrics_row(items):
    cols = st.columns(len(items))
    for col, (label, value, cls) in zip(cols, items):
        col.markdown(f"""
        <div class="metric-box {cls}">
            <span class="metric-value">{value}</span>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

PLOTLY_TEMPLATE = dict(
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font=dict(color="#e2e8f0", family="DM Sans"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True),
    margin=dict(t=40, b=40, l=40, r=20),
    colorway=["#00d4ff", "#ff4d6d", "#7b61ff", "#10b981", "#f59e0b"],
)

def styled_fig(fig):
    fig.update_layout(**PLOTLY_TEMPLATE)
    return fig

# ─────────────────────────────────────────────
# CHARGEMENT ET PRÉPARATION DES DONNÉES
# ─────────────────────────────────────────────
@st.cache_data
def charger_donnees():
    df = pd.read_csv("data/data_exm.csv")
    df = df.rename(columns={
        'date': 'Date',
        'ip_source': 'Adresse_IP_Source',
        'ip_destination': 'Adresse_IP_Destination',
        'protocol': 'Protocole',
        'dest_port': 'Port_Destination',
        'action': 'Action',
        'rule_id': 'Identifiant_Regle',
        'interface_in': 'Interface_Entree',
        'interface_out': 'Interface_Sortie'
    })
    df['Date'] = pd.to_datetime(df['Date'])
    df['Heure']  = df['Date'].dt.hour
    df['Jour_Semaine'] = df['Date'].dt.dayofweek
    df['Est_Rejet'] = (df['Action'] == 'Deny').astype(int)
    df['Est_TCP']   = (df['Protocole'] == 'TCP').astype(int)
    return df

@st.cache_data
def construire_features_comportementales(df):
    groupes = df.groupby('Adresse_IP_Source')
    features = groupes.agg(
        Nombre_Ports_Distincts=('Port_Destination', 'nunique'),
        Nombre_Rejets=('Action', lambda x: (x == 'Deny').sum()),
        Nombre_Connexions=('Date', 'count'),
        Duree_Minutes=('Date', lambda x: max((x.max() - x.min()).total_seconds() / 60, 1)),
        Port_Moyen=('Port_Destination', 'mean'),
        Port_Max=('Port_Destination', 'max'),
        Ratio_TCP=('Est_TCP', 'mean'),
    ).reset_index()
    features['Vitesse_Connexion_Par_Minute'] = features['Nombre_Connexions'] / features['Duree_Minutes']
    features['Ratio_Rejet'] = features['Nombre_Rejets'] / features['Nombre_Connexions']
    return features

# ─────────────────────────────────────────────
# ONGLET 1 : INGÉNIERIE DES DESCRIPTEURS
# ─────────────────────────────────────────────
def onglet_feature_engineering(df, features):
    section_header("🔬", "Ingénierie des Descripteurs Comportementaux",
                   "Construction des variables prédictives à partir des logs bruts", "icon-blue")

    info_box("""
    Chaque adresse IP source est résumée par un vecteur de descripteurs calculés à partir 
    de l'ensemble de ses connexions. Cette agrégation transforme des logs bruts en profils 
    comportementaux exploitables par les modèles d'apprentissage automatique.
    """)

    col1, col2 = st.columns([1.4, 1])
    with col1:
        st.markdown("**Extrait des profils comportementaux calculés**")
        st.dataframe(
            features.head(10).style.format({
                'Nombre_Ports_Distincts': '{:.0f}',
                'Nombre_Rejets': '{:.0f}',
                'Nombre_Connexions': '{:.0f}',
                'Vitesse_Connexion_Par_Minute': '{:.2f}',
                'Ratio_Rejet': '{:.2%}',
                'Ratio_TCP': '{:.2%}',
            }),
            use_container_width=True, height=280
        )
    with col2:
        st.markdown("**Description des descripteurs construits**")
        descripteurs = {
            "Nombre de ports distincts": "Diversité des ports contactés — révèle un balayage de ports",
            "Nombre de rejets": "Volume de connexions bloquées par le pare-feu",
            "Vitesse de connexion (connexions/min)": "Fréquence d'activité — taux élevé = comportement automatisé",
            "Ratio de rejet": "Proportion de trafic bloqué — indicateur de malveillance",
            "Ratio TCP": "Part du protocole TCP — utile pour distinguer les profils",
            "Port maximal contacté": "Port le plus élevé — balayage total = port 65535",
        }
        for d, e in descripteurs.items():
            st.markdown(f"- **{d}** : {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    metrics_row([
        ("Adresses IP analysées", f"{len(features):,}", ""),
        ("Descripteurs construits", "8", "purple"),
        ("Connexions totales", f"{len(df):,}", "green"),
        ("Taux de rejet global", f"{df['Est_Rejet'].mean():.1%}", "red"),
    ])

# ─────────────────────────────────────────────
# ONGLET 2 : ISOLATION FOREST
# ─────────────────────────────────────────────
def onglet_isolation_forest(features):
    section_header("🌲", "Détection d'Anomalies — Isolation Forest",
                   "Apprentissage non supervisé : isolation rapide des points aberrants", "icon-red")

    info_box("""
    L'Isolation Forest construit une multitude d'arbres aléatoires. L'hypothèse fondamentale est 
    qu'une anomalie est plus "facile à isoler" : elle sera séparée du reste en beaucoup moins 
    de divisions que les points normaux. Un score d'anomalie proche de 1 indique une anomalie probable.
    """)

    cols_entrainement = ['Nombre_Ports_Distincts', 'Nombre_Rejets',
                          'Vitesse_Connexion_Par_Minute', 'Ratio_Rejet', 'Ratio_TCP']

    scaler = StandardScaler()
    X_reduit = scaler.fit_transform(features[cols_entrainement])

    col_param1, col_param2 = st.columns(2)
    with col_param1:
        contamination = st.slider(
            "Taux de contamination attendu (proportion d'anomalies)",
            min_value=0.01, max_value=0.20, value=0.05, step=0.01,
            help="Correspond au paramètre 'contamination' de l'Isolation Forest"
        )
    with col_param2:
        nombre_arbres = st.slider(
            "Nombre d'arbres dans la forêt",
            min_value=50, max_value=500, value=100, step=50
        )

    modele = IsolationForest(
        contamination=contamination,
        n_estimators=nombre_arbres,
        random_state=42
    )
    features = features.copy()
    features['Score_Anomalie_Brut'] = modele.fit(X_reduit).score_samples(X_reduit)
    features['Prediction'] = modele.fit_predict(X_reduit)
    features['Statut'] = features['Prediction'].map({1: 'Normal', -1: 'Suspect'})

    nb_suspects = (features['Statut'] == 'Suspect').sum()
    nb_normaux  = (features['Statut'] == 'Normal').sum()

    metrics_row([
        ("Adresses IP normales", f"{nb_normaux}", "green"),
        ("Adresses IP suspectes", f"{nb_suspects}", "red"),
        ("Taux de détection", f"{nb_suspects/len(features):.1%}", ""),
        ("Arbres utilisés", f"{nombre_arbres}", "purple"),
    ])

    # Graphique distribution des scores
    fig_score = go.Figure()
    for statut, couleur in [("Normal", "#00d4ff"), ("Suspect", "#ff4d6d")]:
        sous_df = features[features['Statut'] == statut]
        fig_score.add_trace(go.Histogram(
            x=sous_df['Score_Anomalie_Brut'],
            name=statut, opacity=0.75,
            marker_color=couleur, nbinsx=40
        ))
    fig_score.update_layout(
        **PLOTLY_TEMPLATE,
        title="Distribution des scores d'anomalie par statut",
        xaxis_title="Score d'anomalie (plus négatif = plus suspect)",
        yaxis_title="Nombre d'adresses IP",
        barmode='overlay', height=320
    )
    st.plotly_chart(fig_score, use_container_width=True)

    st.markdown("**Tableau des adresses IP les plus suspectes**")
    top_suspects = (
        features[features['Statut'] == 'Suspect']
        .sort_values('Score_Anomalie_Brut')
        [['Adresse_IP_Source', 'Nombre_Ports_Distincts', 'Vitesse_Connexion_Par_Minute',
          'Ratio_Rejet', 'Nombre_Rejets', 'Score_Anomalie_Brut']]
        .head(15)
    )
    st.dataframe(top_suspects.style.format({
        'Vitesse_Connexion_Par_Minute': '{:.2f}',
        'Ratio_Rejet': '{:.2%}',
        'Score_Anomalie_Brut': '{:.4f}',
    }), use_container_width=True)

    return features  # on retourne avec les colonnes Statut

# ─────────────────────────────────────────────
# ONGLET 3 : LOF
# ─────────────────────────────────────────────
def onglet_lof(features):
    section_header("📡", "Détection d'Anomalies — Local Outlier Factor (LOF)",
                   "Détection par densité locale : les anomalies vivent dans des zones peu denses", "icon-orange")

    info_box("""
    Le Local Outlier Factor (LOF) compare la densité locale de chaque point à celle de ses 
    k plus proches voisins. Un score LOF >> 1 indique que le point se trouve dans une zone 
    beaucoup moins dense que son entourage — signe probable d'une anomalie.
    """)

    cols_entrainement = ['Nombre_Ports_Distincts', 'Nombre_Rejets',
                          'Vitesse_Connexion_Par_Minute', 'Ratio_Rejet']

    scaler = StandardScaler()
    X_reduit = scaler.fit_transform(features[cols_entrainement])

    col1, col2 = st.columns(2)
    with col1:
        k_voisins = st.slider("Nombre de voisins (k)", min_value=5, max_value=50, value=20)
    with col2:
        contamination_lof = st.slider("Taux de contamination LOF", 0.01, 0.20, 0.05, 0.01)

    features = features.copy()
    lof = LocalOutlierFactor(n_neighbors=k_voisins, contamination=contamination_lof)
    predictions_lof = lof.fit_predict(X_reduit)
    features['Score_LOF'] = -lof.negative_outlier_factor_
    features['Statut_LOF'] = predictions_lof

    # Courbe des scores triés pour trouver le "coude"
    scores_tries = np.sort(features['Score_LOF'].values)[::-1]
    fig_coude = go.Figure()
    fig_coude.add_trace(go.Scatter(
        y=scores_tries, mode='lines',
        line=dict(color='#00d4ff', width=2),
        fill='tozeroy', fillcolor='rgba(0,212,255,0.05)',
        name='Score LOF'
    ))
    fig_coude.add_hline(y=features['Score_LOF'].quantile(0.95),
                         line=dict(color='#ff4d6d', dash='dash', width=1.5),
                         annotation_text="Seuil 95e percentile")
    fig_coude.update_layout(
        **PLOTLY_TEMPLATE,
        title="Courbe des scores LOF triés (recherche du « coude »)",
        xaxis_title="Rang de l'adresse IP",
        yaxis_title="Score LOF",
        height=300
    )
    st.plotly_chart(fig_coude, use_container_width=True)

    nb_lof = (features['Statut_LOF'] == -1).sum()
    metrics_row([
        ("Anomalies LOF détectées", f"{nb_lof}", "red"),
        ("k voisins utilisés", f"{k_voisins}", "purple"),
        ("Score LOF maximum", f"{features['Score_LOF'].max():.2f}", ""),
        ("Score LOF médian", f"{features['Score_LOF'].median():.2f}", "green"),
    ])

    return features

# ─────────────────────────────────────────────
# ONGLET 4 : ACP
# ─────────────────────────────────────────────
def onglet_acp(features):
    section_header("🔭", "Visualisation Factorielle — Analyse en Composantes Principales",
                   "Réduction de dimension pour valider visuellement les anomalies détectées", "icon-purple")

    info_box("""
    L'ACP projette les données dans un espace de dimension réduite en maximisant la variance 
    expliquée. Elle est utilisée ici comme outil de diagnostic visuel : si les anomalies détectées 
    se démarquent nettement du nuage central, cela valide la qualité de notre détection.
    """)

    cols_acp = ['Nombre_Ports_Distincts', 'Nombre_Rejets',
                 'Vitesse_Connexion_Par_Minute', 'Ratio_Rejet', 'Ratio_TCP']

    scaler = StandardScaler()
    X_reduit = scaler.fit_transform(features[cols_acp])

    acp = PCA(n_components=min(len(cols_acp), 4))
    composantes = acp.fit_transform(X_reduit)

    features = features.copy()
    features['Composante_1'] = composantes[:, 0]
    features['Composante_2'] = composantes[:, 1]

    variance_expliquee = acp.explained_variance_ratio_
    variance_cumulee   = np.cumsum(variance_expliquee)

    col1, col2 = st.columns([2, 1])
    with col1:
        couleur_col = 'Statut' if 'Statut' in features.columns else 'Ratio_Rejet'
        couleur_map = {'Normal': '#00d4ff', 'Suspect': '#ff4d6d'} if couleur_col == 'Statut' else None

        fig_acp = px.scatter(
            features, x='Composante_1', y='Composante_2',
            color=couleur_col,
            color_discrete_map=couleur_map,
            hover_data=['Adresse_IP_Source', 'Vitesse_Connexion_Par_Minute',
                        'Nombre_Ports_Distincts', 'Ratio_Rejet'],
            title="Plan factoriel ACP — Axes 1 et 2",
            opacity=0.75, size_max=8
        )
        fig_acp.update_traces(marker=dict(size=6))
        fig_acp.update_layout(
            **PLOTLY_TEMPLATE,
            xaxis_title=f"Composante 1 ({variance_expliquee[0]:.1%} de variance)",
            yaxis_title=f"Composante 2 ({variance_expliquee[1]:.1%} de variance)",
            height=400
        )
        st.plotly_chart(fig_acp, use_container_width=True)

    with col2:
        st.markdown("**Variance expliquée par composante**")
        fig_var = go.Figure(go.Bar(
            x=[f"Axe {i+1}" for i in range(len(variance_expliquee))],
            y=variance_expliquee,
            marker_color=['#00d4ff', '#7b61ff', '#ff4d6d', '#10b981'][:len(variance_expliquee)],
            text=[f"{v:.1%}" for v in variance_expliquee],
            textposition='outside'
        ))
        fig_var.add_trace(go.Scatter(
            x=[f"Axe {i+1}" for i in range(len(variance_expliquee))],
            y=variance_cumulee,
            mode='lines+markers',
            name='Variance cumulée',
            line=dict(color='#f59e0b', width=2),
            yaxis='y2'
        ))
        template_var = {k: v for k, v in PLOTLY_TEMPLATE.items() if k != 'yaxis'}
        fig_var.update_layout(
            **template_var,
            title="Éboulis des valeurs propres",
            yaxis=dict(title="Variance expliquée", tickformat='.0%',
                       gridcolor="rgba(255,255,255,0.05)", showgrid=True),
            yaxis2=dict(title="Cumulée", tickformat='.0%',
                        overlaying='y', side='right', gridcolor='rgba(0,0,0,0)'),
            height=350, showlegend=False
        )
        st.plotly_chart(fig_var, use_container_width=True)

        metrics_row([
            ("Variance axes 1+2", f"{variance_cumulee[1]:.1%}", "purple"),
        ])

    # Cercle des corrélations
    st.markdown("**Cercle des corrélations (contribution des variables aux axes)**")
    loadings = acp.components_[:2]
    fig_cercle = go.Figure()
    fig_cercle.add_shape(type="circle", x0=-1, y0=-1, x1=1, y1=1,
                          line=dict(color="rgba(255,255,255,0.1)", width=1))
    for i, nom in enumerate(cols_acp):
        fig_cercle.add_annotation(
            x=loadings[0, i], y=loadings[1, i],
            text=nom.replace('_', ' '), showarrow=True,
            arrowhead=2, arrowcolor='#00d4ff',
            ax=0, ay=0, font=dict(size=10, color='#e2e8f0')
        )
        fig_cercle.add_shape(type='line', x0=0, y0=0,
                              x1=loadings[0, i], y1=loadings[1, i],
                              line=dict(color='rgba(0,212,255,0.4)', width=1.5))
    template_cercle = {k: v for k, v in PLOTLY_TEMPLATE.items() if k not in ('xaxis', 'yaxis')}
    fig_cercle.update_layout(
        **template_cercle,
        xaxis=dict(range=[-1.1, 1.1], title=f"Axe 1 ({variance_expliquee[0]:.1%})",
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
                   gridcolor='rgba(255,255,255,0.05)', showgrid=True),
        yaxis=dict(range=[-1.1, 1.1], title=f"Axe 2 ({variance_expliquee[1]:.1%})",
                   zeroline=True, zerolinecolor='rgba(255,255,255,0.15)',
                   gridcolor='rgba(255,255,255,0.05)', showgrid=True),
        height=380, title="Cercle des corrélations"
    )
    st.plotly_chart(fig_cercle, use_container_width=True)
    return features

# ─────────────────────────────────────────────
# ONGLET 5 : K-MEANS
# ─────────────────────────────────────────────
def onglet_kmeans(features):
    section_header("🔵", "Classification Automatique — K-Means",
                   "Partitionnement non supervisé pour identifier des groupes de comportements homogènes", "icon-blue")

    info_box("""
    Le K-Means regroupe les adresses IP en clusters de comportements similaires sans utiliser 
    d'étiquettes. L'outil de la courbe d'inertie (méthode du coude) permet de choisir le nombre 
    optimal de groupes. Le coefficient de silhouette mesure la qualité de la partition obtenue.
    """)

    cols_kmeans = ['Nombre_Ports_Distincts', 'Nombre_Rejets',
                    'Vitesse_Connexion_Par_Minute', 'Ratio_Rejet']

    scaler = StandardScaler()
    X_reduit = scaler.fit_transform(features[cols_kmeans])

    # Recherche du K optimal (méthode du coude)
    k_max = st.slider("Nombre maximum de clusters à tester", 3, 12, 8)
    inerties, silhouettes = [], []
    plage_k = range(2, k_max + 1)
    for k in plage_k:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_reduit)
        inerties.append(km.inertia_)
        silhouettes.append(silhouette_score(X_reduit, labels))

    col1, col2 = st.columns(2)
    with col1:
        fig_inertie = go.Figure()
        fig_inertie.add_trace(go.Scatter(
            x=list(plage_k), y=inerties,
            mode='lines+markers',
            line=dict(color='#00d4ff', width=2),
            marker=dict(size=8, color='#7b61ff')
        ))
        fig_inertie.update_layout(
            **PLOTLY_TEMPLATE,
            title="Courbe d'inertie intra-classe (Méthode du coude)",
            xaxis_title="Nombre de clusters K",
            yaxis_title="Inertie intra-classe",
            height=280
        )
        st.plotly_chart(fig_inertie, use_container_width=True)

    with col2:
        fig_silhouette = go.Figure()
        fig_silhouette.add_trace(go.Bar(
            x=list(plage_k), y=silhouettes,
            marker_color=['#10b981' if s == max(silhouettes) else '#7b61ff' for s in silhouettes],
            text=[f"{s:.3f}" for s in silhouettes], textposition='outside'
        ))
        fig_silhouette.update_layout(
            **PLOTLY_TEMPLATE,
            title="Coefficient de silhouette par nombre de clusters",
            xaxis_title="Nombre de clusters K",
            yaxis_title="Coefficient de silhouette",
            height=280
        )
        st.plotly_chart(fig_silhouette, use_container_width=True)

    k_optimal = list(plage_k)[silhouettes.index(max(silhouettes))]
    k_choisi = st.number_input(
        f"Nombre de clusters retenu (K optimal suggéré : {k_optimal})",
        min_value=2, max_value=k_max, value=k_optimal
    )

    kmeans_final = KMeans(n_clusters=k_choisi, random_state=42, n_init=10)
    features = features.copy()
    features['Cluster'] = kmeans_final.fit_predict(X_reduit).astype(str)

    # Projection ACP pour visualiser les clusters
    acp_visu = PCA(n_components=2)
    coords = acp_visu.fit_transform(X_reduit)
    features['Axe_1'] = coords[:, 0]
    features['Axe_2'] = coords[:, 1]

    fig_clusters = px.scatter(
        features, x='Axe_1', y='Axe_2', color='Cluster',
        hover_data=['Adresse_IP_Source', 'Nombre_Ports_Distincts',
                    'Vitesse_Connexion_Par_Minute', 'Ratio_Rejet'],
        title=f"Partition K-Means ({k_choisi} clusters) — projection ACP",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    fig_clusters.update_traces(marker=dict(size=7, opacity=0.8))
    fig_clusters.update_layout(**PLOTLY_TEMPLATE, height=380)
    st.plotly_chart(fig_clusters, use_container_width=True)

    # Profil moyen des clusters
    st.markdown("**Profil moyen des clusters**")
    profil = (
        features.groupby('Cluster')[cols_kmeans]
        .mean()
        .round(3)
    )
    st.dataframe(profil, use_container_width=True)


# ─────────────────────────────────────────────
# ONGLET 6 : CLASSIFICATION SUPERVISÉE
# ─────────────────────────────────────────────
def onglet_classification_supervisee(df):
    section_header("🎯", "Classification Supervisée — Comparaison de Modèles",
                   "Régression logistique, Arbre CART, SVM et Forêt Aléatoire avec validation croisée", "icon-green")

    info_box("""
    Trois modèles classiques sont entraînés pour prédire si une connexion sera rejetée ou acceptée. 
    La validation croisée à 5 plis (Stratified K-Fold) garantit une évaluation robuste, non biaisée 
    par un découpage aléatoire unique. La courbe ROC mesure la capacité discriminante globale.
    """)

    # Préparation du jeu d'entraînement
    df_model = df.head(5000).copy()
    df_model['Est_TCP']     = (df_model['Protocole'] == 'TCP').astype(int)
    df_model['Tranche_Port'] = pd.cut(
        df_model['Port_Destination'],
        bins=[0, 1023, 49151, 65535],
        labels=[0, 1, 2]  # Bien connu / Enregistré / Dynamique (RFC 6056)
    ).astype(int)

    X = df_model[['Port_Destination', 'Est_TCP', 'Tranche_Port', 'Heure', 'Jour_Semaine']]
    y = df_model['Est_Rejet']

    if y.nunique() < 2:
        warn_box("Les données ne contiennent pas assez de variété dans la variable cible pour entraîner un modèle supervisé.")
        return

    scaler = StandardScaler()
    X_reduit = scaler.fit_transform(X)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    modeles = {
        "Régression Logistique (Lasso)": LogisticRegression(C=0.1, penalty='l1', solver='liblinear', max_iter=1000),
        "Régression Logistique (Ridge)": LogisticRegression(C=1.0, penalty='l2', max_iter=1000),
        "Arbre de Décision CART":        DecisionTreeClassifier(max_depth=4, random_state=42),
        "Forêt Aléatoire":               RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42),
    }

    resultats = []
    with st.spinner("Entraînement et validation croisée en cours..."):
        for nom, modele in modeles.items():
            scores_acc = cross_val_score(modele, X_reduit, y, cv=cv, scoring='accuracy')
            scores_auc = cross_val_score(modele, X_reduit, y, cv=cv, scoring='roc_auc')
            resultats.append({
                'Modèle': nom,
                'Précision moyenne': scores_acc.mean(),
                'Précision (écart-type)': scores_acc.std(),
                'AUC-ROC moyenne': scores_auc.mean(),
                'AUC-ROC (écart-type)': scores_auc.std(),
            })

    df_resultats = pd.DataFrame(resultats).sort_values('AUC-ROC moyenne', ascending=False)

    # Tableau de comparaison
    st.markdown("**Tableau comparatif des modèles (validation croisée 5 plis)**")
    st.dataframe(
        df_resultats.style.format({
            'Précision moyenne': '{:.3f}',
            'Précision (écart-type)': '± {:.3f}',
            'AUC-ROC moyenne': '{:.3f}',
            'AUC-ROC (écart-type)': '± {:.3f}',
        }),
        use_container_width=True
    )

    # Graphique des performances
    fig_perf = go.Figure()
    for metrique, couleur in [('Précision moyenne', '#00d4ff'), ('AUC-ROC moyenne', '#7b61ff')]:
        fig_perf.add_trace(go.Bar(
            name=metrique,
            x=df_resultats['Modèle'],
            y=df_resultats[metrique],
            marker_color=couleur,
            opacity=0.85,
            error_y=dict(
                type='data',
                array=df_resultats[metrique.replace('moyenne', '(écart-type)')].values,
                visible=True, color='rgba(255,255,255,0.4)'
            )
        ))
    fig_perf.update_layout(
        **{k: v for k, v in PLOTLY_TEMPLATE.items() if k not in ('yaxis')},
        title="Comparaison des performances (validation croisée 5 plis)",
        yaxis_title="Score",
        yaxis=dict(range=[0, 1]),
        barmode='group', height=340,
        xaxis_tickangle=-15
    )
    st.plotly_chart(fig_perf, use_container_width=True)

    # Courbes ROC
    st.markdown("**Courbes ROC — capacité discriminante de chaque modèle**")
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X_reduit, y, test_size=0.3, random_state=42, stratify=y
    )
    fig_roc = go.Figure()
    fig_roc.add_shape(type='line', x0=0, y0=0, x1=1, y1=1,
                       line=dict(color='rgba(255,255,255,0.2)', dash='dash'))
    couleurs_roc = ['#00d4ff', '#7b61ff', '#ff4d6d', '#10b981']
    for (nom, modele), couleur in zip(modeles.items(), couleurs_roc):
        modele.fit(X_train, y_train)
        if hasattr(modele, 'predict_proba'):
            proba = modele.predict_proba(X_test)[:, 1]
        else:
            proba = modele.decision_function(X_test)
        taux_fp, taux_vp, _ = roc_curve(y_test, proba)
        aire = auc(taux_fp, taux_vp)
        fig_roc.add_trace(go.Scatter(
            x=taux_fp, y=taux_vp, name=f"{nom} (AUC={aire:.3f})",
            mode='lines', line=dict(color=couleur, width=2)
        ))
    fig_roc.update_layout(
        **PLOTLY_TEMPLATE,
        title="Courbes ROC sur l'échantillon test (30%)",
        xaxis_title="Taux de faux positifs",
        yaxis_title="Taux de vrais positifs",
        height=380
    )
    st.plotly_chart(fig_roc, use_container_width=True)


# ─────────────────────────────────────────────
# ONGLET 7 : ARBRE DE DÉCISION + RÈGLES
# ─────────────────────────────────────────────
def onglet_arbre_regles(df):
    section_header("📋", "Extraction de Règles de Sécurité — Arbre CART",
                   "Interprétation humaine : transformation de l'arbre en règles de pare-feu actionnables", "icon-purple")

    info_box("""
    L'arbre de décision CART (Classification And Regression Tree) est particulièrement précieux 
    en cybersécurité car il produit des règles lisibles par un humain. Chaque chemin de la racine 
    vers une feuille correspond à une règle de filtrage potentielle.
    """)

    df_arbre = df.head(3000).copy()
    df_arbre['Est_TCP']     = (df_arbre['Protocole'] == 'TCP').astype(int)
    df_arbre['Tranche_Port'] = pd.cut(
        df_arbre['Port_Destination'],
        bins=[0, 1023, 49151, 65535],
        labels=[0, 1, 2]
    ).astype(int)

    X_arbre = df_arbre[['Port_Destination', 'Est_TCP', 'Tranche_Port', 'Heure']]
    y_arbre = (df_arbre['Action'] == 'Deny').astype(int)

    col1, col2 = st.columns(2)
    with col1:
        profondeur_max = st.slider("Profondeur maximale de l'arbre", 2, 6, 4)
    with col2:
        feuille_min = st.slider("Nombre minimum d'échantillons par feuille", 5, 100, 20)

    clf = DecisionTreeClassifier(
        max_depth=profondeur_max,
        min_samples_leaf=feuille_min,
        random_state=42
    )
    clf.fit(X_arbre, y_arbre)

    precision_arbre = clf.score(X_arbre, y_arbre)
    importance = clf.feature_importances_
    noms_features = ['Port de destination', 'Protocole TCP', 'Tranche de port', 'Heure']

    metrics_row([
        ("Précision sur échantillon", f"{precision_arbre:.3f}", "green"),
        ("Profondeur réelle", f"{clf.get_depth()}", "purple"),
        ("Nombre de feuilles", f"{clf.get_n_leaves()}", ""),
    ])

    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.markdown("**Règles logiques extraites de l'arbre**")
        regles = export_text(clf, feature_names=noms_features)
        st.code(regles, language="text")

    with col2:
        st.markdown("**Importance des variables prédictives**")
        fig_imp = go.Figure(go.Bar(
            x=importance,
            y=noms_features,
            orientation='h',
            marker=dict(
                color=importance,
                colorscale=[[0, '#1a2235'], [1, '#00d4ff']],
                showscale=False
            ),
            text=[f"{v:.3f}" for v in importance],
            textposition='outside'
        ))
        fig_imp.update_layout(
            **PLOTLY_TEMPLATE,
            title="Contribution de chaque variable",
            xaxis_title="Importance (Gini)",
            height=280
        )
        st.plotly_chart(fig_imp, use_container_width=True)

        st.markdown("**Matrice de confusion**")
        y_pred = clf.predict(X_arbre)
        matrice = confusion_matrix(y_arbre, y_pred)
        fig_mat = px.imshow(
            matrice,
            labels=dict(x="Prédit", y="Réel", color="Nombre"),
            x=['Accepté', 'Rejeté'], y=['Accepté', 'Rejeté'],
            color_continuous_scale=[[0, '#111827'], [1, '#00d4ff']],
            text_auto=True
        )
        fig_mat.update_layout(**PLOTLY_TEMPLATE, height=220)
        st.plotly_chart(fig_mat, use_container_width=True)


# ─────────────────────────────────────────────
# ONGLET 8 : BILAN ET SYNTHÈSE
# ─────────────────────────────────────────────
def onglet_bilan(df, features):
    section_header("📊", "Synthèse et Recommandations",
                   "Vue d'ensemble des résultats et recommandations opérationnelles", "icon-green")

    # Évolution temporelle du trafic suspect
    df_temp = df.copy()
    df_temp['Date_Jour'] = df_temp['Date'].dt.date
    evolution = df_temp.groupby(['Date_Jour', 'Action']).size().reset_index(name='Nombre')

    fig_evo = px.area(
        evolution, x='Date_Jour', y='Nombre', color='Action',
        color_discrete_map={'Permit': '#10b981', 'Deny': '#ff4d6d'},
        title="Évolution quotidienne des flux acceptés et rejetés"
    )
    fig_evo.update_layout(**PLOTLY_TEMPLATE, height=300)
    st.plotly_chart(fig_evo, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # Distribution des ports
        top_ports = df[df['Action'] == 'Deny']['Port_Destination'].value_counts().head(10).reset_index()
        top_ports.columns = ['Port', 'Rejets']
        fig_ports = px.bar(
            top_ports, x='Rejets', y='Port', orientation='h',
            title="Top 10 des ports les plus rejetés",
            color='Rejets', color_continuous_scale=[[0, '#1a2235'], [1, '#ff4d6d']]
        )
        fig_ports.update_layout(**PLOTLY_TEMPLATE, height=320)
        st.plotly_chart(fig_ports, use_container_width=True)

    with col2:
        # Distribution horaire
        horaire = df.groupby(['Heure', 'Action']).size().reset_index(name='Nombre')
        fig_horaire = px.line(
            horaire, x='Heure', y='Nombre', color='Action',
            color_discrete_map={'Permit': '#10b981', 'Deny': '#ff4d6d'},
            title="Distribution horaire du trafic réseau",
            markers=True
        )
        fig_horaire.update_layout(**PLOTLY_TEMPLATE, height=320)
        st.plotly_chart(fig_horaire, use_container_width=True)

    success_box("""
    <strong>Recommandations opérationnelles :</strong><br>
    1. Bloquer de manière proactive les adresses IP identifiées comme suspectes par l'Isolation Forest et le LOF.<br>
    2. Renforcer les règles de filtrage sur les ports les plus ciblés (balayage détecté).<br>
    3. Surveiller les plages horaires présentant un pic d'activité de rejet.<br>
    4. Intégrer les règles extraites par l'arbre CART dans la configuration du pare-feu Iptables.
    """)


# ─────────────────────────────────────────────
# POINT D'ENTRÉE PRINCIPAL
# ─────────────────────────────────────────────
def show():
    st.markdown(STYLE, unsafe_allow_html=True)

    # Bannière principale
    st.markdown("""
    <div class="ml-hero">
        <h1>⚙️ Analyse par Apprentissage Automatique</h1>
        <p>
            Détection d'intrusions, classification comportementale et extraction de règles de sécurité 
            à partir des logs du pare-feu Iptables. L'ensemble des méthodes présentées ici combinent 
            apprentissage non supervisé (Isolation Forest, LOF, K-Means) et supervisé 
            (Régression Logistique, Arbre CART, Forêt Aléatoire) avec une évaluation rigoureuse 
            par validation croisée stratifiée.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Chargement des données
    try:
        df = charger_donnees()
    except Exception as erreur:
        st.error(f"Erreur lors du chargement des données : {erreur}")
        st.info("Assurez-vous que le fichier `data/data_exm.csv` est bien présent.")
        return

    features = construire_features_comportementales(df)

    # Navigation par onglets
    onglets = st.tabs([
        "🔬 Descripteurs",
        "🌲 Isolation Forest",
        "📡 LOF",
        "🔭 ACP",
        "🔵 K-Means",
        "🎯 Classification",
        "📋 Règles CART",
        "📊 Synthèse"
    ])

    with onglets[0]:
        onglet_feature_engineering(df, features)

    with onglets[1]:
        features_if = onglet_isolation_forest(features)

    with onglets[2]:
        onglet_lof(features)

    with onglets[3]:
        features_acp = features.copy()
        # Si Isolation Forest a déjà tourné dans ce run, on récupère Statut
        if 'Statut' not in features_acp.columns:
            scaler_tmp = StandardScaler()
            cols_tmp = ['Nombre_Ports_Distincts', 'Nombre_Rejets',
                        'Vitesse_Connexion_Par_Minute', 'Ratio_Rejet', 'Ratio_TCP']
            X_tmp = scaler_tmp.fit_transform(features_acp[cols_tmp])
            modele_tmp = IsolationForest(contamination=0.05, random_state=42)
            features_acp['Statut'] = pd.Series(
                modele_tmp.fit_predict(X_tmp), index=features_acp.index
            ).map({1: 'Normal', -1: 'Suspect'})
        onglet_acp(features_acp)

    with onglets[4]:
        onglet_kmeans(features)

    with onglets[5]:
        onglet_classification_supervisee(df)

    with onglets[6]:
        onglet_arbre_regles(df)

    with onglets[7]:
        onglet_bilan(df, features)