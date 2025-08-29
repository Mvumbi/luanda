# core/urls.py

from django.urls import path
from .views import generate_report, download_report

app_name = 'reports' # Bonne pratique pour le namespace de l'application

urlpatterns = [
    path('list/', generate_report, name='report_list'),
    path('download/<int:report_id>/', download_report, name='download_report'),
]