import pandas as pd

# Codes de gravité visuels
G_CRITIQUE = "🔴 CRITIQUE"  # Bloquant fiscalement / Impossible
G_HAUTE = "🟠 HAUTE"       # Risque fiscal élevé
G_MOYENNE = "🟡 MOYENNE"    # A vérifier (peut être une erreur de saisie)

# -------------------------------------------------------------------------
# REGLE 1 : Compte 471 (Compte d'Attente) -> CRITIQUE
# -------------------------------------------------------------------------
def check_compte_471(df, nom_client="Inconnu"):
    anomalies = pd.DataFrame()
    if 'Compte' in df.columns:
        lignes_471 = df[df['Compte'].astype(str).str.startswith('471', na=False)]
        if not lignes_471.empty:
            solde_471 = round(lignes_471['Debit'].sum() - lignes_471['Credit'].sum(), 2)
            if solde_471 != 0:
                anomalies = lignes_471.copy()
                anomalies['Client'] = nom_client
                anomalies['Type_Anomalie'] = f'1. Compte 471 non soldé ({solde_471}€)'
                anomalies['Gravité'] = G_CRITIQUE  # <--- AJOUT
    return anomalies

# -------------------------------------------------------------------------
# REGLE 2 : Caisse Négative -> CRITIQUE
# -------------------------------------------------------------------------
def check_caisse_negative(df, nom_client="Inconnu"):
    anomalies = pd.DataFrame()
    if 'Compte' in df.columns and 'Date' in df.columns:
        caisse = df[df['Compte'].astype(str).str.startswith('53', na=False)].copy()
        if not caisse.empty:
            caisse = caisse.sort_values(by='Date')
            caisse['Solde_Cumul'] = (caisse['Debit'] - caisse['Credit']).cumsum()
            if caisse['Solde_Cumul'].min() < -0.01:
                lignes_neg = caisse[caisse['Solde_Cumul'] < 0].copy()
                lignes_neg['Client'] = nom_client
                lignes_neg['Type_Anomalie'] = '2. Caisse Négative'
                lignes_neg['Gravité'] = G_CRITIQUE # <--- AJOUT
                anomalies = lignes_neg
    return anomalies

# -------------------------------------------------------------------------
# REGLE 3 : Doublons -> HAUTE
# -------------------------------------------------------------------------
def check_doublons(df, nom_client="Inconnu"):
    anomalies = pd.DataFrame()
    cols_dbl = ['Date', 'Debit', 'Credit', 'Compte', 'Libelle']
    if all(col in df.columns for col in cols_dbl):
        journaux_exclus = ['BQ', 'TR', 'CA', 'AN', 'RAN']
        if 'Journal' in df.columns:
            df_audit_dbl = df[~df['Journal'].isin(journaux_exclus)]
        else:
            df_audit_dbl = df
        
        doublons = df_audit_dbl[df_audit_dbl.duplicated(subset=cols_dbl, keep=False)]
        doublons = doublons[(doublons['Debit'] > 0) | (doublons['Credit'] > 0)]
        
        if not doublons.empty:
            anomalies = doublons.copy()
            anomalies['Client'] = nom_client
            anomalies['Type_Anomalie'] = '3. Doublon Suspect'
            anomalies['Gravité'] = G_HAUTE # <--- AJOUT
    return anomalies

# -------------------------------------------------------------------------
# REGLE 4 : Écritures le Dimanche -> MOYENNE
# -------------------------------------------------------------------------
def check_ecritures_dimanche(df, nom_client="Inconnu"):
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
            anomalies['Client'] = nom_client
            anomalies['Type_Anomalie'] = '4. Écriture Dimanche'
            anomalies['Gravité'] = G_MOYENNE # <--- AJOUT
    return anomalies

# -------------------------------------------------------------------------
# REGLE 5 : Montants Ronds -> MOYENNE
# -------------------------------------------------------------------------
def check_montants_ronds(df, nom_client="Inconnu"):
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
            anomalies['Client'] = nom_client
            anomalies['Type_Anomalie'] = '5. Montant Rond Suspect'
            anomalies['Gravité'] = G_MOYENNE # <--- AJOUT
    return anomalies

