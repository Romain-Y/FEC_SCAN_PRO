import pandas as pd

def charger_et_nettoyer(fichier):
    """
    Charge un fichier FEC (CSV/TXT), standardise les colonnes
    et convertit les types (dates, montants).
    """
    try:

        df = pd.read_csv(fichier, sep='\t', encoding='latin-1', dtype=str)


        mapping = {
            'CompteNum': 'Compte', 
            'EcritureDate': 'Date', 
            'Debit': 'Debit', 
            'Credit': 'Credit', 
            'EcritureLib': 'Libelle', 
            'JournalCode': 'Journal',
            'EcriturePiece': 'Piece' 
        }
        df = df.rename(columns=mapping)


        cols_montants = ['Debit', 'Credit']
        for col in cols_montants:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(' ', '')  
                    .str.replace(',', '.') 
                    .astype(float)         
                    .fillna(0)             
                )

        # 4. Conversion des Dates
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

        # 5. Nettoyage des chaînes de caractères
        if 'Compte' in df.columns:
            df['Compte'] = df['Compte'].astype(str).str.strip()
            
        return df

    except Exception as e:
     
        print(f"Erreur lors du nettoyage : {e}")
        return pd.DataFrame() # Retourne vide si échec