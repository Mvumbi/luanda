from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.forms import inlineformset_factory
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F
from django.core.exceptions import ObjectDoesNotExist
import json
from datetime import datetime, timedelta

from .models import Vente, LigneVente
from .forms import VenteForm, LigneVenteForm
from products.models import Produit, Stock, MouvementStock


LigneVenteFormSet = inlineformset_factory(
    Vente,
    LigneVente,
    form=LigneVenteForm,
    fields=['product', 'quantity', 'price_at_sale'],
    extra=1,
    can_delete=True
)

class VenteCreateView(LoginRequiredMixin, CreateView):
    model = Vente
    form_class = VenteForm
    template_name = 'sales/vente_form.html'
    success_url = reverse_lazy('sales:vente_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = LigneVenteFormSet(self.request.POST, self.request.FILES, prefix='form')
        else:
            context['formset'] = LigneVenteFormSet(prefix='form')

        products = Produit.objects.all().values('id', 'price')
        products_prices = {str(p['id']): float(p['price']) for p in products}
        context['products_json'] = json.dumps(products_prices)
        
        context['page_title'] = "Enregistrer une Nouvelle Vente"
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if formset.is_valid():
            with transaction.atomic():
                self.object = form.save(commit=False)
                self.object.seller = self.request.user
                
                # Validation du stock avant la sauvegarde
                for ligne_form in formset.forms:
                    if not ligne_form.is_valid() or not ligne_form.cleaned_data or not ligne_form.cleaned_data.get('product'):
                        continue
                    
                    product_instance = ligne_form.cleaned_data.get('product')
                    quantity_sold = ligne_form.cleaned_data.get('quantity')
                    sale_boutique = self.object.boutique

                    try:
                        stock_item = Stock.objects.select_for_update().get(product=product_instance, boutique=sale_boutique)
                        
                        if stock_item.quantity < quantity_sold:
                            messages.error(self.request, f"Stock insuffisant pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Stock disponible : {stock_item.quantity}, demandé : {quantity_sold}.")
                            return self.form_invalid(form) # Arrête ici si le stock est insuffisant
                    except ObjectDoesNotExist:
                        messages.error(self.request, f"Aucun enregistrement de stock trouvé pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Assurez-vous que le stock a été initialisé.")
                        return self.form_invalid(form) # Arrête ici si le stock n'existe pas

                # Sauvegarde uniquement si toutes les validations sont passées
                self.object.save()

                for ligne_form in formset.forms:
                    if not ligne_form.is_valid() or not ligne_form.cleaned_data or not ligne_form.cleaned_data.get('product'):
                        continue
                        
                    ligne_vente = ligne_form.save(commit=False)
                    ligne_vente.sale = self.object
                    ligne_vente.price_at_sale = ligne_vente.product.price
                    ligne_vente.save()
                    
                    # Mise à jour du stock
                    product_instance = ligne_vente.product
                    quantity_sold = ligne_vente.quantity
                    sale_boutique = self.object.boutique
                    
                    stock_item = Stock.objects.select_for_update().get(product=product_instance, boutique=sale_boutique)
                    stock_item.quantity -= quantity_sold
                    stock_item.save()

                    MouvementStock.objects.create(
                        product=product_instance,
                        boutique=sale_boutique,
                        quantity=quantity_sold,
                        movement_type='exit',
                        user=self.request.user,
                        notes=f"Vente (ID Vente: {self.object.id})"
                    )

                total_amount = self.object.lignes_vente.aggregate(total=Sum(F('quantity') * F('price_at_sale')))['total'] or 0
                self.object.total_amount = total_amount
                self.object.save()
                
                messages.success(self.request, "La vente a été enregistrée avec succès!")
                return HttpResponseRedirect(self.get_success_url())
        else:
            return self.form_invalid(form)
            
    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        context['formset'] = LigneVenteFormSet(self.request.POST, self.request.FILES, instance=self.object if self.object.pk else None, prefix='form')
        return self.render_to_response(context)


class VenteListView(LoginRequiredMixin, ListView):
    model = Vente
    template_name = 'sales/vente_list.html'
    context_object_name = 'ventes'
    ordering = ['-sale_date']

    def get_queryset(self):
        # La vue ne fait que préparer les données, le filtrage est fait en JS
        queryset = super().get_queryset().annotate(
            calculated_total_amount=Sum(F('lignes_vente__quantity') * F('lignes_vente__price_at_sale'))
        )
        return queryset.order_by('-sale_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Liste des Ventes"
        return context
    
class VenteDetailView(LoginRequiredMixin, DetailView):
    model = Vente
    template_name = 'sales/vente_detail.html'
    context_object_name = 'vente'

    def get_context_data(self, **kwargs):
        """
        Ajoute le titre de la page et les lignes de vente associées au contexte.
        """
        context = super().get_context_data(**kwargs)
        vente_id = self.object.id if self.object else "N/A"
        context['page_title'] = f"Détails de la Vente #{vente_id}"
        context['items'] = self.object.lignes_vente.all()
        return context