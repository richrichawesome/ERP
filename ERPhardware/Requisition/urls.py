# Requisition/urls.py
# from django.urls import path
# from .views import track_requisition_page
# from .views.inventory_replenishment import inventory_replenishment_form, create_inventory_replenishment
# from .views.internal_transfer import internal_transfer_form, create_internal_transfer
# from . import views

# urlpatterns = [
#     path("track_requisition/", track_requisition_page, name="track_requisition"),
    
#     # Inventory Replenishment
#     path('inventory-replenishment/', 
#          inventory_replenishment_form, 
#          name='inventory_replenishment_form'),
    
#     path('create-inventory-replenishment/', 
#          create_inventory_replenishment, 
#          name='create_inventory_replenishment'),
    
#     # Internal Transfer
#     path('internal-transfer/', 
#          internal_transfer_form, 
#          name='internal_transfer_form'),
    
#     path('create-internal-transfer/', 
#          create_internal_transfer, 
#          name='create_internal_transfer'),
    
#     # List and Detail
#     path('', views.requisition_list, name='list'),
#     path('<int:req_id>/', views.requisition_detail, name='detail'),
# ]

# Requisition/urls.py
from django.urls import path
from .views import track_requisition_page
from .views.inventory_replenishment import inventory_replenishment_form, create_inventory_replenishment
from .views.internal_transfer import internal_transfer_form, create_internal_transfer
from .views.requisition_management import serve_rf_file
from . import views

urlpatterns = [
    path("track_requisition/", track_requisition_page, name="track_requisition"),
    
    # Inventory Replenishment
    path('inventory-replenishment/', 
         inventory_replenishment_form, 
         name='inventory_replenishment_form'),
    
    path('create-inventory-replenishment/', 
         create_inventory_replenishment, 
         name='create_inventory_replenishment'),
    
    # Internal Transfer
    path('internal-transfer/', 
         internal_transfer_form, 
         name='internal_transfer_form'),
    
    path('create-internal-transfer/', 
         create_internal_transfer, 
         name='create_internal_transfer'),
    
    # Serve RF Files
    path('media/rfs/<str:filename>', 
         serve_rf_file, 
         name='serve_rf_file'),
    
    # List and Detail
    path('', views.requisition_list, name='list'),
    path('<int:req_id>/', views.requisition_detail, name='detail'),
]