import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Next Pick", layout="wide", page_icon="🛡️")

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFe-_p54aZOkH3IhSR48qH-DI4-G2O6EODPv3607B7D6SGhuOsd9Yv7HJoBxfOvOofoWr8MZB9JJo1/pub?output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Nettoyage des colonnes numériques (incluant Secteur en texte)
    cols_num = ['Score', 'Alpha', 'PEG', 'ROE', 'ROIC', 'Perf. Stock', 'Perf. SPY', 'Prix Actuel']
    for col in cols_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df = df.dropna(subset=['Ticker', 'Alpha'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

try:
    df = load_data()

    # --- FILTRE PAR SECTEUR (Barre latérale) ---
    st.sidebar.title("🛡️ Next Pick Navigation")
    
    secteurs_dispos = sorted(df['Secteur'].dropna().unique())
    secteurs_selectionnes = st.sidebar.multiselect("Filtrer par Secteurs", secteurs_dispos, default=secteurs_dispos)
    
    menu = st.sidebar.radio("Menu", ["🔍 Scanner Global", "📈 Historique Action", "💰 Mon Portefeuille"])
    
    # Application du filtre
    df_filtered = df[df['Secteur'].isin(secteurs_selectionnes)]

    # ==========================================
    # 1. SCANNER GLOBAL
    # ==========================================
    if menu == "🔍 Scanner Global":
        st.title("💎 Signaux & Opportunités")
        
        # KPIs (sur les données filtrées)
        col1, col2, col3 = st.columns(3)
        col1.metric("Alpha Moyen", f"{df_filtered['Alpha'].mean():.4f}")
        col2.metric("Actions Affichées", len(df_filtered['Ticker'].unique()))
        col3.metric("Taux de Succès", f"{(df_filtered['Alpha'] > 0).mean()*100:.1f}%")

        # Meilleures Sélections A+
        st.subheader("🚀 Top Signaux A+ (Filtrés)")
        top_picks = df_filtered[df_filtered['Grade'].str.contains("A+", na=False)].sort_values('Score', ascending=False).head(5)
        
        if not top_picks.empty:
            cols = st.columns(len(top_picks))
            for i, (_, row) in enumerate(top_picks.iterrows()):
                with cols[i]:
                    st.success(f"**{row['Ticker']}**")
                    st.write(f"PEG: **{row['PEG']}**")
                    st.write(f"Score: **{row['Score']:.2f}**") # Score en bas
        else:
            st.info("Aucun signal A+ dans ces secteurs aujourd'hui.")

        st.subheader("📋 Base de Données Complète")
        st.dataframe(df_filtered.sort_values('Date', ascending=False), use_container_width=True)

    # ==========================================
    # 2. HISTORIQUE PAR ACTION
    # ==========================================
    elif menu == "📈 Historique Action":
        st.title("🔍 Analyse Historique")
        target = st.selectbox("Choisir une action :", sorted(df['Ticker'].unique()))
        stock_df = df[df['Ticker'] == target].sort_values('Date')
        
        st.plotly_chart(px.line(stock_df, x='Date', y='Score', title=f"Score : {target}"), use_container_width=True)
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.line(stock_df, x='Date', y='ROIC', title="ROIC Evolution"), use_container_width=True)
        c2.plotly_chart(px.line(stock_df, x='Date', y='PEG', title="PEG Evolution"), use_container_width=True)

    # ==========================================
    # 3. MON PORTEFEUILLE
    # ==========================================
    elif menu == "💰 Mon Portefeuille":
        st.title("🏆 Performance Portefeuille vs S&P 500")
        if 'Portfolio' in df.columns:
            my_stocks = df[df['Portfolio'].astype(str).str.upper() == "OUI"]
            if not my_stocks.empty:
                df_bench = df.sort_values('Date').groupby('Date').agg({'Perf. Stock': 'mean', 'Perf. SPY': 'mean'}).reset_index()
                df_bench['Mon Portfolio'] = (1 + df_bench['Perf. Stock']).cumprod() * 100
                df_bench['S&P 500'] = (1 + df_bench['Perf. SPY']).cumprod() * 100
                st.plotly_chart(px.line(df_bench, x='Date', y=['Mon Portfolio', 'S&P 500'], title="Croissance vs Index"), use_container_width=True)
                st.dataframe(my_stocks, use_container_width=True)

except Exception as e:
    st.error(f"Erreur de syntaxe ou de chargement : {e}")
    st.info("Vérifiez que le bloc 'except' est bien présent à la fin du fichier.")
