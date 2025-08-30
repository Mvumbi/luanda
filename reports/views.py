from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.http import HttpResponse
from django.utils import timezone
from datetime import date, timedelta
import pandas as pd
from openpyxl import Workbook # Assurez-vous d'avoir installé openpyxl (pip install openpyxl)

# Import your models
from reports.models import Rapport
from core.models import Boutique
from sales.models import Vente, LigneVente, Facture # Importez les modèles nécessaires

@login_required
def generate_report(request):
    """
    Handles the generation and display of reports.
    """
    if request.method == 'POST':
        type_rapport = request.POST.get('type_rapport')
        boutique_id = request.POST.get('boutique')

        try:
            boutique = Boutique.objects.get(id=boutique_id)
        except Boutique.DoesNotExist:
            messages.error(request, "Boutique introuvable.")
            return redirect('reports:report_view')

        # Define the date range based on the report type
        today = date.today()
        if type_rapport == 'daily':
            start_date = today
            end_date = today
        elif type_rapport == 'weekly':
            # Week starts on Monday (ISO 8601)
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif type_rapport == 'monthly':
            start_date = today.replace(day=1)
            end_date = today
        elif type_rapport == 'annual':
            start_date = today.replace(month=1, day=1)
            end_date = today
        else:
            messages.error(request, "Type de rapport non valide.")
            return redirect('reports:report_view')

        # Check for existing reports
        if Rapport.objects.filter(type_rapport=type_rapport, boutique=boutique, date_debut=start_date, date_fin=end_date).exists():
            messages.warning(request, "Un rapport a déjà été généré pour cette période et cette boutique.")
            return redirect('reports:report_view')

        # **Corrected data calculation:**
        # Get the sales for the period from the Vente model
        ventes_period = Vente.objects.filter(
            boutique=boutique,
            sale_date__date__range=[start_date, end_date]
        )
        
        # Calculate the total revenue
        total_revenue = ventes_period.aggregate(total=Sum('total_amount'))['total'] or 0

        # Calculate the number of distinct sales
        num_sales = ventes_period.count()

        # Create and save the report
        report = Rapport.objects.create(
            type_rapport=type_rapport,
            boutique=boutique,
            date_debut=start_date,
            date_fin=end_date,
            total_revenue=total_revenue,
            num_sales=num_sales
        )
        
        messages.success(request, f"Rapport {report.get_type_rapport_display()} généré avec succès pour {boutique.name}.")
        return redirect('reports:report_list')

    # Display existing reports
    rapports = Rapport.objects.all()
    boutiques = Boutique.objects.all()
    context = {
        'rapports': rapports,
        'boutiques': boutiques,
        'page_title': 'Rapports',
    }
    return render(request, 'reports/report_list.html', context)


@login_required
def download_report(request, report_id):
    """
    Génère et télécharge un rapport au format Excel avec plusieurs onglets.
    """
    # 1. Récupérer le rapport
    rapport = get_object_or_404(Rapport, pk=report_id)

    # 2. Créer une réponse HTTP pour un fichier Excel
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    file_name = f"rapport_{rapport.get_type_rapport_display()}_{rapport.date_debut}_boutique_{rapport.boutique.name}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

    # 3. Utiliser pd.ExcelWriter pour créer un fichier avec plusieurs onglets
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        
        # Onglet 1 : Résumé du rapport
        data_resume = {
            "Type": [rapport.get_type_rapport_display()],
            "Boutique": [rapport.boutique.name],
            "Période": [f"{rapport.date_debut} au {rapport.date_fin}"],
            "Chiffre d'affaires": [rapport.total_revenue],
            "Nombre de ventes": [rapport.num_sales],
            "Généré le": [rapport.generated_at.strftime("%Y-%m-%d %H:%M:%S")],
        }
        df_resume = pd.DataFrame(data_resume)
        df_resume.to_excel(writer, index=False, sheet_name='Résumé du rapport')

        # Onglet 2 : Détail des ventes
        ventes = Vente.objects.filter(
            boutique=rapport.boutique,
            sale_date__date__range=[rapport.date_debut, rapport.date_fin]
        ).prefetch_related('lignes_vente__product').order_by('sale_date')

        lignes_ventes = []
        for vente in ventes:
            for ligne in vente.lignes_vente.all():
                lignes_ventes.append({
                    "Date de vente": vente.sale_date.strftime("%Y-%m-%d %H:%M"),
                    "Numéro de vente": vente.id,
                    "Vendeur": vente.seller.username if vente.seller else 'N/A',
                    "Nom du produit": ligne.product.name,
                    "Quantité": ligne.quantity,
                    "Prix unitaire": ligne.price_at_sale,
                    "Total de la ligne": ligne.get_total_item_price,
                    "Total de la vente": vente.total_amount,
                })
        
        df_detail = pd.DataFrame(lignes_ventes)
        df_detail.to_excel(writer, index=False, sheet_name='Détail des ventes')

    return response