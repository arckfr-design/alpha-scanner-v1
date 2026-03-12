import streamlit as st
import pandas as pd
import plotly.express as px # Pour des graphiques interactifs

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Alpha Scanner Pro", layout="wide", page_icon="📈")

# --- LECTURE DES DONNÉES ---
# Note : Pour que cela marche, dans Google Sheets : 
# Fichier > Partager > Publier sur le Web > Format CSV > Publier
# Copie le lien généré ici :
SHEET_CSV_URL = "# Correction du lien : on passe de 'pubhtml' à 'pub?output=csv'
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFe-_p54aZOkH3IhSR48qH-DI4-G2O6EODPv3607B7D6SGhuOsd9Yv7HJoBxfOvOofoWr8MZB9JJo1/pub?output=csv"

@st.cache_data # Pour éviter de recharger le fichier à chaque clic
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

try:
    df = load_data()

    # --- HEADER ---
    st.title("🛡️ Alpha Scanner Business Intelligence")
    st.markdown(f"**Dernière mise à jour :** {df['Date'].max().strftime('%d/%m/%Y')}")

    # --- KPI TOP BAR ---
    # Calcul de l'Alpha Moyen (Perf Action - Perf SPY)
    alpha_total = df['ALPHA'].mean() * 100
    win_rate = (df['ALPHA'] > 0).mean() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Alpha Moyen par Signal", f"{alpha_total:.2f}%", delta="Performance vs Marché")
    col2.metric("Taux de Succès (Hit Rate)", f"{win_rate:.1f}%", delta="Signaux Gagnants")
    col3.metric("Actions sous Surveillance", len(df['Ticker'].unique()))

    # --- GRAPHIQUE DE PERFORMANCE CUMULÉE ---
    st.subheader("📈 Courbe d'Alpha Cumulé (Preuve de Performance)")
    # On groupe par date pour voir l'évolution de la stratégie
    perf_growth = df.groupby('Date')['ALPHA'].mean().cumsum().reset_index()
    fig = px.area(perf_growth, x='Date', y='ALPHA', title="Progression de l'Alpha (Surperformance cumulée)")
    st.plotly_chart(fig, use_container_width=True)

    # --- LES PÉPITES DU JOUR (GRADE A+) ---
    st.subheader("💎 Signaux Premium (A+)")
    top_picks = df[df['Grade'].str.contains("A+")].sort_values(by='Score', ascending=False)
    
    # Affichage sous forme de colonnes/cartes
    cols = st.columns(len(top_picks.head(5)))
    for i, (_, row) in enumerate(top_picks.head(5).iterrows()):
        with cols[i]:
            st.success(f"**{row['Ticker']}**")
            st.write(f"Score: {row['Score']}")
            st.write(f"PEG: {row['PEG']}")

    # --- TABLEAU DE RECHERCHE COMPLET ---
    st.subheader("🔍 Base de Données Complète")
    recherche = st.text_input("Rechercher une action (ex: NVDA)...")
    if recherche:
        st.dataframe(df[df['Ticker'].str.contains(recherche.upper())])
    else:
        st.dataframe(df.sort_values(by='Date', ascending=False).head(20))

except Exception as e:
    st.error("En attente de données... Vérifie que ton lien Google Sheets CSV est bien configuré et publié.")
    st.info("Astuce : Dans Google Sheets, assure-toi d'avoir des données dans les colonnes A à M.")
