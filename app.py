import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Alpha Scanner Business", layout="wide", page_icon="📈")

# --- 2. FONCTION DE CHARGEMENT ET NETTOYAGE ---
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFe-_p54aZOkH3IhSR48qH-DI4-G2O6EODPv3607B7D6SGhuOsd9Yv7HJoBxfOvOofoWr8MZB9JJo1/pub?output=csv"

@st.cache_data(ttl=300) # Rafraîchit toutes les 5 minutes
def load_data():
    # Lecture du CSV
    df = pd.read_csv(SHEET_CSV_URL)
    
    # Nettoyage des noms de colonnes
    df.columns = df.columns.str.strip()
    
    # --- NETTOYAGE DES DONNÉES ---
    # On convertit les colonnes numériques (Virgule -> Point)
    cols_num = ['Score', 'Alpha', 'PEG', 'ROE', 'Prix Actuel', 'Perf. Stock', 'Perf. SPY']
    for col in cols_num:
        if col in df.columns:
            # On transforme en texte, remplace la virgule, enlève le %
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '')
            # On transforme en nombre. Si c'est du texte comme "Cargando", ça devient NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # --- FILTRE ANTI-VIDE (CRITIQUE) ---
    # On ne garde que les lignes où Ticker ET Alpha existent réellement
    df = df.dropna(subset=['Ticker', 'Alpha'])
    
    # Conversion de la date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    return df

# --- 3. CHARGEMENT ET INTERFACE ---
try:
    df = load_data()

    if df.empty:
        st.warning("⚠️ En attente de données valides... Vérifie que tes formules Google Sheets ont fini de calculer.")
        st.info("Astuce : Assure-toi d'avoir au moins une ligne avec un Ticker et un Alpha calculé.")
        st.stop()

    # --- NAVIGATION LATERALE ---
    st.sidebar.title("💎 Alpha Navigation")
    menu = st.sidebar.radio("Aller vers :", ["🔍 Scanner Global", "💰 Mon Portefeuille"])
    
    st.sidebar.markdown("---")
    st.sidebar.write(f"**Dernier Scan :** {df['Date'].max().strftime('%d/%m/%Y')}")

    # ==========================================
    # ONGLET 1 : SCANNER GLOBAL
    # ==========================================
    if menu == "🔍 Scanner Global":
        st.title("🛡️ Alpha Scanner Business Intelligence")
        
        # --- KPIs ---
        alpha_moy = df['Alpha'].mean()
        win_rate = (df['Alpha'] > 0).mean() * 100
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Alpha Moyen (Global)", f"{alpha_moy:.4f}", delta="Performance vs Marché")
        col2.metric("Taux de Succès", f"{win_rate:.1f}%")
        col3.metric("Actions Surveillées", len(df['Ticker'].unique()))

        # --- GRAPHIQUE ---
        st.subheader("📈 Courbe de Performance (Alpha Cumulé)")
        # On trie par date pour le graphique
        df_sorted = df.sort_values('Date')
        perf_growth = df_sorted.groupby('Date')['Alpha'].mean().cumsum().reset_index()
        fig = px.area(perf_growth, x='Date', y='Alpha', title="Surperformance cumulée")
        st.plotly_chart(fig, use_container_width=True)

        # --- TOP PICKS A+ ---
        st.subheader("💎 Signaux Premium (Grade A+)")
        top_picks = df[df['Grade'].str.contains("A+", na=False)].sort_values(by='Score', ascending=False)
        
        if not top_picks.empty:
            cols = st.columns(min(len(top_picks), 5))
            for i, (_, row) in enumerate(top_picks.head(5).iterrows()):
                with cols[i]:
                    st.success(f"**{row['Ticker']}**")
                    st.write(f"Score: **{row['Score']}**")
                    st.write(f"Alpha: **{row['Alpha']:.4f}**")
        else:
            st.info("Aucune pépite A+ détectée aujourd'hui.")

        # --- TABLEAU ---
        st.subheader("🔍 Base de données complète")
        st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)

    # ==========================================
    # ONGLET 2 : MON PORTEFEUILLE
    # ==========================================
    elif menu == "💰 Mon Portefeuille":
        st.title("💰 Suivi de mon Portefeuille")
        
        if 'Portfolio' in df.columns:
            # On nettoie et filtre
            my_stocks = df[df['Portfolio'].astype(str).str.upper() == "OUI"]
            
            if not my_stocks.empty:
                alpha_p = my_stocks['Alpha'].mean()
                
                c1, c2 = st.columns(2)
                c1.metric("Alpha de mon Portefeuille", f"{alpha_p:.4f}")
                c2.metric("Nombre de Lignes", len(my_stocks))
                
                st.subheader("📊 Performance par action")
                fig_port = px.bar(my_stocks, x='Ticker', y='Alpha', color='Alpha',
                                  color_continuous_scale='RdYlGn')
                st.plotly_chart(fig_port, use_container_width=True)
                
                st.dataframe(my_stocks[['Date', 'Ticker', 'Grade', 'Alpha', 'Prix Actuel']], use_container_width=True)
            else:
                st.warning("⚠️ Aucune action marquée 'OUI' dans la colonne 'Portfolio'.")
        else:
            st.error("❌ La colonne 'Portfolio' (colonne N) est manquante dans Sheets.")

except Exception as e:
    st.error(f"Erreur de chargement : {e}")
