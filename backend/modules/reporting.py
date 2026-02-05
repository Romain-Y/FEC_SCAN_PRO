import pandas as pd
from io import BytesIO

def generer_excel_audit(df_anomalies, nom_client):
    """
    Génère un fichier Excel en mémoire avec 2 onglets :
    1. SYNTHESE : Résumé des chiffres
    2. DETAILS : La liste des anomalies
    """
    output = BytesIO()
    
    # --- 1. Préparation de l'onglet SYNTHESE ---
    synthese_data = {
        'Fichier': [nom_client],
        'Total Anomalies': [len(df_anomalies)],
        'Montant Total Risque': [df_anomalies['Debit'].sum() - df_anomalies['Credit'].sum() if not df_anomalies.empty else 0],
        'Nb Règles Touchées': [df_anomalies['Type_Anomalie'].nunique() if not df_anomalies.empty else 0]
    }
    
    df_synthese = pd.DataFrame(synthese_data)

    # --- 2. Écriture du fichier Excel ---
    # Note : On utilise 'xlsxwriter' pour pouvoir formater les colonnes
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Onglet Synthèse
        df_synthese.to_excel(writer, sheet_name='SYNTHESE', index=False)
        
        # Onglet Détails
        if not df_anomalies.empty:
            # On réorganise les colonnes pour que ce soit propre
            cols_propre = ['Gravité','Type_Anomalie', 'Compte', 'Date', 'Libelle', 'Debit', 'Credit', 'Journal']
            # On prend seulement les colonnes qui existent dans le DF
            cols_finales = [c for c in cols_propre if c in df_anomalies.columns]
            
            df_anomalies[cols_finales].to_excel(writer, sheet_name='DETAILS_ANOMALIES', index=False)
            
            # Mise en forme (Largeur des colonnes)
            worksheet = writer.sheets['DETAILS_ANOMALIES']
            for i, col in enumerate(cols_finales):
                worksheet.set_column(i, i, 20) 
        else:
            # Si tout est vide (pas d'anomalie)
            pd.DataFrame(["Aucune anomalie ! Bravo."]).to_excel(writer, sheet_name='DETAILS_ANOMALIES', header=False, index=False)

    return output.getvalue()