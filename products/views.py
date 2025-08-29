# products/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required # Gardé pour les vues fonctionnelles si tu les conserves
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin # Mixin pour les vues basées sur des classes
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Produit, Stock, MouvementStock
from django.contrib.auth import get_user_model # Assure-toi que ce chemin est correct pour ton modèle User
from core.models import Boutique
from django.db import transaction
from .forms import ProduitForm, StockForm, MouvementStockForm

User = get_user_model()


@login_required
def product_list(request):
    products = Produit.objects.all().order_by('name')
    context = {
        'products': products,
        'page_title': "Liste des produits",
    }
    return render(request, 'products/product_list.html', context)

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProduitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit ajouté avec succès.")
            return redirect('products:product_list')
    else:
        form = ProduitForm()
    context = {
        'form': form,
        'page_title': "Créer un nouveau produit",
    }
    return render(request, 'products/product_form.html', context)

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Produit, pk=pk)
    context = {
        'product': product,
        'page_title': f"Détails du produit: {product.name}",
    }
    return render(request, 'products/product_detail.html', context)

@login_required
def product_update(request, pk):
    product = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        form = ProduitForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit mis à jour avec succès.")
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProduitForm(instance=product)
    context = {
        'form': form,
        'product': product,
        'page_title': f"Modifier le produit: {product.name}",
    }
    return render(request, 'products/product_form.html', context)

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, f"Le produit '{product.name}' a été supprimé avec succès.")
        return redirect('products:product_list')
    context = {
        'product': product,
        'page_title': f"Confirmer la suppression de: {product.name}",
    }
    return render(request, 'products/product_confirm_delete.html', context)


# --- Vues pour la gestion des Stocks (Vues basées sur des classes) ---
# REMARQUE : La fonction 'stock_list' a été supprimée car elle est remplacée par StockListView (classe).

class StockListView(LoginRequiredMixin, ListView):
    model = Stock
    template_name = 'products/stock_list.html'
    context_object_name = 'stocks'
    paginate_by = 15

    def get_queryset(self):
        return Stock.objects.select_related('product', 'boutique').order_by('product__name', 'boutique__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Gestion des Stocks"
        return context
class StockCreateView(LoginRequiredMixin, CreateView):
    model = Stock
    form_class = StockForm
    template_name = 'products/stock_form.html'
    success_url = reverse_lazy('products:stock_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Ajouter un Stock"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Récupère l'instance réelle de l'utilisateur connecté
            # Utilise request.user.pk pour garantir une instance User concrète, pas un SimpleLazyObject
            # Le LoginRequiredMixin garantit que self.request.user est authentifié.
            user_instance_for_fk = User.objects.get(pk=self.request.user.pk) # <-- MODIFICATION CLÉ

            MouvementStock.objects.create(
                product=self.object.product,
                boutique=self.object.boutique,
                quantity=self.object.quantity,
                movement_type='entry',
                user=user_instance_for_fk, # <-- Assigne l'instance concrète ici
                notes="Initialisation du stock"
            )
            messages.success(self.request, "Le stock a été ajouté et le mouvement enregistré avec succès.")
            return response

class StockUpdateView(LoginRequiredMixin, UpdateView):
    model = Stock
    form_class = StockForm
    template_name = 'products/stock_form.html'
    success_url = reverse_lazy('products:stock_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Modifier le Stock"
        return context

    def form_valid(self, form):
        old_quantity = self.get_object().quantity
        new_quantity = form.instance.quantity
        
        quantity_diff = new_quantity - old_quantity
        
        with transaction.atomic():
            response = super().form_valid(form)

            if quantity_diff != 0: 
                movement_type = 'entry' if quantity_diff > 0 else 'exit'
                notes = (
                    f"Augmentation de stock de {quantity_diff} unités." 
                    if quantity_diff > 0 
                    else f"Diminution de stock de {abs(quantity_diff)} unités."
                )
                
                # Récupère l'instance réelle de l'utilisateur connecté
                user_instance_for_fk = User.objects.get(pk=self.request.user.pk) # <-- MODIFICATION CLÉ

                MouvementStock.objects.create(
                    product=self.object.product,
                    boutique=self.object.boutique,
                    quantity=abs(quantity_diff),
                    movement_type=movement_type,
                    user=user_instance_for_fk, # <-- Assigne l'instance concrète ici
                    notes=notes
                )
                messages.success(self.request, "Le stock a été mis à jour et le mouvement enregistré avec succès.")
            else:
                messages.info(self.request, "Le stock a été mis à jour (aucune modification de quantité).")
            return response

class MouvementStockListView(LoginRequiredMixin, ListView):
    model = MouvementStock
    template_name = 'products/mouvement_stock_list.html'
    context_object_name = 'mouvements'
    paginate_by = 20

    def get_queryset(self):
        return MouvementStock.objects.select_related('product', 'boutique', 'user').order_by('-timestamp')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Historique des Mouvements de Stock"
        return context