from io import BytesIO
import pandas as pd

G_CRITIQUE = "CRITIQUE"
G_HAUTE = "HAUTE"
G_MOYENNE = "MOYENNE"

COLONNES_DGFIP_OBLIGATOIRES = [
    "JournalCode",
    "JournalLib",
    "EcritureNum",
    "EcritureDate",
    "CompteNum",
    "CompteLib",
    "CompAuxNum",
    "CompAuxLib",
    "PieceRef",
    "PieceDate",
    "EcritureLib",
    "Debit",
    "Credit",
    "EcritureLet",
    "DateLet",
    "ValidDate",
    "Montantdevise",
    "Idevise",
]


def charger_et_nettoyer(fichier):
  try:
    contenu = fichier.read() if hasattr(fichier, "read") else fichier
    df = None
    separateurs = ["\t", ";", "|", ","]
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    fichier_lu = False

    for sep in separateurs:
      for enc in encodings:
        try:
          temp_df = pd.read_csv(
              BytesIO(contenu),
              sep=sep,
              encoding=enc,
              dtype=str,
              on_bad_lines="skip",
          )
          if len(temp_df.columns) >= 6:
            df = temp_df
            fichier_lu = True
            break
        except Exception:
          continue
      if fichier_lu:
        break

    if not fichier_lu or df is None:
      return pd.DataFrame(), False, False, 0

    structure_valide = all(
        col in df.columns
        for col in ["CompteNum", "Debit", "Credit", "EcritureDate"]
    )

    mapping = {
        "CompteNum": "Compte",
        "EcritureDate": "Date",
        "Debit": "Debit",
        "Credit": "Credit",
        "EcritureLib": "Libelle",
        "JournalCode": "Journal",
        "PieceRef": "Piece",
        "EcriturePiece": "Piece",
    }
    df = df.rename(columns=mapping)

    for col in ["Debit", "Credit"]:
      if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(" ", "")
            .str.replace(",", ".")
            .astype(float)
            .fillna(0.0)
        )
      else:
        df[col] = 0.0

    if "Date" in df.columns:
      df["Date"] = pd.to_datetime(
          df["Date"].astype(str), format="%Y%m%d", errors="coerce"
      )
      masque_na = df["Date"].isna()
      if masque_na.any():
        df.loc[masque_na, "Date"] = pd.to_datetime(
            df.loc[masque_na, "Date"], errors="coerce"
        )

    if "Compte" in df.columns:
      df["Compte"] = df["Compte"].astype(str).str.strip()

    if "Piece" not in df.columns:
      df["Piece"] = ""

    total_debit = round(df["Debit"].sum(), 2)
    total_credit = round(df["Credit"].sum(), 2)
    equilibre = abs(total_debit - total_credit) < 0.05

    return df, structure_valide, equilibre, len(df)

  except Exception:
    return pd.DataFrame(), False, False, 0


def check_compte_471(df):
  anomalies = pd.DataFrame()
  if "Compte" in df.columns:
    lignes_471 = df[df["Compte"].astype(str).str.startswith("471", na=False)]
    if not lignes_471.empty:
      solde = round(lignes_471["Debit"].sum() - lignes_471["Credit"].sum(), 2)
      if solde != 0:
        anomalies = lignes_471.copy()
        anomalies["Type_Anomalie"] = f"Compte 471 non soldé ({solde} €)"
        anomalies["Gravite"] = G_CRITIQUE
  return anomalies


def check_caisse_negative(df):
  anomalies = pd.DataFrame()
  if "Compte" in df.columns and "Date" in df.columns:
    caisse = df[df["Compte"].astype(str).str.startswith("53", na=False)].copy()
    if not caisse.empty:
      caisse = caisse.sort_values(by="Date")
      caisse["Solde_Cumul"] = (caisse["Debit"] - caisse["Credit"]).cumsum()
      if caisse["Solde_Cumul"].min() < -0.01:
        anomalies = caisse[caisse["Solde_Cumul"] < 0].copy()
        anomalies["Type_Anomalie"] = "Caisse Négative (Solde créditeur)"
        anomalies["Gravite"] = G_CRITIQUE
  return anomalies


