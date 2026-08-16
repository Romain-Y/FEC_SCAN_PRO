from django.db import models
from django.contrib.auth.models import User

class DossierClient(models.Model):
    nom = models.CharField(max_length=255, verbose_name="Nom du client")
    siren = models.CharField(max_length=9, db_index=True, verbose_name="Numéro SIREN")
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dossier Client"
        verbose_name_plural = "Dossiers Clients"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.siren})"


class AuditFEC(models.Model):
    STATUT_CHOICES = [
        ('CONFORME', 'Conforme'),
        ('AVERTISSEMENT', 'Anomalies détectées'),
        ('NON_CONFORME', 'Rejet fiscal potentiel'),
    ]

    dossier = models.ForeignKey(
        DossierClient, 
        on_delete=models.CASCADE, 
        related_name='audits'
    )
    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audits_effectues'
    )
    date_audit = models.DateTimeField(auto_now_add=True)
    fichier_nom = models.CharField(max_length=255)
    exercice_annee = models.IntegerField(null=True, blank=True, verbose_name="Millésime / Année")
    
    # Indicateurs d'intégrité DGFiP
    nb_lignes_total = models.PositiveIntegerField(default=0)
    equilibre_debit_credit = models.BooleanField(default=True)
    structure_18_colonnes_valide = models.BooleanField(default=True)
    
    # KPIs d'analyse
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='CONFORME')
    total_anomalies = models.PositiveIntegerField(default=0)
    montant_risque = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Audit FEC"
        verbose_name_plural = "Audits FEC"
        ordering = ['-date_audit']

    def __str__(self):
        return f"Audit #{self.id} - {self.dossier.nom} ({self.date_audit.strftime('%d/%m/%Y')})"


class Anomalie(models.Model):
    GRAVITE_CHOICES = [
        ('CRITIQUE', 'Critique'),
        ('HAUTE', 'Haute'),
        ('MOYENNE', 'Moyenne'),
    ]
    
    audit = models.ForeignKey(
        AuditFEC, 
        on_delete=models.CASCADE, 
        related_name='anomalies'
    )
    gravite = models.CharField(max_length=20, choices=GRAVITE_CHOICES, db_index=True)
    type_anomalie = models.CharField(max_length=255)
    
    # Données extraites du FEC
    date_ecriture = models.DateField(null=True, blank=True)
    journal = models.CharField(max_length=50, null=True, blank=True)
    piece = models.CharField(max_length=100, null=True, blank=True)
    compte = models.CharField(max_length=50, db_index=True)
    libelle_ecriture = models.CharField(max_length=255, null=True, blank=True)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = "Anomalie"
        verbose_name_plural = "Anomalies"
        ordering = ['-gravite', 'compte']

    def __str__(self):
        return f"{self.gravite} - {self.type_anomalie} (Compte {self.compte})"