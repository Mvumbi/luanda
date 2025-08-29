# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from core.forms import BoutiqueForm
from .models import Boutique
from products.models import Produit, Stock, MouvementStock
from django.db.models import Sum
from datetime import date

@login_required
def home_view(request):
    # Logique pour la page d'accueil (KPIs)

    # KPI 1: Total boutiques
    total_boutiques = Boutique.objects.count()

    # KPI 2: Total produits en stock
    total_stock_value = Stock.objects.aggregate(Sum('quantity'))['quantity__sum']
    total_produits_stock = total_stock_value if total_stock_value is not None else 0

    # KPI 3: Ventes du mois en cours
    today = date.today()
    
    ventes_du_mois = MouvementStock.objects.filter(
        movement_type='exit',
        timestamp__year=today.year,
        timestamp__month=today.month
    ).count()

    # KPI 4: Alertes de stock (nombre de stocks sous le seuil d'alerte)
    seuil_alerte = 5  # Tu peux changer cette valeur selon tes besoins
    alertes_stock = Stock.objects.filter(quantity__lte=seuil_alerte).count()
    
    context = {
        'page_title': "Tableau de Bord",
        'user': request.user,
        'total_boutiques': total_boutiques,
        'total_produits_stock': total_produits_stock,
        'ventes_du_mois': ventes_du_mois,
        'alertes_stock': alertes_stock,
    }
    return render(request, 'core/home.html', context)

@login_required
def boutique_list(request):
    boutiques = Boutique.objects.all().order_by('name')
    context = {
        'boutiques': boutiques,
        'page_title': "Liste des Boutiques",
    }
    return render(request, 'core/boutique_list.html', context) # Nouveau template

@login_required
def boutique_create(request):
    if request.method == 'POST':
        form = BoutiqueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Boutique créée avec succès !")
            return redirect('core:boutique_list')
    else:
        form = BoutiqueForm()
    context = {
        'form': form,
        'page_title': "Ajouter une nouvelle boutique",
    }
    return render(request, 'core/boutique_form.html', context) # Nouveau template, réutilisé pour update

@login_required
def boutique_detail(request, pk):
    boutique = get_object_or_404(Boutique, pk=pk)
    context = {
        'boutique': boutique,
        'page_title': f"Détails de la boutique : {boutique.name}",
    }
    return render(request, 'core/boutique_detail.html', context) # Nouveau template

@login_required
def boutique_update(request, pk):
    boutique = get_object_or_404(Boutique, pk=pk)
    if request.method == 'POST':
        form = BoutiqueForm(request.POST, instance=boutique)
        if form.is_valid():
            form.save()
            messages.success(request, f"La boutique '{boutique.name}' a été mise à jour.")
            return redirect('core:boutique_detail', pk=boutique.pk)
    else:
        form = BoutiqueForm(instance=boutique)
    context = {
        'form': form,
        'boutique': boutique,
        'page_title': f"Modifier la boutique : {boutique.name}",
    }
    return render(request, 'core/boutique_form.html', context) # Réutilise le template de formulaire

@login_required
def boutique_delete(request, pk):
    boutique = get_object_or_404(Boutique, pk=pk)
    if request.method == 'POST':
        boutique.delete()
        messages.success(request, f"La boutique '{boutique.name}' a été supprimée.")
        return redirect('core:boutique_list')
    context = {
        'boutique': boutique,
        'page_title': f"Confirmer la suppression de : {boutique.name}",
    }
    return render(request, 'core/boutique_confirm_delete.html', context) # Nouveau template