def check_doublons(df):
  cols_dbl = ["Date", "Debit", "Credit", "Compte", "Libelle"]
  if all(col in df.columns for col in cols_dbl):
    df_audit = (
        df[~df["Journal"].isin(["BQ", "TR", "CA", "AN", "RAN"])]
        if "Journal" in df.columns
        else df
    )
    doublons = df_audit[df_audit.duplicated(subset=cols_dbl, keep=False)]
    doublons = doublons[
        (doublons["Debit"] > 0) | (doublons["Credit"] > 0)
    ].copy()
    if not doublons.empty:
      doublons["Type_Anomalie"] = "Doublon suspect"
      doublons["Gravite"] = G_HAUTE
      return doublons
  return pd.DataFrame()


def check_ecritures_dimanche(df):
  anomalies = pd.DataFrame()
  if "Date" in df.columns and "Journal" in df.columns:
    df_temp = df[df["Date"].notna()].copy()
    if not df_temp.empty:
      df_temp["JourSemaine"] = df_temp["Date"].dt.dayofweek
      dimanches = df_temp[
          (df_temp["JourSemaine"] == 6)
          & (df_temp["Compte"].astype(str).str.startswith(("6", "2"), na=False))
          & (~df_temp["Journal"].isin(["OD", "AN", "RAN"]))
      ]
      if not dimanches.empty:
        anomalies = dimanches.copy()
        anomalies["Type_Anomalie"] = "Écriture enregistrée un dimanche"
        anomalies["Gravite"] = G_MOYENNE
  return anomalies


def check_montants_ronds(df):
  anomalies = pd.DataFrame()
  if "Debit" in df.columns:
    ronds = df[
        (df["Debit"] >= 500)
        & (df["Debit"] % 10 == 0)
        & (df["Compte"].astype(str).str.startswith("6", na=False))
        & (~df["Journal"].isin(["AN", "OD"]))
    ]
    if not ronds.empty:
      anomalies = ronds.copy()
      anomalies["Type_Anomalie"] = "Montant rond suspect (Charge >= 500 €)"
      anomalies["Gravite"] = G_MOYENNE
  return anomalies


def check_mots_interdits(df):
  anomalies = pd.DataFrame()
  if "Libelle" in df.columns:
    mots_interdits = [
        "AMENDE",
        "PENALITE",
        "MAJORATION",
        "PV ",
        "RADAR",
        "FISC",
    ]
    amendes = df[
        df["Libelle"]
        .str.upper()
        .str.contains("|".join(mots_interdits), na=False)
    ]
    if not amendes.empty:
      anomalies = amendes.copy()
      anomalies["Type_Anomalie"] = "Libellé à risque fiscal (Amende / Pénalité)"
      anomalies["Gravite"] = G_HAUTE
  return anomalies


def check_fournisseurs_debiteurs(df):
  anomalies_list = []
  if "Compte" in df.columns:
    df_fourn = df[df["Compte"].astype(str).str.startswith("401", na=False)]
    if not df_fourn.empty:
      soldes = df_fourn.groupby("Compte")[["Debit", "Credit"]].sum()
      soldes["Solde"] = soldes["Debit"] - soldes["Credit"]
      anormaux = soldes[soldes["Solde"] > 1.0]
      for compte, data in anormaux.iterrows():
        anomalies_list.append({
            "Type_Anomalie": "Fournisseur débiteur anormal",
            "Compte": compte,
            "Libelle": f"Solde débiteur de {round(data['Solde'], 2)} €",
            "Debit": data["Debit"],
            "Credit": data["Credit"],
            "Date": None,
            "Journal": "N/A",
            "Piece": "N/A",
            "Gravite": G_MOYENNE,
        })
  return pd.DataFrame(anomalies_list)


