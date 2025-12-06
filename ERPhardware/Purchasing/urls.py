


# Purchasing/urls.py
from django.urls import path
from . import views
from .views import supplier_management_views

urlpatterns = [
    # Dashboard and existing pages
    path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
    path("purchasing_staff_approved_req/", views.purchasing_staff_approved_req, name="purchasing_staff_approved_req"),


    path("purchasing_staff_inventory/", views.purchasing_staff_inventory, name="purchasing_staff_inventory"),
    path("purchasing_staff_reports/", views.purchasing_staff_reports, name="purchasing_staff_reports"),
    


     # RFQ Quotation URLs
    path('rfq/<int:rfq_id>/input-quotation/', views.input_quotation, name='input_quotation'),
    path('purchasing/get-rfq-items/<int:rfq_id>/', views.get_rfq_items, name='get_rfq_items'),




    path('rfq_creation/', views.rfq_creation, name='rfq_creation'),
    path('requisition/create-rfq-multiple/', views.create_rfq_multiple, name='create_rfq_multiple'),


    path('purchasing/preview-rfq/', views.preview_rfq_data, name='preview_rfq_data'),  
    path('purchasing/quote_creation.html', views.quote_creation, name='quote_creation'),


    path('purchasing/add-supplier/', views.add_supplier, name='add_supplier'),
    path('purchasing/save-supplier-quotation/', views.save_supplier_quotation, name='save_supplier_quotation'),
    path('purchasing/complete-quotation-input/', views.complete_quotation_input, name='complete_quotation_input'),
    
    
    
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
     



     path("po_creation/", views.po_creation, name="po_creation"),
     path('purchasing/preview-po/', views.preview_po_data, name='preview_po_data'),
     path('purchasing/generate-po-preview/', views.generate_po_preview_data, name='generate_po_preview_data'),
     path('purchasing/create-po-multiple/', views.create_po_multiple, name='create_po_multiple'),



]