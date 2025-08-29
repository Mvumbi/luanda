# products/urls.py

from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # URLs for Product management (using function-based views)
    path('list/', views.product_list, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/update/', views.product_update, name='product_update'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'), 
    
    # URLs for Stock management (using class-based views)
    # This line was incorrect: path('stock/list/', views.stock_list, name='stock_list'),
    # It should use the class-based view:
    path('stocks/', views.StockListView.as_view(), name='stock_list'), # Corrected: uses StockListView.as_view()
    path('stocks/add/', views.StockCreateView.as_view(), name='stock_add'), # Renamed 'stock_create' to 'stock_add' for clarity
    path('stocks/<int:pk>/edit/', views.StockUpdateView.as_view(), name='stock_update'),
 
    # URLs for Stock Movements (using class-based views)
    path('stock-movements/', views.MouvementStockListView.as_view(), name='mouvement_stock_list'),
]