# 📊 Dashboard Descriptif — Analyse des Logs Iptables

## 🎯 Objectif du Dashboard

Ce dashboard Streamlit permet une **analyse descriptive interactive** des flux réseau issus des logs d’un pare-feu Iptables.

Il offre :

- Visualisation des flux Permit / Deny
- Analyse TCP vs UDP
- Exploration des ports selon la RFC 6056
- Filtrage interactif avancé
- Exploration et export des données brutes

L'objectif est de fournir une vue claire, opérationnelle et exploitable de l'activité réseau.

---

# 🗂 Données utilisées

Fichier attendu :

data/data_exm.csv

Colonnes principales exploitées :

- date
- ip_source
- ip_destination
- protocol
- dest_port
- action

Les variables dérivées automatiquement :

- hour
- day
- port_category (classification RFC 6056)

---

# 🧭 Structure du Dashboard

Le dashboard est organisé en 8 sections analytiques.

---

## 🚦 1. Vue d’Ensemble

Indicateurs globaux :

- Total des flux
- Flux autorisés
- Flux bloqués
- Nombre d’IP sources distinctes
- Nombre de ports distincts

Permet d’avoir immédiatement une photographie de la posture réseau.

---

## 🔧 2. Filtres Interactifs

Filtres disponibles :

- Protocole (TCP / UDP / autres)
- Plage de ports :
  - System Ports (0-1023)
  - User Ports (1024-49151)
  - Dynamic Ports (49152-65535)
  - Plage personnalisée

Les catégories de ports respectent la RFC 6056.

---

## 📈 3. Analyse des Flux

- Barplot Autorisé vs Rejeté par protocole
- Évolution temporelle du trafic
- Range selector dynamique (1 semaine, 1 mois, etc.)

Permet d’identifier les pics d’activité.

---

## 📡 4. Comparaison TCP vs UDP

Pour chaque protocole :

- Total des flux
- Nombre bloqué
- Taux de blocage
- Top 5 ports

Cela permet d’identifier quel protocole présente le plus de risque.

---

## 📊 5. Distribution des Ports (RFC 6056)

- Diagramme circulaire des catégories de ports
- Barplot empilé Permit / Deny par catégorie

Analyse structurée selon :

- System Ports
- User Ports
- Dynamic Ports

---

## 🔝 6. Top IP Sources

- Top 5 IP les plus actives
- Scatter plot :
  - Nombre de destinations contactées
  - Flux rejetés
  - Taille proportionnelle au volume total

Permet d’identifier les comportements de scan ou de flood.

---

## 🔌 7. Top 10 Ports Privilégiés (<1024)

Analyse des ports système :

- SSH (22)
- FTP (21)
- HTTP (80)
- HTTPS (443)
- DNS (53)
- etc.

Visualisation :

- Donut chart
- Barplot détaillé

---

## 📄 8. Exploration des Données Brutes

Fonctionnalités :

- Filtrage protocole
- Filtrage action
- Sélection du nombre de lignes
- Export CSV

Permet une exploitation opérationnelle directe.

---

# 🧠 Choix Techniques

- Streamlit pour l’interactivité
- Plotly pour les visualisations dynamiques
- Cache Streamlit (@st.cache_data) pour optimiser les performances
- Design System unifié avec thème sombre cohérent
- Séparation logique des sections

---

# 🚀 Lancement

streamlit run dashboard.py

Vérifier que :

- Le dossier data/ existe
- Le fichier data_exm.csv est présent

---

# 🏁 Conclusion

Ce dashboard fournit une analyse descriptive complète des logs firewall.

Il constitue :

- Une base d’exploration initiale
- Un outil d’investigation rapide
- Un support décisionnel
- Un complément visuel aux modules ML et RAG

Il s’intègre dans une architecture globale d’analyse sécurité combinant :
Dashboard descriptif + Machine Learning + RAG intelligent.
