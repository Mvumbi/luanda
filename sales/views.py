from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.forms import inlineformset_factory
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin

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
            # Si le formulaire principal a été soumis (requête POST), lier les données du POST au formset
            context['formset'] = LigneVenteFormSet(self.request.POST, self.request.FILES, prefix='form')
        else:
            # Sinon (requête GET), créer un formset vide ou pré-rempli
            context['formset'] = LigneVenteFormSet(prefix='form')

        # Passer les prix des produits pour le JavaScript
        # Ceci est utilisé par le JS pour remplir le champ de prix automatiquement
        products = Produit.objects.all().values('id', 'price')
        products_prices = {str(p['id']): float(p['price']) for p in products}
        import json # S'assurer que json est importé
        context['products_json'] = json.dumps(products_prices)
        
        context['page_title'] = "Enregistrer une Nouvelle Vente"
        return context

    def form_valid(self, form):
        # Enregistrer la vente principale (sans commit pour ajouter le vendeur)
        self.object = form.save(commit=False)
        self.object.seller = self.request.user # L'utilisateur connecté est le vendeur
        self.object.save()

        # Initialiser le formset avec l'instance de la vente que l'on vient de créer
        formset = LigneVenteFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='form')
        
        # Vérifier la validité du formset (lignes de vente)
        if formset.is_valid():
            with transaction.atomic(): # Assure que toutes les opérations réussissent ou échouent ensemble
                for ligne_form in formset:
                    # Ne traiter que les lignes qui ne sont pas marquées pour suppression
                    if not ligne_form.cleaned_data.get('DELETE', False):
                        ligne_vente = ligne_form.save(commit=False)
                        ligne_vente.sale = self.object
                        # Le prix de vente est toujours le prix actuel du produit, même si JS l'a pré-rempli
                        ligne_vente.price_at_sale = ligne_vente.product.price
                        ligne_vente.save()

                        # Gérer la décrémentation du stock via le modèle Stock
                        product_instance = ligne_vente.product
                        quantity_sold = ligne_vente.quantity
                        sale_boutique = self.object.boutique # La boutique associée à la vente principale

                        try:
                            # Tenter de récupérer l'objet Stock pour ce produit et cette boutique
                            stock_item = Stock.objects.get(product=product_instance, boutique=sale_boutique)
                            
                            # Vérifier si la quantité en stock est suffisante avant de décrémenter
                            if stock_item.quantity < quantity_sold:
                                messages.error(self.request, f"Stock insuffisant pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Stock disponible : {stock_item.quantity}, demandé : {quantity_sold}.")
                                transaction.set_rollback(True) # Force l'annulation de toutes les opérations de cette transaction
                                return self.render_to_response(self.get_context_data(form=form, formset=formset)) # Retourne le formulaire avec les erreurs

                            # Décrémenter la quantité en stock et sauvegarder
                            stock_item.quantity -= quantity_sold
                            stock_item.save()

                            # Enregistrer un mouvement de stock de type 'Sortie'
                            MouvementStock.objects.create(
                                product=product_instance,
                                boutique=sale_boutique,
                                quantity=quantity_sold,
                                movement_type='exit',
                                user=self.request.user,
                                notes=f"Vente (ID Vente: {self.object.id})"
                            )

                        except Stock.DoesNotExist:
                            # Si aucun enregistrement de stock n'est trouvé pour le produit/boutique
                            messages.error(self.request, f"Aucun enregistrement de stock trouvé pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Assurez-vous que le stock a été initialisé.")
                            transaction.set_rollback(True) # Force l'annulation
                            return self.render_to_response(self.get_context_data(form=form, formset=formset))
                
                # Sauvegarde finale des lignes de vente (nécessaire pour les suppressions gérées par le formset)
                formset.save()
            
            messages.success(self.request, "La vente a été enregistrée avec succès!")
            return HttpResponseRedirect(self.get_success_url())
        else:
            # Si le formset n'est pas valide, afficher les erreurs et retourner le formulaire
            messages.error(self.request, "Veuillez corriger les erreurs dans les articles de la vente.")
            return self.render_to_response(self.get_context_data(form=form, formset=formset))


