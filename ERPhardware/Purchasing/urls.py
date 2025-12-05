# from django.urls import path
# from . import views

# urlpatterns = [
#     path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
#     path("purchasing_staff_approved_req/", views.purchasing_staff_approved_req, name="purchasing_staff_approved_req"),

#     # path("create_po_selection/", views.create_po_selection, name="create_po_selection"),
#     path('create-po/selection/', views.create_po_selection, name='create_po_selection'),
#     path('create-po/supplier-selection/', views.create_po_supplier_selection, name='create_po_supplier_selection'),
#     path('create-po/summary/', views.create_po_summary, name='create_po_summary'),

#     path("purchasing_staff_sup_manage/", views.purchasing_staff_sup_manage, name="purchasing_staff_sup_manage"),
#     path("purchasing_staff_inventory/", views.purchasing_staff_inventory, name="purchasing_staff_inventory"),
#     path("purchasing_staff_reports/", views.purchasing_staff_reports, name="purchasing_staff_reports"),
#     path('requisition/<int:req_id>/create-rfq/', views.create_rfq, name='create_rfq'),
#     path('requisition/<int:req_id>/input-quotation/', views.input_quotation, name='input_quotation'),

#     # NEW URLS - Add these:
#     path('add-supplier/', views.input_quotation_views.add_supplier, name='add_supplier'),
#     path('requisition/<int:req_id>/save-quotation/', views.input_quotation_views.save_quotation, name='save_quotation'),

# ]   




# Purchasing/urls.py
# from django.urls import path
# from . import views

# urlpatterns = [
#     path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
#     path("purchasing_staff_approved_req/", views.purchasing_staff_approved_req, name="purchasing_staff_approved_req"),

#     # PO Creation URLs
#     path('create-po/selection/', views.create_po_selection, name='create_po_selection'),
#     path('create-po/supplier-selection/', views.create_po_supplier_selection, name='create_po_supplier_selection'),
#     path('create-po/summary/', views.create_po_summary, name='create_po_summary'),
    
#     # ADD THIS URL for the AJAX call
#     path('api/consolidated-items/', views.get_consolidated_items, name='get_consolidated_items'),

#     path("purchasing_staff_sup_manage/", views.purchasing_staff_sup_manage, name="purchasing_staff_sup_manage"),
#     path("purchasing_staff_inventory/", views.purchasing_staff_inventory, name="purchasing_staff_inventory"),
#     path("purchasing_staff_reports/", views.purchasing_staff_reports, name="purchasing_staff_reports"),
#     path('requisition/<int:req_id>/create-rfq/', views.create_rfq, name='create_rfq'),
#     path('requisition/<int:req_id>/input-quotation/', views.input_quotation, name='input_quotation'),

#     # Quotation URLs
#     path('add-supplier/', views.add_supplier, name='add_supplier'),
#     path('requisition/<int:req_id>/save-quotation/', views.save_quotation, name='save_quotation'),
# ]



# Purchasing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
    path("purchasing_staff_approved_req/", views.purchasing_staff_approved_req, name="purchasing_staff_approved_req"),


    path("purchasing_staff_sup_manage/", views.purchasing_staff_sup_manage, name="purchasing_staff_sup_manage"),
    path("purchasing_staff_inventory/", views.purchasing_staff_inventory, name="purchasing_staff_inventory"),
    path("purchasing_staff_reports/", views.purchasing_staff_reports, name="purchasing_staff_reports"),
    # path('requisition/<int:req_id>/create-rfq/', views.create_rfq, name='create_rfq'),
    # path('requisition/<int:req_id>/input-quotation/', views.input_quotation, name='input_quotation'),


     # RFQ Quotation URLs
    path('rfq/<int:rfq_id>/input-quotation/', views.input_quotation, name='input_quotation'),
    # path('purchasing/save-quotation/', views.save_rfq_quotation, name='save_rfq_quotation'),
    path('purchasing/get-rfq-items/<int:rfq_id>/', views.get_rfq_items, name='get_rfq_items'),



    # Quotation URLs
    # path('add-supplier/', views.add_supplier, name='add_supplier'),
    # path('requisition/<int:req_id>/save-quotation/', views.save_quotation, name='save_quotation'),


    # path('rf_selection/', views.rf_selection, name="rf_selection"),
    # path('create_po/', views.create_po, name="create_po"),

    # path('rf_selection/', views.rf_selection, name='rf_selection'),
    # path('create-po-from-requisitions/', views.create_po_from_requisitions, name='create_po_from_requisitions'),




    path('rfq_creation/', views.rfq_creation, name='rfq_creation'),
    path('requisition/create-rfq-multiple/', views.create_rfq_multiple, name='create_rfq_multiple'),


    path('purchasing/preview-rfq/', views.preview_rfq_data, name='preview_rfq_data'),  
    path('purchasing/quote_creation.html', views.quote_creation, name='quote_creation'),


    path('purchasing/add-supplier/', views.add_supplier, name='add_supplier'),
    path('purchasing/save-supplier-quotation/', views.save_supplier_quotation, name='save_supplier_quotation'),
    path('purchasing/complete-quotation-input/', views.complete_quotation_input, name='complete_quotation_input'),
    # path('input-quotation/save/', views.save_supplier_quotation, name='save_quote_action'),
    # path('input-quotation/confirm/', views.confirm_quotation_status, name='confirm_quote_action'),
]