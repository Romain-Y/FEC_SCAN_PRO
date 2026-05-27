import pandas as pd
from io import BytesIO

# --- CODES DE GRAVITÉ ---
G_CRITIQUE = "🔴 CRITIQUE"
G_HAUTE = "🟠 HAUTE"
G_MOYENNE = "🟡 MOYENNE"

# ==========================================
# 1. NETTOYAGE DES DONNÉES
# ==========================================
def charger_et_nettoyer(fichier):
    try:
        contenu = fichier.read()
        df = None
        separateurs = ['\t', ';', '|', ',']
        encodings = ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']
        fichier_lu = False
        
        for sep in separateurs:
            for enc in encodings:
                try:
                    temp_df = pd.read_csv(BytesIO(contenu), sep=sep, encoding=enc, dtype=str, on_bad_lines='skip')
                    if len(temp_df.columns) > 4: 
                        df = temp_df
                        print(f"✅ Fichier lu avec succès ! (Séparateur: '{sep}', Encodage: '{enc}')")
                        fichier_lu = True
                        break
                except Exception:
                    continue
            if fichier_lu:
                break
        
        if not fichier_lu or df is None:
            return pd.DataFrame()

        mapping = {
            'CompteNum': 'Compte', 'EcritureDate': 'Date', 'Debit': 'Debit', 
            'Credit': 'Credit', 'EcritureLib': 'Libelle', 'JournalCode': 'Journal',
            'EcriturePiece': 'Piece'
        }
        df = df.rename(columns=mapping)

        for col in ['Debit', 'Credit']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(' ', '').str.replace(',', '.').astype(float).fillna(0)

        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

        if 'Compte' in df.columns:
            df['Compte'] = df['Compte'].astype(str).str.strip()
            
        return df

    except Exception as e:
        print(f"❌ Erreur CRITIQUE pendant le nettoyage : {e}")
        return pd.DataFrame()


# ==========================================
# 2. RÈGLES D'AUDIT (L'Intelligence Comptable)
# ==========================================

def check_compte_471(df):
    anomalies = pd.DataFrame()
    if 'Compte' in df.columns:
        lignes_471 = df[df['Compte'].astype(str).str.startswith('471', na=False)]
        if not lignes_471.empty:
            solde = round(lignes_471['Debit'].sum() - lignes_471['Credit'].sum(), 2)
            if solde != 0:
                anomalies = lignes_471.copy()
                anomalies['Type_Anomalie'] = f'1. Compte 471 non soldé ({solde}€)'
                anomalies['Gravité'] = G_CRITIQUE
    return anomalies

def check_caisse_negative(df):
    anomalies = pd.DataFrame()
    if 'Compte' in df.columns and 'Date' in df.columns:
        caisse = df[df['Compte'].astype(str).str.startswith('53', na=False)].copy()
        if not caisse.empty:
            caisse = caisse.sort_values(by='Date')
            caisse['Solde_Cumul'] = (caisse['Debit'] - caisse['Credit']).cumsum()
            if caisse['Solde_Cumul'].min() < -0.01:
                anomalies = caisse[caisse['Solde_Cumul'] < 0].copy()
                anomalies['Type_Anomalie'] = '2. Caisse Négative'
                anomalies['Gravité'] = G_CRITIQUE
    return anomalies

def check_doublons(df):
    cols_dbl = ['Date', 'Debit', 'Credit', 'Compte', 'Libelle']
    if all(col in df.columns for col in cols_dbl):
        df_audit = df[~df['Journal'].isin(['BQ', 'TR', 'CA', 'AN', 'RAN'])] if 'Journal' in df.columns else df
        doublons = df_audit[df_audit.duplicated(subset=cols_dbl, keep=False)]
        doublons = doublons[(doublons['Debit'] > 0) | (doublons['Credit'] > 0)].copy()
        if not doublons.empty:
            doublons['Type_Anomalie'] = '3. Doublon Suspect'
            doublons['Gravité'] = G_HAUTE
            return doublons
    return pd.DataFrame()

def check_ecritures_dimanche(df):
    anomalies = pd.DataFrame()
    if 'Date' in df.columns and 'Journal' in df.columns:
        df_temp = df.copy()
        df_temp['JourSemaine'] = df_temp['Date'].dt.dayofweek 
        dimanches = df_temp[
            (df_temp['JourSemaine'] == 6) & 
            (df_temp['Compte'].astype(str).str.startswith(('6', '2'), na=False)) &
            (~df_temp['Journal'].isin(['OD', 'AN', 'RAN']))
        ]
        if not dimanches.empty:
            anomalies = dimanches.copy()
            anomalies['Type_Anomalie'] = '4. Écriture le Dimanche'
            anomalies['Gravité'] = G_MOYENNE
    return anomalies

def check_montants_ronds(df):
    anomalies = pd.DataFrame()
    if 'Debit' in df.columns:
        ronds = df[
            (df['Debit'] >= 500) & 
            (df['Debit'] % 10 == 0) & 
            (df['Compte'].astype(str).str.startswith('6', na=False)) &
            (~df['Journal'].isin(['AN', 'OD']))
        ]
        if not ronds.empty:
            anomalies = ronds.copy()
            anomalies['Type_Anomalie'] = '5. Montant Rond Suspect'
            anomalies['Gravité'] = G_MOYENNE
    return anomalies

