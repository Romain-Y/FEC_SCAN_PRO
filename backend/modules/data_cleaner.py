import pandas as pd

def charger_et_nettoyer(fichier):
    """
    Charge un fichier FEC (CSV/TXT), standardise les colonnes
    et convertit les types (dates, montants).
    """
    try:
        # 1. Lecture du fichier
        # On garde tes paramètres : séparateur tabulation et encodage latin-1
        df = pd.read_csv(fichier, sep='\t', encoding='latin-1', dtype=str)

        # 2. Standardisation des noms de colonnes
        # Cela permet d'avoir toujours les mêmes noms dans le reste du code
        mapping = {
            'CompteNum': 'Compte', 
            'EcritureDate': 'Date', 
            'Debit': 'Debit', 
            'Credit': 'Credit', 
            'EcritureLib': 'Libelle', 
            'JournalCode': 'Journal',
            'EcriturePiece': 'Piece' # Ajout utile pour l'audit
        }
        df = df.rename(columns=mapping)

        # 3. Conversion des Montants (Debit / Credit)
        # On remplace les virgules par des points et les espaces par rien
        cols_montants = ['Debit', 'Credit']
        for col in cols_montants:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(' ', '')  # Enlève les espaces des milliers
                    .str.replace(',', '.') # Remplace virgule par point
                    .astype(float)         # Convertit en nombre
                    .fillna(0)             # Remplace les vides par 0
                )

        # 4. Conversion des Dates
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

        # 5. Nettoyage des chaînes de caractères (Optionnel mais propre)
        if 'Compte' in df.columns:
            df['Compte'] = df['Compte'].astype(str).str.strip()
            
        return df

    except Exception as e:
        # En cas d'erreur de lecture (ex: mauvais format), on renvoie un DataFrame vide ou on lève l'erreur
        print(f"Erreur lors du nettoyage : {e}")
        return pd.DataFrame() # Retourne vide si échec