# sales/views.py

from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.forms import inlineformset_factory
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum

# Importe tes modèles de vente et de produits
from .models import Vente, LigneVente
from .forms import VenteForm, LigneVenteForm
from products.models import Produit, Stock, MouvementStock # Assure-toi d'importer tous ces modèles

# Création du Formset pour les lignes de vente
LigneVenteFormSet = inlineformset_factory(
    Vente,
    LigneVente,
    form=LigneVenteForm,
    fields=['product', 'quantity', 'price_at_sale'],
    extra=1,
    can_delete=True
)

# --- Vues de gestion des ventes ---

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
        import json
        context['products_json'] = json.dumps(products_prices)
        
        context['page_title'] = "Enregistrer une Nouvelle Vente"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            # Enregistrer la vente principale (sans commit pour ajouter le vendeur)
            self.object = form.save(commit=False)
            self.object.seller = self.request.user # L'utilisateur connecté est le vendeur
            self.object.save()

            # Initialiser le formset avec l'instance de la vente que l'on vient de créer
            formset = LigneVenteFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='form')
            
            # Vérifier la validité du formset (lignes de vente)
            if formset.is_valid():
                for ligne_form in formset:
                    if not ligne_form.cleaned_data.get('DELETE', False):
                        ligne_vente = ligne_form.save(commit=False)
                        ligne_vente.sale = self.object
                        ligne_vente.price_at_sale = ligne_vente.product.price
                        ligne_vente.save()

                        product_instance = ligne_vente.product
                        quantity_sold = ligne_vente.quantity
                        sale_boutique = self.object.boutique

                        try:
                            stock_item = Stock.objects.get(product=product_instance, boutique=sale_boutique)
                            
                            if stock_item.quantity < quantity_sold:
                                messages.error(self.request, f"Stock insuffisant pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Stock disponible : {stock_item.quantity}, demandé : {quantity_sold}.")
                                transaction.set_rollback(True)
                                return self.render_to_response(self.get_context_data(form=form, formset=formset))

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
                        except Stock.DoesNotExist:
                            messages.error(self.request, f"Aucun enregistrement de stock trouvé pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Assurez-vous que le stock a été initialisé.")
                            transaction.set_rollback(True)
                            return self.render_to_response(self.get_context_data(form=form, formset=formset))
                
                # Sauvegarder les lignes de vente (nécessaire pour les suppressions)
                formset.save()
                
                # RECALCULER et mettre à jour le montant total de la vente
                total_amount = self.object.lignes_vente.aggregate(total=Sum(F('quantity') * F('price_at_sale')))['total'] or 0
                self.object.total_amount = total_amount
                self.object.save() # Sauvegarde l'objet Vente mis à jour
                
                messages.success(self.request, "La vente a été enregistrée avec succès!")
                return HttpResponseRedirect(self.get_success_url())
            else:
                # Si le formset n'est pas valide, retourner le formulaire avec les erreurs
                # Le transaction.atomic() gérera le rollback si l'une des validations échoue
                return self.render_to_response(self.get_context_data(form=form, formset=formset))

# --- Vues de list, détail et suppression non modifiées ---
class VenteListView(LoginRequiredMixin, ListView):
    model = Vente
    template_name = 'sales/vente_list.html'
    context_object_name = 'ventes'
    ordering = ['-sale_date']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Liste des Ventes"
        return context

class VenteDetailView(LoginRequiredMixin, DetailView):
    model = Vente
    template_name = 'sales/vente_detail.html'
    context_object_name = 'vente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Détails de la Vente #{self.object.id}"
        context['lignes_vente'] = self.object.lignes_vente.all()
        return context

