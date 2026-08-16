from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    test_connexion,
    upload_fec,
    historique_audits,
    export_excel,
    export_pdf,
    register_comptable  # <-- Import de la nouvelle vue
)

urlpatterns = [
    path('test/', test_connexion, name='test_connexion'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', register_comptable, name='register_comptable'), # <-- Route d'inscription
    path('upload/', upload_fec, name='upload_fec'),
    path('historique/', historique_audits, name='historique_audits'),
    path('export/excel/', export_excel, name='export_excel'),
    path('export/pdf/', export_pdf, name='export_pdf'),
]