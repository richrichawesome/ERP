# Requisition/urls.py
from django.urls import path
from .views import track_requisition_page
from .views.inventory_replenishment import inventory_replenishment_form, create_inventory_replenishment
from .views.internal_transfer import internal_transfer_form, create_internal_transfer
from .views.requisition_management import serve_rf_file
from .views.internal_transfer_request import (
    internal_transfer_request_detail,
    custodian_approve_direct,
    custodian_send_to_management,
    custodian_reject,
    management_approve,
    management_reject,
#     sender_accept_transfer,
#     sender_reject_transfer,
#     receiver_confirm_receipt,
#     get_timeline_details
)
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
    
    # Internal Transfer Request Page
    path('internal_transfer_request/', 
         views.internal_transfer_request, 
         name='internal_transfer_request'),
    
    path('internal_transfer_request/<int:req_id>/', 
         internal_transfer_request_detail, 
         name='internal_transfer_request_detail'),
    
    # Property Custodian Actions
    path('internal_transfer_request/<int:req_id>/custodian/approve-direct/', 
         custodian_approve_direct, 
         name='custodian_approve_direct'),
    
    path('internal_transfer_request/<int:req_id>/custodian/send-management/', 
         custodian_send_to_management, 
         name='custodian_send_to_management'),
    
    path('internal_transfer_request/<int:req_id>/custodian/reject/', 
         custodian_reject, 
         name='custodian_reject'),
    
    # Top Management Actions
    path('internal_transfer_request/<int:req_id>/management/approve/', 
         management_approve, 
         name='management_approve'),
    
    path('internal_transfer_request/<int:req_id>/management/reject/', 
         management_reject, 
         name='management_reject'),
    
    # Sender Branch Manager Actions
#     path('internal_transfer_request/<int:req_id>/sender/accept/', 
#          sender_accept_transfer, 
#          name='sender_accept_transfer'),
    
#     path('internal_transfer_request/<int:req_id>/sender/reject/', 
#          sender_reject_transfer, 
#          name='sender_reject_transfer'),
    
    # Receiver Branch Manager Actions
#     path('internal_transfer_request/<int:req_id>/receiver/confirm/', 
#          receiver_confirm_receipt, 
#          name='receiver_confirm_receipt'),
    
    # Timeline Details
#     path('internal_transfer_request/<int:req_id>/timeline/', 
#          get_timeline_details, 
#          name='get_timeline_details'),
]