# -------------------------------------------------------------------------
# REGLE 6 : Mots-clés Interdits -> HAUTE
# -------------------------------------------------------------------------
def check_mots_interdits(df, nom_client="Inconnu"):
    anomalies = pd.DataFrame()
    if 'Libelle' in df.columns:
        mots_interdits = ['AMENDE', 'PENALITE', 'MAJORATION', 'PV ', 'RADAR', 'FISC']
        amendes = df[df['Libelle'].str.upper().str.contains('|'.join(mots_interdits), na=False)]
        if not amendes.empty:
            anomalies = amendes.copy()
            anomalies['Client'] = nom_client
            anomalies['Type_Anomalie'] = '6. Amende/Pénalité détectée'
            anomalies['Gravité'] = G_HAUTE # <--- AJOUT
    return anomalies

# -------------------------------------------------------------------------
# REGLE 7 : Fournisseurs Débiteurs -> MOYENNE
# -------------------------------------------------------------------------
def check_fournisseurs_debiteurs(df, nom_client="Inconnu"):
    anomalies_list = []
    if 'Compte' in df.columns:
        df_fourn = df[df['Compte'].astype(str).str.startswith('401', na=False)]
        if not df_fourn.empty:
            soldes = df_fourn.groupby('Compte')[['Debit', 'Credit']].sum()
            soldes['Solde'] = soldes['Debit'] - soldes['Credit']
            anormaux = soldes[soldes['Solde'] > 1.0]
            
            for compte, data in anormaux.iterrows():
                anomalies_list.append({
                    'Client': nom_client,
                    'Type_Anomalie': '7. Fournisseur Débiteur (Anormal)',
                    'Compte': compte,
                    'Libelle': f"SOLDE DÉBITEUR DE {round(data['Solde'], 2)} €",
                    'Debit': data['Debit'], 'Credit': data['Credit'], 'Date': None, 'Journal': 'N/A',
                    'Gravité': G_MOYENNE # <--- AJOUT
                })
    return pd.DataFrame(anomalies_list) if anomalies_list else pd.DataFrame()

# -------------------------------------------------------------------------
# REGLE 8 : Clients Créditeurs -> MOYENNE
# -------------------------------------------------------------------------
def check_clients_crediteurs(df, nom_client="Inconnu"):
    anomalies_list = []
    if 'Compte' in df.columns:
        df_cli = df[df['Compte'].astype(str).str.startswith('411', na=False)]
        if not df_cli.empty:
            soldes = df_cli.groupby('Compte')[['Debit', 'Credit']].sum()
            soldes['Solde'] = soldes['Debit'] - soldes['Credit']
            anormaux = soldes[soldes['Solde'] < -1.0]
            
            for compte, data in anormaux.iterrows():
                anomalies_list.append({
                    'Client': nom_client,
                    'Type_Anomalie': '8. Client Créditeur (Anormal)',
                    'Compte': compte,
                    'Libelle': f"SOLDE CRÉDITEUR DE {round(data['Solde'], 2)} €",
                    'Debit': data['Debit'], 'Credit': data['Credit'], 'Date': None, 'Journal': 'N/A',
                    'Gravité': G_MOYENNE # <--- AJOUT
                })
    return pd.DataFrame(anomalies_list) if anomalies_list else pd.DataFrame()

# -------------------------------------------------------------------------
# REGLE 9 : Cohérence des Dates -> HAUTE
# -------------------------------------------------------------------------
def check_coherence_dates(df, nom_client="Inconnu"):
    anomalies = pd.DataFrame()
    if 'Date' in df.columns and not df.empty and df['Date'].notna().any():
        annee_mode = df['Date'].dt.year.mode()[0]
        erreurs_date = df[(df['Date'].dt.year != annee_mode) & (~df['Journal'].isin(['AN', 'RAN']))]
        if not erreurs_date.empty:
            anomalies = erreurs_date.copy()
            anomalies['Client'] = nom_client
            anomalies['Type_Anomalie'] = f'9. Date Hors Exercice ({int(annee_mode)})'
            anomalies['Gravité'] = G_HAUTE # <--- AJOUT
    return anomalies