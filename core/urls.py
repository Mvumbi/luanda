# core/urls.py

from django.urls import path
from core import views

app_name = 'core' # Bonne pratique pour le namespace de l'application

urlpatterns = [
    path('', views.home_view, name='home'),  # Page d'accueil
    path('boutiques/', views.boutique_list, name='boutique_list'),
    path('boutiques/create/', views.boutique_create, name='boutique_create'),
    path('boutiques/<int:pk>/', views.boutique_detail, name='boutique_detail'),
    path('boutiques/<int:pk>/update/', views.boutique_update, name='boutique_update'),
    path('boutiques/<int:pk>/delete/', views.boutique_delete, name='boutique_delete'),
]

