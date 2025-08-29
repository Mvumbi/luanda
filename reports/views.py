# reports/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import RapportMensuel # Importez le modèle RapportMensuel

@login_required
def report_list(request):
    # Récupère tous les rapports mensuels et les ordonne par année puis mois (du plus récent au plus ancien)
    reports = RapportMensuel.objects.all().order_by('-year', '-month')
    context = {
        'reports': reports,
        'page_title': "Rapports Mensuels",
    }
    return render(request, 'reports/report_list.html', context)