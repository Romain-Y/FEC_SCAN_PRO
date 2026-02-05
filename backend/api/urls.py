from django.urls import path
from .views import test_connexion

urlpatterns = [
    path('test/', test_connexion),
]