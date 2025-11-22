from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from Requisition.models import Requisition, RequisitionStatusTimeline
from ERP.models import User


def requisition_detail(request, req_id):
    user_id = request.session.get('user_id')
    
    user = User.objects.get(pk=user_id)
    if not user_id:
        return redirect('login')
    print(user_id)
    
    # Get the specific requisition with related data
    requisition = get_object_or_404(
        Requisition.objects.select_related('requested_by', 'branch', 'approved_by')
                          .prefetch_related('items__product__product_specification_set'),
        req_id=req_id
    )
    
    # Get requisition items with product specifications
    requisition_items = requisition.items.select_related('product').all()
    
    # Define progress steps based on your status choices
    progress_steps = [
        {'status': 'PENDING_CUSTODIAN', 'label': 'Property Custodian Review', 'active': False},
        {'status': 'PENDING_TOP_MGMT', 'label': 'Pending Top Management Approval', 'active': False},
        {'status': 'APPROVED_REQUISITION', 'label': 'Approved Requisition', 'active': False},
        {'status': 'PO_APPROVAL', 'label': 'PO Approval', 'active': False},
        {'status': 'TO_BE_DELIVERED', 'label': 'To be Delivered', 'active': False},
        {'status': 'INSPECTION', 'label': 'Inspection', 'active': False},
        {'status': 'FULFILLED', 'label': 'Request Fulfilled', 'active': False},
    ]
    
    # Activate steps up to current status
    current_status_index = None
    for i, step in enumerate(progress_steps):
        if step['status'] == requisition.req_main_status:
            step['active'] = True
            current_status_index = i
            break
    
    # Mark all previous steps as completed
    if current_status_index is not None:
        for i in range(current_status_index):
            progress_steps[i]['completed'] = True

    # Determine which buttons to show based on user role and requisition status
    show_buttons = False
    show_property_custodian_buttons = False
    show_top_management_buttons = False
    show_purchase_management_buttons = False

    #Property Custodian (role_id == 4) can only see buttons when status is PENDING_CUSTODIAN
    if user.role_id == 4 and requisition.req_main_status == 'PENDING_CUSTODIAN':
        show_buttons = True
        show_property_custodian_buttons = True
    
    # Top Management can only see buttons when status is PENDING_TOP_MGMT
    # Assuming top management has role_id == 2 (adjust according to your role IDs)
    elif user.role_id == 1 and requisition.req_main_status == 'PENDING_TOP_MGMT':
        show_buttons = True
        show_top_management_buttons = True

    # Purchase Management can only see Create RFQ button when status is APPROVED_REQUISITION
    # Assuming purchase management has role_id == 3 (adjust according to your role IDs)
    elif user.role_id == 3 and requisition.req_main_status == 'APPROVED_REQUISITION':
        show_buttons = True
        show_purchase_management_buttons = True
    
    return render(request, "main/requisition_detail.html", {
        "requisition": requisition,
        "requisition_items": requisition_items,
        "progress_steps": progress_steps,
        "current_status_index": current_status_index if current_status_index is not None else 0,
        "user": user,
        "active_page": "requisition",
        "show_buttons": show_buttons,
        "show_property_custodian_buttons": show_property_custodian_buttons,
        "show_top_management_buttons": show_top_management_buttons,
        "show_purchase_management_buttons": show_purchase_management_buttons,
    })