class VenteUpdateView(LoginRequiredMixin, UpdateView):
    model = Vente
    form_class = VenteForm
    template_name = 'sales/vente_form.html'
    success_url = reverse_lazy('sales:vente_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = LigneVenteFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='form')
        else:
            context['formset'] = LigneVenteFormSet(instance=self.object, prefix='form')
        
        products = Produit.objects.all().values('id', 'price')
        products_prices = {str(p['id']): float(p['price']) for p in products}
        import json
        context['products_json'] = json.dumps(products_prices)

        context['page_title'] = f"Modifier la Vente #{self.object.id}"
        return context

    def form_valid(self, form):
        with transaction.atomic():
            initial_quantities = {
                ligne.id: ligne.quantity
                for ligne in self.object.lignes_vente.all()
            }

            self.object = form.save(commit=False)
            self.object.save()

            formset = LigneVenteFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='form')

            if formset.is_valid():
                for ligne_form in formset:
                    if ligne_form.cleaned_data.get('DELETE', False):
                        if ligne_form.instance.id:
                            product_instance = ligne_form.instance.product
                            quantity_returned = initial_quantities.get(ligne_form.instance.id, 0)
                            sale_boutique = self.object.boutique

                            try:
                                stock_item = Stock.objects.get(product=product_instance, boutique=sale_boutique)
                                stock_item.quantity += quantity_returned
                                stock_item.save()
                                MouvementStock.objects.create(
                                    product=product_instance,
                                    boutique=sale_boutique,
                                    quantity=quantity_returned,
                                    movement_type='entry',
                                    user=self.request.user,
                                    notes=f"Annulation ligne vente (ID Vente: {self.object.id})"
                                )
                            except Stock.DoesNotExist:
                                messages.error(self.request, f"Erreur de stock : pas d'enregistrement pour {product_instance.name} à {sale_boutique.name} lors de la suppression.")
                                transaction.set_rollback(True)
                                return self.render_to_response(self.get_context_data(form=form, formset=formset))
                            ligne_form.instance.delete()
                    else:
                        ligne_vente = ligne_form.save(commit=False)
                        ligne_vente.sale = self.object
                        ligne_vente.price_at_sale = ligne_vente.product.price

                        product_instance = ligne_vente.product
                        sale_boutique = self.object.boutique

                        try:
                            stock_item = Stock.objects.get(product=product_instance, boutique=sale_boutique)
                            
                            if ligne_vente.id:
                                old_quantity = initial_quantities.get(ligne_vente.id, 0)
                                quantity_change = ligne_vente.quantity - old_quantity

                                if stock_item.quantity < quantity_change:
                                    messages.error(self.request, f"Stock insuffisant pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Stock disponible : {stock_item.quantity}, demandé en plus : {quantity_change}.")
                                    transaction.set_rollback(True)
                                    return self.render_to_response(self.get_context_data(form=form, formset=formset))

                                stock_item.quantity -= quantity_change
                                stock_item.save()

                                if quantity_change > 0:
                                    MouvementStock.objects.create(
                                        product=product_instance,
                                        boutique=sale_boutique,
                                        quantity=quantity_change,
                                        movement_type='exit',
                                        user=self.request.user,
                                        notes=f"Modification vente (ID Vente: {self.object.id}) - Augmentation qté"
                                    )
                                elif quantity_change < 0:
                                    MouvementStock.objects.create(
                                        product=product_instance,
                                        boutique=sale_boutique,
                                        quantity=abs(quantity_change),
                                        movement_type='entry',
                                        user=self.request.user,
                                        notes=f"Modification vente (ID Vente: {self.object.id}) - Diminution qté / Retour"
                                    )
                            else:
                                if stock_item.quantity < ligne_vente.quantity:
                                    messages.error(self.request, f"Stock insuffisant pour le nouveau produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Stock disponible : {stock_item.quantity}, demandé : {ligne_vente.quantity}.")
                                    transaction.set_rollback(True)
                                    return self.render_to_response(self.get_context_data(form=form, formset=formset))
                                
                                stock_item.quantity -= ligne_vente.quantity
                                stock_item.save()
                                MouvementStock.objects.create(
                                    product=product_instance,
                                    boutique=sale_boutique,
                                    quantity=ligne_vente.quantity,
                                    movement_type='exit',
                                    user=self.request.user,
                                    notes=f"Nouvelle ligne ajoutée à vente (ID Vente: {self.object.id})"
                                )

                        except Stock.DoesNotExist:
                            messages.error(self.request, f"Aucun enregistrement de stock trouvé pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'.")
                            transaction.set_rollback(True)
                            return self.render_to_response(self.get_context_data(form=form, formset=formset))
                        
                        ligne_vente.save()
                
                # RECALCULER et mettre à jour le montant total de la vente
                total_amount = self.object.lignes_vente.aggregate(total=Sum(F('quantity') * F('price_at_sale')))['total'] or 0
                self.object.total_amount = total_amount
                self.object.save() # Sauvegarde l'objet Vente mis à jour

                messages.success(self.request, "La vente a été mise à jour avec succès!")
                return HttpResponseRedirect(self.get_success_url())
            else:
                return self.render_to_response(self.get_context_data(form=form, formset=formset))

class VenteDeleteView(LoginRequiredMixin, DeleteView):
    model = Vente
    template_name = 'sales/vente_confirm_delete.html'
    success_url = reverse_lazy('sales:vente_list')
    context_object_name = 'vente'

    def form_valid(self, form):
        with transaction.atomic():
            sale_boutique = self.object.boutique
            for ligne_vente in self.object.lignes_vente.all():
                try:
                    stock_item = Stock.objects.get(product=ligne_vente.product, boutique=sale_boutique)
                    stock_item.quantity += ligne_vente.quantity
                    stock_item.save()
                    
                    MouvementStock.objects.create(
                        product=ligne_vente.product,
                        boutique=sale_boutique,
                        quantity=ligne_vente.quantity,
                        movement_type='entry',
                        user=self.request.user,
                        notes=f"Annulation vente complète (ID Vente: {self.object.id})"
                    )
                except Stock.DoesNotExist:
                    messages.error(self.request, f"Erreur de stock lors de la suppression : pas d'enregistrement pour {ligne_vente.product.name} à {sale_boutique.name}.")
                    transaction.set_rollback(True)
                    return self.render_to_response(self.get_context_data())
            messages.success(self.request, "La vente a été supprimée et les stocks mis à jour.")
            return super().form_valid(form)