def check_mots_interdits(df):
    anomalies = pd.DataFrame()
    if 'Libelle' in df.columns:
        mots_interdits = ['AMENDE', 'PENALITE', 'MAJORATION', 'PV ', 'RADAR', 'FISC']
        amendes = df[df['Libelle'].str.upper().str.contains('|'.join(mots_interdits), na=False)]
        if not amendes.empty:
            anomalies = amendes.copy()
            anomalies['Type_Anomalie'] = '6. Amende/Pénalité détectée'
            anomalies['Gravité'] = G_HAUTE
    return anomalies

def check_fournisseurs_debiteurs(df):
    anomalies_list = []
    if 'Compte' in df.columns:
        df_fourn = df[df['Compte'].astype(str).str.startswith('401', na=False)]
        if not df_fourn.empty:
            soldes = df_fourn.groupby('Compte')[['Debit', 'Credit']].sum()
            soldes['Solde'] = soldes['Debit'] - soldes['Credit']
            anormaux = soldes[soldes['Solde'] > 1.0]
            for compte, data in anormaux.iterrows():
                anomalies_list.append({
                    'Type_Anomalie': '7. Fournisseur Débiteur (Anormal)',
                    'Compte': compte,
                    'Libelle': f"SOLDE DÉBITEUR DE {round(data['Solde'], 2)} €",
                    'Debit': data['Debit'], 'Credit': data['Credit'], 'Date': None, 'Journal': 'N/A',
                    'Gravité': G_MOYENNE
                })
    return pd.DataFrame(anomalies_list)

def check_clients_crediteurs(df):
    anomalies_list = []
    if 'Compte' in df.columns:
        df_cli = df[df['Compte'].astype(str).str.startswith('411', na=False)]
        if not df_cli.empty:
            soldes = df_cli.groupby('Compte')[['Debit', 'Credit']].sum()
            soldes['Solde'] = soldes['Debit'] - soldes['Credit']
            anormaux = soldes[soldes['Solde'] < -1.0]
            for compte, data in anormaux.iterrows():
                anomalies_list.append({
                    'Type_Anomalie': '8. Client Créditeur (Anormal)',
                    'Compte': compte,
                    'Libelle': f"SOLDE CRÉDITEUR DE {round(data['Solde'], 2)} €",
                    'Debit': data['Debit'], 'Credit': data['Credit'], 'Date': None, 'Journal': 'N/A',
                    'Gravité': G_MOYENNE
                })
    return pd.DataFrame(anomalies_list)

def check_coherence_dates(df):
    anomalies = pd.DataFrame()
    if 'Date' in df.columns and not df.empty and df['Date'].notna().any():
        annee_mode = df['Date'].dt.year.mode()[0]
        erreurs_date = df[(df['Date'].dt.year != annee_mode) & (~df['Journal'].isin(['AN', 'RAN']))]
        if not erreurs_date.empty:
            anomalies = erreurs_date.copy()
            anomalies['Type_Anomalie'] = f'9. Date Hors Exercice ({int(annee_mode)})'
            anomalies['Gravité'] = G_HAUTE
    return anomalies


# ==========================================
# 3. LE CHEF D'ORCHESTRE (API)
# ==========================================
def executer_audit_complet(fichier_upload):
    df = charger_et_nettoyer(fichier_upload)
    
    if df.empty:
        return {"success": False, "error": "Le fichier est vide ou n'est pas un FEC valide."}

    # On appelle TOUTES tes fonctions
    liste_anomalies = [
        check_compte_471(df),
        check_caisse_negative(df),
        check_doublons(df),
        check_ecritures_dimanche(df),
        check_montants_ronds(df),
        check_mots_interdits(df),
        check_fournisseurs_debiteurs(df),
        check_clients_crediteurs(df),
        check_coherence_dates(df)
    ]

    # Concaténation en ignorant les DataFrames vides
    df_final = pd.concat([a for a in liste_anomalies if not a.empty], ignore_index=True)

    if df_final.empty:
        return {
            "success": True, 
            "stats": {"total_anomalies": 0, "montant_risque": 0}, 
            "anomalies": []
        }

    # Formatage de la date pour le Frontend
    if 'Date' in df_final.columns:
        df_final['Date'] = df_final['Date'].astype(str)

    # Tri par Gravité (Critique en premier, puis Haute, puis Moyenne)
    ordre_gravite = {G_CRITIQUE: 1, G_HAUTE: 2, G_MOYENNE: 3}
    df_final['Tri_Gravite'] = df_final['Gravité'].map(ordre_gravite)
    df_final = df_final.sort_values(by=['Tri_Gravite', 'Type_Anomalie']).drop(columns=['Tri_Gravite'])

    montant_risque = df_final['Debit'].sum() - df_final['Credit'].sum()

    return {
        "success": True,
        "stats": {
            "total_anomalies": len(df_final),
            "montant_risque": round(abs(montant_risque), 2)
        },
        "anomalies": df_final[['Gravité', 'Type_Anomalie', 'Date', 'Compte', 'Libelle', 'Debit', 'Credit']].fillna('').to_dict(orient='records')
    }