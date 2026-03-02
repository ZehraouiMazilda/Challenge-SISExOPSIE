import streamlit as st

# Configuration de la page
st.set_page_config(page_title="SOC Dashboard SISE-OPSIE", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller vers :", 
    ["Accueil & Données", "Dashboard Descriptif", "Analyse ML", "Expert LLM"])

if page == "Accueil & Données":
    st.title("🛡️ SOC Dashboard - SISE 2026")
    st.write("Bienvenue Mazilda. Chargez les logs des OPSIE pour commencer.")
    # Ici, tu mettras le code pour charger le CSV ou se connecter à MariaDB

elif page == "Dashboard Descriptif":
    st.title("📊 Analyse descriptive des flux")
    st.info("Cette section répond aux exigences 1.5 du projet.")
    # Appel de ta fonction de dashboard (Top 5 IP, Top 10 ports < 1024, etc.)

elif page == "Analyse ML":
    st.title("🤖 Intelligence Artificielle - Clustering")
    st.write("Analyse des comportements suspects via Machine Learning.")
    # Ici, ton collègue ML intégrera son code

elif page == "Expert LLM":
    st.title("🧠 Expert IA Générative")
    st.write("Interpréteur de logs et aide à la décision.")
    # Ici, ton collègue LLM intégrera son code