class VenteListView(LoginRequiredMixin, ListView):
    model = Vente
    template_name = 'sales/vente_list.html'
    context_object_name = 'ventes'
    ordering = ['-sale_date'] # Les ventes les plus récentes en premier
    
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
        # Récupère les lignes de vente associées pour les afficher dans les détails
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
            # Si le formulaire a été soumis, lier les données au formset avec l'instance
            context['formset'] = LigneVenteFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='form')
        else:
            # Sinon (GET), initialiser le formset avec les données existantes de la vente
            context['formset'] = LigneVenteFormSet(instance=self.object, prefix='form')
        
        # Passer les prix des produits pour le JavaScript
        products = Produit.objects.all().values('id', 'price')
        products_prices = {str(p['id']): float(p['price']) for p in products}
        import json
        context['products_json'] = json.dumps(products_prices)

        context['page_title'] = f"Modifier la Vente #{self.object.id}"
        return context

    def form_valid(self, form):
        # Sauvegarder les quantités initiales des lignes de vente existantes avant toute modification
        # Cela nous permet de calculer les ajustements de stock nécessaires
        initial_quantities = {
            ligne.id: ligne.quantity
            for ligne in self.object.lignes_vente.all()
        }

        self.object = form.save(commit=False)
        self.object.save() # Sauvegarde le formulaire de vente principal

        formset = LigneVenteFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='form')

        if formset.is_valid():
            with transaction.atomic():
                # Parcourir chaque ligne du formset pour gérer les ajouts, modifications et suppressions
                for ligne_form in formset:
                    if ligne_form.cleaned_data.get('DELETE', False):
                        # La ligne est marquée pour suppression
                        if ligne_form.instance.id: # S'il s'agit d'une ligne existante (pas une nouvelle ligne vide)
                            product_instance = ligne_form.instance.product
                            quantity_returned = initial_quantities.get(ligne_form.instance.id, 0) # La quantité initialement vendue
                            sale_boutique = self.object.boutique

                            try:
                                stock_item = Stock.objects.get(product=product_instance, boutique=sale_boutique)
                                stock_item.quantity += quantity_returned # Rajoute la quantité au stock
                                stock_item.save()
                                MouvementStock.objects.create(
                                    product=product_instance,
                                    boutique=sale_boutique,
                                    quantity=quantity_returned,
                                    movement_type='entry', # Mouvement d'entrée car la vente est annulée pour cette ligne
                                    user=self.request.user,
                                    notes=f"Annulation ligne vente (ID Vente: {self.object.id})"
                                )
                            except Stock.DoesNotExist:
                                messages.error(self.request, f"Erreur de stock : pas d'enregistrement pour {product_instance.name} à {sale_boutique.name} lors de la suppression.")
                                transaction.set_rollback(True)
                                return self.render_to_response(self.get_context_data(form=form, formset=formset))
                            ligne_form.instance.delete() # Supprime l'objet LigneVente de la base de données
                    else:
                        # La ligne n'est pas marquée pour suppression (elle est nouvelle ou modifiée)
                        ligne_vente = ligne_form.save(commit=False)
                        ligne_vente.sale = self.object
                        ligne_vente.price_at_sale = ligne_vente.product.price # Assure que le prix est le prix actuel

                        product_instance = ligne_vente.product
                        sale_boutique = self.object.boutique

                        try:
                            stock_item = Stock.objects.get(product=product_instance, boutique=sale_boutique)
                            
                            if ligne_vente.id: # C'est une ligne existante qui a été modifiée
                                old_quantity = initial_quantities.get(ligne_vente.id, 0)
                                quantity_change = ligne_vente.quantity - old_quantity # Différence entre nouvelle et ancienne quantité

                                if stock_item.quantity < quantity_change: # Si on tente d'augmenter la quantité au-delà du stock disponible
                                    messages.error(self.request, f"Stock insuffisant pour le produit '{product_instance.name}' à la boutique '{sale_boutique.name}'. Stock disponible : {stock_item.quantity}, demandé en plus : {quantity_change}.")
                                    transaction.set_rollback(True)
                                    return self.render_to_response(self.get_context_data(form=form, formset=formset))

                                stock_item.quantity -= quantity_change # Ajuste le stock
                                stock_item.save()

                                if quantity_change > 0: # Si la quantité a augmenté (plus de produit vendu)
                                    MouvementStock.objects.create(
                                        product=product_instance,
                                        boutique=sale_boutique,
                                        quantity=quantity_change,
                                        movement_type='exit',
                                        user=self.request.user,
                                        notes=f"Modification vente (ID Vente: {self.object.id}) - Augmentation qté"
                                    )
                                elif quantity_change < 0: # Si la quantité a diminué (moins de produit vendu, ou retour partiel)
                                    MouvementStock.objects.create(
                                        product=product_instance,
                                        boutique=sale_boutique,
                                        quantity=abs(quantity_change), # Utilise la valeur absolue pour la quantité du mouvement
                                        movement_type='entry',
                                        user=self.request.user,
                                        notes=f"Modification vente (ID Vente: {self.object.id}) - Diminution qté / Retour"
                                    )
                            else: # C'est une nouvelle ligne ajoutée à une vente existante
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
                        
                        ligne_vente.save() # Sauvegarde la LigneVente après les ajustements de stock
                        
            messages.success(self.request, "La vente a été mise à jour avec succès!")
            return HttpResponseRedirect(self.get_success_url())
        else:
            messages.error(self.request, "Veuillez corriger les erreurs dans les articles de la vente.")
            return self.render_to_response(self.get_context_data(form=form, formset=formset))
        
class VenteDeleteView(LoginRequiredMixin, DeleteView):
    model = Vente
    template_name = 'sales/vente_confirm_delete.html'
    success_url = reverse_lazy('sales:vente_list')
    context_object_name = 'vente'

    def form_valid(self, form):
        with transaction.atomic():
            sale_boutique = self.object.boutique # La boutique de la vente à supprimer
            for ligne_vente in self.object.lignes_vente.all():
                try:
                    stock_item = Stock.objects.get(product=ligne_vente.product, boutique=sale_boutique)
                    stock_item.quantity += ligne_vente.quantity # Rajoute la quantité au stock lors de la suppression
                    stock_item.save()
                    
                    # Enregistrer un mouvement de stock de type 'Entrée' pour l'annulation
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
                    transaction.set_rollback(True) # Force le rollback pour éviter une suppression partielle
                    # Renvoyer le formulaire avec l'erreur. Note: Pour une DeleteView, ce cas est rare car il n'y a pas de formulaire à remplir.
                    # Il est plus courant de rediriger avec un message flash.
                    return self.render_to_response(self.get_context_data()) # On ne passe pas de "form" ici
            messages.success(self.request, "La vente a été supprimée et les stocks mis à jour.")
            return super().form_valid(form)