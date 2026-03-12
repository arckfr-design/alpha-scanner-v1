import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Alpha Scanner Business", layout="wide", page_icon="📈")

# --- 2. LECTURE ET NETTOYAGE DES DONNÉES ---
# Ton lien public Google Sheets (Format CSV)
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFe-_p54aZOkH3IhSR48qH-DI4-G2O6EODPv3607B7D6SGhuOsd9Yv7HJoBxfOvOofoWr8MZB9JJo1/pub?output=csv"

@st.cache_data(ttl=600) # Mise à jour toutes les 10 minutes
def load_data():
    # Lecture brute
    df = pd.read_csv(SHEET_CSV_URL)
    
    # Nettoyage des noms de colonnes (supprime les espaces)
    df.columns = df.columns.str.strip()
    
    # Conversion de la Date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # Nettoyage des colonnes numériques (Virgule -> Point)
    cols_num = ['Score', 'Alpha', 'PEG', 'ROE']
    for col in cols_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    return df

# --- 3. CHARGEMENT DES DONNÉES ---
try:
    df = load_data()
    df = df.dropna(subset=['Ticker']) # On ignore les lignes vides

    # --- 4. NAVIGATION LATERALE ---
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

        # --- GRAPHIQUE ALPHA CUMULÉ ---
        st.subheader("📈 Courbe de Performance (Alpha Cumulé)")
        perf_growth = df.groupby('Date')['Alpha'].mean().cumsum().reset_index()
        fig = px.area(perf_growth, x='Date', y='Alpha', title="Surperformance cumulée de l'algorithme")
        st.plotly_chart(fig, use_container_width=True)

        # --- SECTION PÉPITES A+ ---
        st.subheader("💎 Signaux Premium (Grade A+)")
        top_picks = df[df['Grade'].str.contains("A+", na=False)].sort_values(by='Score', ascending=False)
        
        if not top_picks.empty:
            cols = st.columns(min(len(top_picks), 5))
            for i, (_, row) in enumerate(top_picks.head(5).iterrows()):
                with cols[i]:
                    st.success(f"**{row['Ticker']}**")
                    st.write(f"Score: **{row['Score']}**")
                    st.write(f"PEG: **{row['PEG']}**")
        else:
            st.info("Aucune pépite A+ détectée aujourd'hui.")

        # --- TABLEAU COMPLET ---
        st.subheader("🔍 Toutes les opportunités")
        st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True)

    # ==========================================
    # ONGLET 2 : MON PORTEFEUILLE
    # ==========================================
    elif menu == "💰 Mon Portefeuille":
        st.title("💰 Suivi de mon Portefeuille (Getquin)")
        
        if 'Portfolio' in df.columns:
            # On filtre les actions possédées
            my_stocks = df[df['Portfolio'].str.upper() == "OUI"]
            
            if not my_stocks.empty:
                # Calcul de l'Alpha du Portefeuille
                alpha_p = my_stocks['Alpha'].mean()
                
                c1, c2 = st.columns(2)
                c1.metric("Alpha de mon Portefeuille", f"{alpha_p:.4f}")
                c2.metric("Nombre de Lignes", len(my_stocks))
                
                # Graphique individuel
                st.subheader("📊 Performance par ligne")
                fig_port = px.bar(my_stocks, x='Ticker', y='Alpha', color='Alpha',
                                  color_continuous_scale='RdYlGn', title="Mon Alpha par Action")
                st.plotly_chart(fig_port, use_container_width=True)
                
                st.subheader("📋 Détails de mes positions")
                st.dataframe(my_stocks[['Date', 'Ticker', 'Grade', 'Alpha', 'Prix Actuel', 'Score']], use_container_width=True)
            else:
                st.warning("⚠️ Aucune action marquée comme 'OUI' dans la colonne 'Portfolio'.")
                st.info("Allez dans Google Sheets et écrivez 'OUI' dans la colonne N pour les actions que vous possédez.")
        else:
            st.error("❌ La colonne 'Portfolio' n'existe pas encore dans Google Sheets.")
            st.info("Ajoutez un en-tête 'Portfolio' en colonne N dans votre fichier Sheets.")

except Exception as e:
    st.error(f"Erreur de chargement : {e}")
