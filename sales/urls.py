# sales/urls.py

from django.urls import path
from sales import views # C'est le bon import si sales/urls.py est dans l'application 'sales'

app_name = 'sales'

urlpatterns = [
    path('list/', views.VenteListView.as_view(), name='vente_list'),
    path('add/', views.VenteCreateView.as_view(), name='vente_create'),
    path('<int:pk>/', views.VenteDetailView.as_view(), name='vente_detail'),
    # Ajoute les URLs pour la modification et la suppression si tu ne les as pas déjà
    path('<int:pk>/edit/', views.VenteUpdateView.as_view(), name='vente_edit'), # Ou 'vente_update'
    path('<int:pk>/delete/', views.VenteDeleteView.as_view(), name='vente_delete'),
]