from django.contrib import admin
from .models import RapportMensuel # Importez votre modèle

@admin.register(RapportMensuel)
class RapportMensuelAdmin(admin.ModelAdmin):
    list_display = (
        'boutique',
        'month',
        'year',
        'total_revenue',
        'num_sales',
        'generated_at',
        'report_file_link'
    )
    list_filter = ('boutique', 'year', 'month')
    search_fields = ('boutique__name', 'top_selling_products', 'low_stock_alerts') # La recherche sur JSONField peut être limitée
    date_hierarchy = 'generated_at'
    readonly_fields = ('generated_at', 'report_file_link', 'total_revenue', 'num_sales', 'top_selling_products', 'low_stock_alerts') # Ces champs sont générés, pas modifiés manuellement

    # Méthode pour afficher un lien vers le fichier du rapport dans la liste de l'admin
    def report_file_link(self, obj):
        if obj.report_file:
            # Vous devrez ajuster l'URL en fonction de votre configuration des médias
            return f'<a href="{obj.report_file.url}" target="_blank">Voir Rapport</a>'
        return "Pas de fichier"
    report_file_link.allow_tags = True
    report_file_link.short_description = "Fichier du Rapport"