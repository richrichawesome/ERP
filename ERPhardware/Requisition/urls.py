# from django.urls import path
# from .views import track_requisition_page, redirect_inventory_replenishment_form, redirect_internal_transfer_form
# from . import views
from django.urls import path
from .views import track_requisition_page, redirect_internal_transfer_form
from .views.inventory_replenishment import inventory_replenishment_form, create_inventory_replenishment, test_pdf_generation
from . import views

urlpatterns = [
    path("track_requisition/", track_requisition_page, name="track_requisition"),
    # path("inventory-replenishment/", redirect_inventory_replenishment_form, name="redirect_inventory_replenishment_form"),
    path("internal-transfer/", redirect_internal_transfer_form, name="redirect_internal_transfer_form"),

    # Inventory Replenishment
    path('inventory-replenishment/', 
         views.inventory_replenishment_form, 
         name='inventory_replenishment_form'),
    
    path('create-inventory-replenishment/', 
         views.create_inventory_replenishment, 
         name='create_inventory_replenishment'),

#     path("test-inventory/", test_inventory_view, name="test_inventory"),
#     path('test-pdf/<int:req_id>/', test_pdf_generation, name='test_pdf_generation'),
    
    # List and Detail
    path('', views.requisition_list, name='list'),
    path('<int:req_id>/', views.requisition_detail, name='detail'),

]
