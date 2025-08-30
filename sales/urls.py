# sales/urls.py
from django.urls import path
from sales import views 

app_name = 'sales' # Le nom de l'application est 'sales'

urlpatterns = [
    path('list/', views.VenteListView.as_view(), name='vente_list'),
    path('add/', views.VenteCreateView.as_view(), name='vente_create'),
    path('<int:pk>/', views.VenteDetailView.as_view(), name='vente_detail'), # Le nom est 'vente_detail'
]