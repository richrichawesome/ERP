# # Purchasing/urls.py

# from django.urls import path
# from . import views

# urlpatterns = [
#     path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
#     path("purchasing_staff_approved_req/", views.purchasing_staff_approved_req, name="purchasing_staff_approved_req"),
#     path("purchasing_staff_sup_manage/", views.purchasing_staff_sup_manage, name="purchasing_staff_sup_manage"),
#     path("purchasing_staff_inventory/", views.purchasing_staff_inventory, name="purchasing_staff_inventory"),
#     path("purchasing_staff_reports/", views.purchasing_staff_reports, name="purchasing_staff_reports"),
# ]  

# Purchasing/urls.py

from django.urls import path # type: ignore
from . import views
from .views import supplier_management_views

urlpatterns = [
    # Dashboard and existing pages
    path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
    path("purchasing_staff_approved_req/", views.purchasing_staff_approved_req, name="purchasing_staff_approved_req"),
    path("purchasing_staff_inventory/", views.purchasing_staff_inventory, name="purchasing_staff_inventory"),
    path("purchasing_staff_reports/", views.purchasing_staff_reports, name="purchasing_staff_reports"),
    
    # Supplier Management
    path("purchasing_staff_sup_manage/", 
         supplier_management_views.purchasing_staff_sup_manage, 
         name="purchasing_staff_sup_manage"),
    
    path("create-supplier/", 
         supplier_management_views.create_supplier, 
         name="create_supplier"),
    
    path("supplier-catalog/<int:supplier_id>/", 
         supplier_management_views.supplier_catalog, 
         name="supplier_catalog"),
    
    path("update-supplier/<int:supplier_id>/", 
         supplier_management_views.update_supplier, 
         name="update_supplier"),
    
    path("add-product-to-supplier/<int:supplier_id>/", 
         supplier_management_views.add_product_to_supplier, 
         name="add_product_to_supplier"),
    
    path("save-supplier-products/<int:supplier_id>/", 
         supplier_management_views.save_supplier_products, 
         name="save_supplier_products"),
    
    path("update-product-price/<int:supplier_product_id>/", 
         supplier_management_views.update_product_price, 
         name="update_product_price"),

    path("get-price-history/<int:supplier_product_id>/", 
         supplier_management_views.get_price_history, 
         name="get_price_history"),
     
]