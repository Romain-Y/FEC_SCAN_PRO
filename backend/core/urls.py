from django.contrib import admin
from django.urls import path, include  # <--- As-tu bien ajouté ', include' ici ?

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')), # <--- Cette ligne est-elle bien là ?
]