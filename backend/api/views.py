import json
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User

from .audit_logic import executer_audit_complet
from .models import DossierClient, AuditFEC, Anomalie

# --- IMPORTS POUR LE PDF ---
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


@api_view(['POST'])
@permission_classes([AllowAny])
def register_comptable(request):
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response({'error': "L'identifiant et le mot de passe sont obligatoires."}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': "Cet identifiant est déjà utilisé par un autre collaborateur."}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    user.save()

    return Response({'success': True, 'message': 'Compte collaborateur créé avec succès.'})


@api_view(['GET'])
def test_connexion(request):
    return Response({"message": "Connexion API opérationnelle."})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historique_audits(request):
    audits = AuditFEC.objects.filter(utilisateur=request.user).select_related('dossier').order_by('-date_audit')
    
    data = []
    for audit in audits:
        data.append({
            "id": audit.id,
            "client": f"{audit.dossier.nom} ({audit.dossier.siren or 'N/A'})",
            "fichier": audit.fichier_nom,
            "date": audit.date_audit.strftime('%d/%m/%Y %H:%M'),
            "exercice_annee": audit.exercice_annee,
            "total_anomalies": audit.total_anomalies,
            "montant_risque": float(audit.montant_risque),
            "equilibre_debit_credit": audit.equilibre_debit_credit,
            "structure_18_colonnes_valide": audit.structure_18_colonnes_valide
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_fec(request):
    if 'fichier_fec' not in request.FILES:
        return Response({"success": False, "error": "Aucun fichier reçu."}, status=400)
    
    fichier = request.FILES['fichier_fec']
    nom_client = request.POST.get('nom_client', 'Client par défaut').strip()
    siren = request.POST.get('siren', '000000000').strip()
    
    # 1. Exécution du moteur d'audit
    resultat_audit = executer_audit_complet(fichier)
    
    if not resultat_audit.get('success', False):
        return Response(resultat_audit, status=400)

    # 2. Gestion du dossier client
    dossier_client, _ = DossierClient.objects.get_or_create(
        siren=siren,
        defaults={'nom': nom_client}
    )
    if dossier_client.nom != nom_client:
        dossier_client.nom = nom_client
        dossier_client.save()

    stats = resultat_audit.get('stats', {})
    metadonnees = resultat_audit.get('metadonnees', {})
    
    # 3. Enregistrement de l'audit
    audit_enregistre = AuditFEC.objects.create(
        dossier=dossier_client,
        utilisateur=request.user,
        fichier_nom=fichier.name,
        exercice_annee=metadonnees.get('exercice_annee'),
        nb_lignes_total=metadonnees.get('nb_lignes', 0),
        equilibre_debit_credit=metadonnees.get('equilibre', True),
        structure_18_colonnes_valide=metadonnees.get('structure_valide', True),
        total_anomalies=stats.get('total_anomalies', 0),
        montant_risque=stats.get('montant_risque', 0.0)
    )
    
    # 4. Enregistrement en masse des anomalies
    anomalies_liste = resultat_audit.get('anomalies', [])
    anomalies_a_creer = []

    for ano in anomalies_liste:
        anomalies_a_creer.append(
            Anomalie(
                audit=audit_enregistre,
                gravite=ano.get('Gravite', 'MOYENNE'),
                type_anomalie=ano.get('Type_Anomalie', 'Inconnu'),
                date_ecriture=ano.get('Date_str') if ano.get('Date_str') else None,
                journal=ano.get('Journal', ''),
                piece=ano.get('Piece', ''),
                compte=str(ano.get('Compte', '')),
                libelle_ecriture=ano.get('Libelle', ''),
                debit=ano.get('Debit', 0.0),
                credit=ano.get('Credit', 0.0)
            )
        )
    
    if anomalies_a_creer:
        Anomalie.objects.bulk_create(anomalies_a_creer)

    return Response(resultat_audit)


@api_view(['POST'])
def export_excel(request):
    try:
        data = json.loads(request.body)
        anomalies = data.get('anomalies', [])
        stats = data.get('stats', {})

        output = BytesIO()

        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            synthese_data = {
                'Total Anomalies': [stats.get('total_anomalies', 0)],
                'Montant Total Risque (€)': [stats.get('montant_risque', 0.0)],
            }
            pd.DataFrame(synthese_data).to_excel(writer, sheet_name='SYNTHESE', index=False)

            if anomalies:
                df_anomalies = pd.DataFrame(anomalies)
                cols_finales = ['Gravite', 'Type_Anomalie', 'Date_str', 'Journal', 'Piece', 'Compte', 'Libelle', 'Debit', 'Credit']
                cols_existantes = [c for c in cols_finales if c in df_anomalies.columns]
                
                df_anomalies[cols_existantes].to_excel(writer, sheet_name='DETAILS', index=False)
                worksheet = writer.sheets['DETAILS']
                for i, col in enumerate(cols_existantes):
                    worksheet.set_column(i, i, 20)
            else:
                pd.DataFrame(["Aucune anomalie"]).to_excel(writer, sheet_name='DETAILS', header=False, index=False)

        output.seek(0)
        response = HttpResponse(
            output.getvalue(), 
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="Rapport_Audit_FEC.xlsx"'
        return response

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(['POST'])
def export_pdf(request):
    try:
        data = json.loads(request.body)
        anomalies = data.get('anomalies', [])
        stats = data.get('stats', {})

        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4))
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("Rapport d'Audit FEC - Synthèse", styles['Title']))
        elements.append(Spacer(1, 15))
        
        texte_stats = f"<b>Total des anomalies détectées :</b> {stats.get('total_anomalies', 0)} <br/>"
        texte_stats += f"<b>Montant global du risque financier :</b> {stats.get('montant_risque', 0.0)} €"
        elements.append(Paragraph(texte_stats, styles['Normal']))
        elements.append(Spacer(1, 20))

        if anomalies:
            table_data = [['Gravité', 'Règle enfreinte', 'JRN', 'Pièce', 'Compte', 'Libellé', 'Débit', 'Crédit']]
            
            for ano in anomalies[:150]:  # Limite pour optimiser le rendu PDF
                table_data.append([
                    str(ano.get('Gravite', '')),
                    str(ano.get('Type_Anomalie', ''))[:30],
                    str(ano.get('Journal', '')),
                    str(ano.get('Piece', ''))[:15],
                    str(ano.get('Compte', '')),
                    str(ano.get('Libelle', ''))[:25],
                    str(ano.get('Debit', 0.0)),
                    str(ano.get('Credit', 0.0))
                ])

            t = Table(table_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('BOTTOMPADDING', (0,0), (-1,0), 8),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#f8fafc")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("Aucune anomalie détectée. Fichier conforme.", styles['Normal']))

        doc.build(elements)
        output.seek(0)
        
        response = HttpResponse(output.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Rapport_Audit_FEC.pdf"'
        return response

    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)