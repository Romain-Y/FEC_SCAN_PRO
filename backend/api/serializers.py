from rest_framework import serializers
from .models import DossierClient, AuditFEC, Anomalie

class DossierClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = DossierClient
        fields = '__all__'

class AuditFECSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditFEC
        fields = '__all__'

class AnomalieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anomalie
        fields = '__all__'