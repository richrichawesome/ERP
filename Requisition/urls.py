# Requisition/urls.py
from django.urls import path
from .views import track_requisition_page
from .views.inventory_replenishment import inventory_replenishment_form, create_inventory_replenishment
from .views.internal_transfer import internal_transfer_form, create_internal_transfer
from .views.requisition_management import serve_rf_file
from .views.internal_transfer_request import (
    internal_transfer_request,
    internal_transfer_request_detail,
    custodian_approve_direct,
    custodian_send_to_management,
    custodian_reject,
    management_approve,
    management_reject,
    sender_accept,
    sender_reject,
    receive_items
)

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
         internal_transfer_request, 
         name='internal_transfer_request'),
    
    path('internal_transfer_request/<int:req_id>/', 
         internal_transfer_request_detail, 
         name='internal_transfer_request_detail'),
    
    # Property Custodian Actions
    path('internal_transfer_request/<int:req_id>/custodian-approve-direct/', 
         custodian_approve_direct, 
         name='custodian_approve_direct'),
    
    path('internal_transfer_request/<int:req_id>/custodian-send-to-management/', 
         custodian_send_to_management, 
         name='custodian_send_to_management'),
    
    path('internal_transfer_request/<int:req_id>/custodian-reject/', 
         custodian_reject, 
         name='custodian_reject'),
    
    # Top Management Actions
    path('internal_transfer_request/<int:req_id>/management-approve/', 
         management_approve, 
         name='management_approve'),
    
    path('internal_transfer_request/<int:req_id>/management-reject/', 
         management_reject, 
         name='management_reject'),
    
    # Sender Actions
    path('internal_transfer_request/<int:req_id>/sender-accept/', 
         sender_accept, 
         name='sender_accept'),
    
    path('internal_transfer_request/<int:req_id>/sender-reject/', 
         sender_reject, 
         name='sender_reject'),
    
    # Receive Items
    path('internal_transfer_request/<int:req_id>/receive-items/', 
         receive_items, 
         name='receive_items'),
]