import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Alpha Scanner Pro", layout="wide", page_icon="📈")

# --- LECTURE ET NETTOYAGE DES DONNÉES ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFe-_p54aZOkH3IhSR48qH-DI4-G2O6EODPv3607B7D6SGhuOsd9Yv7HJoBxfOvOofoWr8MZB9JJo1/pub?output=csv"

@st.cache_data
def load_data():
    # 1. Lecture brute
    df = pd.read_csv(SHEET_CSV_URL)
    
    # 2. Nettoyage des noms de colonnes (supprime les espaces invisibles)
    df.columns = df.columns.str.strip()
    
    # 3. Conversion de la Date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # 4. NETTOYAGE DES NOMBRES (Virgule -> Point)
    # On nettoie les colonnes numériques essentielles
    cols_a_nettoyer = ['Score', 'Alpha', 'PEG', 'ROE']
    for col in cols_a_nettoyer:
        if col in df.columns:
            # On transforme en texte, on remplace la virgule par le point, on enlève le %, et on convertit en nombre
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

try:
    df = load_data()
    
    # On supprime les lignes vides s'il y en a
    df = df.dropna(subset=['Ticker'])

    # --- HEADER ---
    st.title("🛡️ Alpha Scanner Business Intelligence")
    st.markdown(f"**Dernière mise à jour :** {df['Date'].max().strftime('%d/%m/%Y')}")

    # --- KPI TOP BAR ---
    # Ici, les calculs ne planteront plus car Alpha est devenu un nombre (float)
    alpha_moy = df['Alpha'].mean()
    win_rate = (df['Alpha'] > 0).mean() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Alpha Moyen par Signal", f"{alpha_moy:.4f}", delta="Performance vs Marché")
    col2.metric("Taux de Succès", f"{win_rate:.1f}%")
    col3.metric("Actions sous Surveillance", len(df['Ticker'].unique()))

    # --- GRAPHIQUE ---
    st.subheader("📈 Courbe d'Alpha Cumulé")
    perf_growth = df.groupby('Date')['Alpha'].mean().cumsum().reset_index()
    fig = px.area(perf_growth, x='Date', y='Alpha', title="Progression de l'Alpha")
    st.plotly_chart(fig, use_container_width=True)

    # --- LES PÉPITES DU JOUR (GRADE A+) ---
    st.subheader("💎 Signaux Premium (A+)")
    top_picks = df[df['Grade'].str.contains("A+", na=False)].sort_values(by='Score', ascending=False)
    
    if not top_picks.empty:
        cols = st.columns(min(len(top_picks), 5))
        for i, (_, row) in enumerate(top_picks.head(5).iterrows()):
            with cols[i]:
                st.success(f"**{row['Ticker']}**")
                st.write(f"Score: **{row['Score']}**")
                st.write(f"PEG: **{row['PEG']}**")
    else:
        st.info("Aucun signal A+ aujourd'hui.")

    # --- BASE DE DONNÉES ---
    st.subheader("🔍 Base de Données Complète")
    st.dataframe(df.sort_values(by='Date', ascending=False))

except Exception as e:
    st.error(f"Erreur technique : {e}")
    st.info("Conseil : Vérifie que ton Google Sheets contient bien les colonnes : Date, Ticker, Score, Grade, PEG, ROE, Alpha")
