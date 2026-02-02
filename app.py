import streamlit as st
import pandas as pd
from PIL import Image
import os

# Importation des modules
from modules.data_cleaner import charger_et_nettoyer
from modules.rules_expert import (
    check_compte_471, check_caisse_negative, check_doublons,
    check_ecritures_dimanche, check_montants_ronds, check_mots_interdits, 
    check_fournisseurs_debiteurs, check_clients_crediteurs, check_coherence_dates
)
from modules.reporting import generer_excel_audit

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="FEC SCAN by RY", page_icon="🛡️", layout="wide")

# --- CSS PERSONNALISÉ (Pour faire joli comme sur ta capture) ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    h1 {
        color: #fff;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #3b82f6;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR (GAUCHE) ---
with st.sidebar:
    # 1. Le Logo
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.warning("Ajoute 'logo.png' dans le dossier")

    st.markdown("---")
    
    # 2. Bouton Nouvelle Analyse (Recharge la page)
    if st.button("🔄 Nouvelle Analyse"):
        st.rerun()

    st.markdown("### ⚙️ Paramètres")
    
    # 3. Tes réglages (Seuil et Tolérance)
    seuil_ronds = st.number_input("Seuil Montants Ronds (€)", min_value=0, value=500, step=50)
    tolerance_caisse = st.number_input("Tolérance Caisse (€)", min_value=0.0, value=5.0, step=0.5)

    st.markdown("---")
    with st.expander("ℹ️ Guide des 9 Anomalies"):
        st.markdown("""
        1. Compte 471 non soldé
        2. Caisse négative
        3. Doublons suspects
        4. Écritures Dimanche
        5. Montants ronds
        6. Mots-clés interdits
        7. Fournisseurs débiteurs
        8. Clients créditeurs
        9. Dates hors exercice
        """)
    
    st.caption("v3.0 - Architecture Modularisée")

# --- ZONE PRINCIPALE ---
st.title("🛡️ Audit de Conformité")
st.markdown("### Contrôle Qualité Comptable Automatisé")

# Zone de Drag & Drop
st.info("📂 Glisser vos fichiers FEC ici (.txt, .csv)")
uploaded_file = st.file_uploader("", type=['txt', 'csv'], label_visibility="collapsed")

if uploaded_file:
    st.success(f"Fichier détecté : {uploaded_file.name}")
    
    # Nettoyage
    with st.spinner('Analyse et structuration des données...'):
        df = charger_et_nettoyer(uploaded_file)
    
    # Bouton d'action
    if st.button("🚀 LANCER L'AUDIT MAINTENANT"):
        
        # --- EXECUTION DES REGLES ---
        nom_client = uploaded_file.name
        resultats = []
        
        # Barre de progression
        my_bar = st.progress(0)
        
        # On passe tes paramètres (seuils) aux fonctions plus tard si besoin
        # Pour l'instant on lance la logique standard
        resultats.append(check_compte_471(df, nom_client))
        my_bar.progress(15)
        resultats.append(check_caisse_negative(df, nom_client)) # Faudra adapter la tolérance ici plus tard
        my_bar.progress(30)
        resultats.append(check_doublons(df, nom_client))
        my_bar.progress(45)
        resultats.append(check_ecritures_dimanche(df, nom_client))
        my_bar.progress(60)
        resultats.append(check_montants_ronds(df, nom_client)) # Faudra adapter le seuil ici plus tard
        my_bar.progress(70)
        resultats.append(check_mots_interdits(df, nom_client))
        resultats.append(check_fournisseurs_debiteurs(df, nom_client))
        resultats.append(check_clients_crediteurs(df, nom_client))
        resultats.append(check_coherence_dates(df, nom_client))
        my_bar.progress(100)
        
        # --- RÉSULTATS ---
        df_anomalies = pd.concat(resultats, ignore_index=True) if resultats else pd.DataFrame()
        
        # TRI PAR GRAVITÉ (Logique de tri personnalisé)
        if not df_anomalies.empty and 'Gravité' in df_anomalies.columns:
            # On définit l'ordre d'importance
            ordre_gravite = {"🔴 CRITIQUE": 0, "🟠 HAUTE": 1, "🟡 MOYENNE": 2}
            # On crée une colonne temporaire pour trier
            df_anomalies['sort_val'] = df_anomalies['Gravité'].map(ordre_gravite)
            # On trie et on supprime la colonne temporaire
            df_anomalies = df_anomalies.sort_values('sort_val').drop('sort_val', axis=1)

        st.markdown("---")
        
        if not df_anomalies.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Anomalies", len(df_anomalies))
            col2.metric("Montant Risque", f"{df_anomalies['Debit'].sum() - df_anomalies['Credit'].sum():.2f} €")
            col3.metric("Points de contrôle", "9 / 9")
            
            st.write("### 🚨 Tableau des Anomalies (Par Gravité)")
            
            # Affichage du tableau avec la colonne Gravité en premier
            cols = ['Gravité', 'Type_Anomalie', 'Compte', 'Date', 'Libelle', 'Debit', 'Credit']
            # On s'assure que les colonnes existent
            cols_finales = [c for c in cols if c in df_anomalies.columns]
            
            st.dataframe(
                df_anomalies[cols_finales], 
                use_container_width=True,
                height=500
            )
            
            # Export Excel Pro
            excel_data = generer_excel_audit(df_anomalies, nom_client)
            st.download_button(
                label="📥 Télécharger le Rapport Excel (Pro)",
                data=excel_data,
                file_name=f"Audit_{nom_client}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.balloons()
            st.success("✅ Aucune anomalie détectée ! Le fichier est clean.")
            # Bouton rapport vide
            excel_data = generer_excel_audit(df_anomalies, nom_client)
            st.download_button("📥 Télécharger Certificat Conformité", data=excel_data, file_name=f"Conformite_{nom_client}.xlsx")