def check_clients_crediteurs(df):
  anomalies_list = []
  if "Compte" in df.columns:
    df_cli = df[df["Compte"].astype(str).str.startswith("411", na=False)]
    if not df_cli.empty:
      soldes = df_cli.groupby("Compte")[["Debit", "Credit"]].sum()
      soldes["Solde"] = soldes["Debit"] - soldes["Credit"]
      anormaux = soldes[soldes["Solde"] < -1.0]
      for compte, data in anormaux.iterrows():
        anomalies_list.append({
            "Type_Anomalie": "Client créditeur anormal",
            "Compte": compte,
            "Libelle": f"Solde créditeur de {round(data['Solde'], 2)} €",
            "Debit": data["Debit"],
            "Credit": data["Credit"],
            "Date": None,
            "Journal": "N/A",
            "Piece": "N/A",
            "Gravite": G_MOYENNE,
        })
  return pd.DataFrame(anomalies_list)


def check_coherence_dates(df):
  anomalies = pd.DataFrame()
  if "Date" in df.columns and not df.empty and df["Date"].notna().any():
    dates_valides = df.loc[df["Date"].notna(), "Date"]
    annee_mode = dates_valides.dt.year.mode()[0]
    erreurs_date = df[
        (df["Date"].isna())
        | (
            (df["Date"].dt.year != annee_mode)
            & (~df["Journal"].isin(["AN", "RAN"]))
        )
    ]
    if not erreurs_date.empty:
      anomalies = erreurs_date.copy()
      anomalies["Type_Anomalie"] = (
          f"Date hors exercice fiscal ({int(annee_mode)})"
      )
      anomalies["Gravite"] = G_HAUTE
  return anomalies


def executer_audit_complet(fichier_upload):
  df, structure_valide, equilibre, nb_lignes = charger_et_nettoyer(
      fichier_upload
  )

  if df.empty:
    return {
        "success": False,
        "error": "Le fichier est vide ou n'est pas un FEC conforme.",
    }

  dates_valides = (
      df.loc[df["Date"].notna(), "Date"]
      if ("Date" in df.columns and df["Date"].notna().any())
      else None
  )
  annee_exercice = (
      int(dates_valides.dt.year.mode()[0]) if dates_valides is not None else None
  )

  liste_anomalies = [
      check_compte_471(df),
      check_caisse_negative(df),
      check_doublons(df),
      check_ecritures_dimanche(df),
      check_montants_ronds(df),
      check_mots_interdits(df),
      check_fournisseurs_debiteurs(df),
      check_clients_crediteurs(df),
      check_coherence_dates(df),
  ]

  df_final = pd.concat(
      [a for a in liste_anomalies if not a.empty], ignore_index=True
  )

  if df_final.empty:
    return {
        "success": True,
        "metadonnees": {
            "nb_lignes": nb_lignes,
            "structure_valide": structure_valide,
            "equilibre": equilibre,
            "exercice_annee": annee_exercice,
        },
        "stats": {"total_anomalies": 0, "montant_risque": 0.0},
        "anomalies": [],
    }

  montant_risque = df_final["Debit"].sum() + df_final["Credit"].sum()

  for col_manquante in ["Piece", "Libelle", "Journal"]:
    if col_manquante not in df_final.columns:
      df_final[col_manquante] = ""

  if "Date" in df_final.columns:
    df_final["Date_str"] = df_final["Date"].apply(
        lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
    )
  else:
    df_final["Date_str"] = ""

  return {
      "success": True,
      "metadonnees": {
          "nb_lignes": nb_lignes,
          "structure_valide": structure_valide,
          "equilibre": equilibre,
          "exercice_annee": annee_exercice,
      },
      "stats": {
          "total_anomalies": len(df_final),
          "montant_risque": round(float(montant_risque), 2),
      },
      "anomalies": (
          df_final[[
              "Gravite",
              "Type_Anomalie",
              "Date_str",
              "Journal",
              "Piece",
              "Compte",
              "Libelle",
              "Debit",
              "Credit",
          ]]
          .fillna("")
          .to_dict(orient="records")
      ),
  }