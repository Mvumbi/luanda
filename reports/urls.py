# core/urls.py

from django.urls import path
from .views import report_list

app_name = 'reports' # Bonne pratique pour le namespace de l'application

urlpatterns = [
    path('list/', report_list, name='report_list'),
]