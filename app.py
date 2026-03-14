import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Alpha Scanner Pro", layout="wide", page_icon="🛡️")

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRFe-_p54aZOkH3IhSR48qH-DI4-G2O6EODPv3607B7D6SGhuOsd9Yv7HJoBxfOvOofoWr8MZB9JJo1/pub?output=csv"

@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df.columns = df.columns.str.strip()
    
    # Nettoyage des colonnes (Score, PEG, ROE, ROIC, Alpha, etc.)
    cols_num = ['Score', 'Alpha', 'PEG', 'ROE', 'ROIC', 'Perf. Stock', 'Perf. SPY', 'Prix Actuel']
    for col in cols_num:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.').str.replace('%', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Filtre crucial
    df = df.dropna(subset=['Ticker', 'Alpha'])
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    return df

try:
    df = load_data()

    # --- MENU LATERAL ---
    st.sidebar.title("💎 Alpha Navigation")
    menu = st.sidebar.radio("Navigation", ["🔍 Scanner Global", "📈 Historique Action", "💰 Performance Portefeuille"])
    st.sidebar.info(f"Dernière MAJ : {df['Date'].max().strftime('%d/%m/%Y')}")

    # ==========================================
    # 1. SCANNER GLOBAL
    # ==========================================
    if menu == "🔍 Scanner Global":
        st.title("🚀 Opportunités de Marché (GARP & Alpha)")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Alpha Moyen", f"{df['Alpha'].mean():.4f}")
        col2.metric("Win Rate", f"{(df['Alpha'] > 0).mean()*100:.1f}%")
        col3.metric("Signaux A+", len(df[df['Grade'].str.contains("A+", na=False)]))

st.subheader("💎 Meilleures Sélections (Grade A+)")
top_picks = df[df['Grade'].str.contains("A+", na=False)].sort_values('Score', ascending=False).head(5)

if not top_picks.empty:
    cols = st.columns(len(top_picks))
    for i, (_, row) in enumerate(top_picks.iterrows()):
        with cols[i]:
            st.success(f"**{row['Ticker']}**")
            st.write(f"PEG: **{row['PEG']}**")     
            st.write(f"Score: **{row['Score']:.2f}**") 
else:
    st.info("Aucune pépite A+ détectée aujourd'hui.")

        st.subheader("🔍 Base de Données Complète")
        st.dataframe(df.sort_values('Date', ascending=False), use_container_width=True)

    # ==========================================
    # 2. HISTORIQUE ACTION (DEEP DIVE)
    # ==========================================
    elif menu == "📈 Historique Action":
        st.title("🔍 Deep-Dive Historique")
        ticker = st.selectbox("Choisir un Ticker", sorted(df['Ticker'].unique()))
        sub_df = df[df['Ticker'] == ticker].sort_values('Date')

        fig_score = px.line(sub_df, x='Date', y='Score', title=f"Evolution du Score : {ticker}", markers=True)
        st.plotly_chart(fig_score, use_container_width=True)

        c1, c2 = st.columns(2)
        c1.plotly_chart(px.line(sub_df, x='Date', y='ROIC', title="ROIC (%)"), use_container_width=True)
        c2.plotly_chart(px.line(sub_df, x='Date', y='PEG', title="PEG Ratio"), use_container_width=True)

    # ==========================================
    # 3. PERFORMANCE PORTEFEUILLE
    # ==========================================
    elif menu == "💰 Performance Portefeuille":
        st.title("🏁 Notre Performance vs S&P 500")
        
        # Comparaison Since Inception
        df_perf = df.sort_values('Date').groupby('Date').agg({'Perf. Stock': 'mean', 'Perf. SPY': 'mean'}).reset_index()
        df_perf['Portfolio'] = (1 + df_perf['Perf. Stock']).cumprod() * 100
        df_perf['S&P 500'] = (1 + df_perf['Perf. SPY']).cumprod() * 100

        fig_inception = px.line(df_perf, x='Date', y=['Portfolio', 'S&P 500'], 
                                title="Croissance d'un capital de 100$",
                                color_discrete_map={"Portfolio": "#00FF00", "S&P 500": "#FF4B4B"})
        st.plotly_chart(fig_inception, use_container_width=True)

        if 'Portfolio' in df.columns:
            st.subheader("Positions Marquées 'OUI'")
            st.dataframe(df[df['Portfolio'].astype(str).str.upper() == "OUI"], use_container_width=True)

except Exception as e:
    st.error(f"Erreur : {e}")
