from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from Requisition.models import Requisition, RequisitionStatusTimeline
from Purchasing.models import RFQ, RFQ_Item, Supplier  # Add this import
from ERP.models import User


# # def requisition_detail(request, req_id):
# #     user_id = request.session.get('user_id')
    
# #     if not user_id:
# #         return redirect('login')
    
# #     try:
# #         user = User.objects.get(pk=user_id)
# #     except User.DoesNotExist:
# #         return redirect('login')
    
# #     requisition = get_object_or_404(
# #         Requisition.objects.select_related('requested_by', 'branch', 'approved_by')
# #                           .prefetch_related('items__product__product_specification_set'),
# #         req_id=req_id
# #     )
    
# #     requisition_items = requisition.items.select_related('product').all()
    
# #     # Check if RFQ already exists for this requisition
# #     rfq_exists = RFQ.objects.filter(rfq_created_by=requisition).exists()

# #     # get all active suppliers for quotaion form
# #     suppliers = Supplier.objects.filter(sup_is_active=True)
    
# #     progress_steps = [
# #         {'status': 'PENDING_CUSTODIAN', 'label': 'Property Custodian Review', 'active': False},
# #         {'status': 'PENDING_TOP_MGMT', 'label': 'Pending Top Management Approval', 'active': False},
# #         {'status': 'APPROVED_REQUISITION', 'label': 'Approved Requisition', 'active': False},
# #         {'status': 'PO_APPROVAL', 'label': 'PO Approval', 'active': False},
# #         {'status': 'TO_BE_DELIVERED', 'label': 'To be Delivered', 'active': False},
# #         {'status': 'INSPECTION', 'label': 'Inspection', 'active': False},
# #         {'status': 'FULFILLED', 'label': 'Request Fulfilled', 'active': False},
# #     ]
    
# #     current_status_index = None
# #     for i, step in enumerate(progress_steps):
# #         if step['status'] == requisition.req_main_status:
# #             step['active'] = True
# #             current_status_index = i
# #             break
    
# #     if current_status_index is not None:
# #         for i in range(current_status_index):
# #             progress_steps[i]['completed'] = True

# #     show_buttons = False
# #     show_property_custodian_buttons = False
# #     show_top_management_buttons = False
# #     show_purchase_management_buttons = False
# #     show_input_quotation_button = False

# #     if user.role_id == 4 and requisition.req_main_status == 'PENDING_CUSTODIAN':
# #         show_buttons = True
# #         show_property_custodian_buttons = True
    
# #     elif user.role_id == 1 and requisition.req_main_status == 'PENDING_TOP_MGMT':
# #         show_buttons = True
# #         show_top_management_buttons = True

# #     elif user.role_id == 3 and requisition.req_main_status == 'APPROVED_REQUISITION':
# #         show_buttons = True
# #         if rfq_exists or requisition.req_substatus == 'RFQ_CREATED':
# #             show_input_quotation_button = True
# #         else:
# #             show_purchase_management_buttons = True
    
# #     return render(request, "main/requisition_detail.html", {
# #         "requisition": requisition,
# #         "requisition_items": requisition_items,
# #         "progress_steps": progress_steps,
# #         "current_status_index": current_status_index if current_status_index is not None else 0,
# #         "user": user,
# #         "active_page": "requisition",
# #         "show_buttons": show_buttons,
# #         "show_property_custodian_buttons": show_property_custodian_buttons,
# #         "show_top_management_buttons": show_top_management_buttons,
# #         "show_purchase_management_buttons": show_purchase_management_buttons,
# #         "show_input_quotation_button": show_input_quotation_button,
# #         "rfq_exists": rfq_exists,  # Pass this to template if needed
# #         "suppliers": suppliers,
# #     })


# def requisition_detail(request, req_id):
#     user_id = request.session.get('user_id')
    
#     if not user_id:
#         return redirect('login')
    
#     try:
#         user = User.objects.get(pk=user_id)
#     except User.DoesNotExist:
#         return redirect('login')
    
#     requisition = get_object_or_404(
#         Requisition.objects.select_related('requested_by', 'branch', 'approved_by')
#                           .prefetch_related('items__product__product_specification_set'),
#         req_id=req_id
#     )
    
#     requisition_items = requisition.items.select_related('product').all()
    
#     # Check if RFQ already exists for this requisition
#     rfq_exists = RFQ.objects.filter(rfq_created_by=requisition).exists()
    
#     # Get RFQ items if RFQ exists
#     rfq_items = None
#     if rfq_exists:
#         rfq_items = RFQ_Item.objects.filter(requisition=requisition).select_related('product')
    
#     # get all active suppliers for quotation form
#     suppliers = Supplier.objects.filter(sup_is_active=True)
    
#     progress_steps = [
#         {'status': 'PENDING_CUSTODIAN', 'label': 'Property Custodian Review', 'active': False},
#         {'status': 'PENDING_TOP_MGMT', 'label': 'Pending Top Management Approval', 'active': False},
#         {'status': 'APPROVED_REQUISITION', 'label': 'Approved Requisition', 'active': False},
#         {'status': 'PO_APPROVAL', 'label': 'PO Approval', 'active': False},
#         {'status': 'TO_BE_DELIVERED', 'label': 'To be Delivered', 'active': False},
#         {'status': 'INSPECTION', 'label': 'Inspection', 'active': False},
#         {'status': 'FULFILLED', 'label': 'Request Fulfilled', 'active': False},
#     ]
    
#     current_status_index = None
#     for i, step in enumerate(progress_steps):
#         if step['status'] == requisition.req_main_status:
#             step['active'] = True
#             current_status_index = i
#             break
    
#     if current_status_index is not None:
#         for i in range(current_status_index):
#             progress_steps[i]['completed'] = True

#     show_buttons = False
#     show_property_custodian_buttons = False
#     show_top_management_buttons = False
#     show_purchase_management_buttons = False
#     show_input_quotation_button = False

#     if user.role_id == 4 and requisition.req_main_status == 'PENDING_CUSTODIAN':
#         show_buttons = True
#         show_property_custodian_buttons = True
    
#     elif user.role_id == 1 and requisition.req_main_status == 'PENDING_TOP_MGMT':
#         show_buttons = True
#         show_top_management_buttons = True

#     elif user.role_id == 3 and requisition.req_main_status == 'APPROVED_REQUISITION':
#         show_buttons = True
#         if rfq_exists or requisition.req_substatus == 'RFQ_CREATED':
#             show_input_quotation_button = True
#         else:
#             show_purchase_management_buttons = True
    
#     return render(request, "main/requisition_detail.html", {
#         "requisition": requisition,
#         "requisition_items": requisition_items,
#         "rfq_items": rfq_items,  # Add this line
#         "progress_steps": progress_steps,
#         "current_status_index": current_status_index if current_status_index is not None else 0,
#         "user": user,
#         "active_page": "requisition",
#         "show_buttons": show_buttons,
#         "show_property_custodian_buttons": show_property_custodian_buttons,
#         "show_top_management_buttons": show_top_management_buttons,
#         "show_purchase_management_buttons": show_purchase_management_buttons,
#         "show_input_quotation_button": show_input_quotation_button,
#         "rfq_exists": rfq_exists,
#         "suppliers": suppliers,
#     })


# kani ang current
# def requisition_detail(request, req_id):
#     user_id = request.session.get('user_id')
    
#     if not user_id:
#         return redirect('login')
    
#     try:
#         user = User.objects.get(pk=user_id)
#     except User.DoesNotExist:
#         return redirect('login')
    
#     requisition = get_object_or_404(
#         Requisition.objects.select_related('requested_by', 'branch', 'approved_by')
#                           .prefetch_related('items__product__product_specification_set'),
#         req_id=req_id
#     )
    
#     requisition_items = requisition.items.select_related('product').all()
    
#     # Check if RFQ already exists for this requisition
#     rfq_exists = RFQ.objects.filter(rfq_created_by=requisition).exists()
    
#     # Get RFQ items if RFQ exists
#     rfq_items = None
#     if rfq_exists:
#         rfq_items = RFQ_Item.objects.filter(requisition=requisition).select_related('product')
    
#     # Check if supplier quotations exist for this requisition
#     from Purchasing.models import Supplier_Quotation, RFQ_Supplier
#     quotations_exist = Supplier_Quotation.objects.filter(
#         rfq_supplier__rfq=requisition
#     ).exists()
    
#     # get all active suppliers for quotation form
#     suppliers = Supplier.objects.filter(sup_is_active=True)
    
#     progress_steps = [
#         {'status': 'PENDING_CUSTODIAN', 'label': 'Property Custodian Review', 'active': False},
#         {'status': 'PENDING_TOP_MGMT', 'label': 'Pending Top Management Approval', 'active': False},
#         {'status': 'APPROVED_REQUISITION', 'label': 'Approved Requisition', 'active': False},
#         {'status': 'PO_APPROVAL', 'label': 'PO Approval', 'active': False},
#         {'status': 'TO_BE_DELIVERED', 'label': 'To be Delivered', 'active': False},
#         {'status': 'INSPECTION', 'label': 'Inspection', 'active': False},
#         {'status': 'FULFILLED', 'label': 'Request Fulfilled', 'active': False},
#     ]
    
#     current_status_index = None
#     for i, step in enumerate(progress_steps):
#         if step['status'] == requisition.req_main_status:
#             step['active'] = True
#             current_status_index = i
#             break
    
#     if current_status_index is not None:
#         for i in range(current_status_index):
#             progress_steps[i]['completed'] = True

#     show_buttons = False
#     show_property_custodian_buttons = False
#     show_top_management_buttons = False
#     show_purchase_management_buttons = False
#     show_input_quotation_button = False
#     # show_create_po_button = False
#     show_quotation_complete_message = False

#     if user.role_id == 4 and requisition.req_main_status == 'PENDING_CUSTODIAN':
#         show_buttons = True
#         show_property_custodian_buttons = True
    
#     elif user.role_id == 1 and requisition.req_main_status == 'PENDING_TOP_MGMT':
#         show_buttons = True
#         show_top_management_buttons = True

#     elif user.role_id == 3 and requisition.req_main_status == 'APPROVED_REQUISITION':
#         show_buttons = True
#         if rfq_exists or requisition.req_substatus == 'RFQ_CREATED':
#             # Check if quotations exist OR if status is QUOTATIONS_COMPLETED
#             if quotations_exist or requisition.req_substatus == 'QUOTATIONS_COMPLETED':
#                 show_quotation_complete_message = True  # Show message instead of button
#             else:
#                 show_input_quotation_button = True
#         else:
#             show_purchase_management_buttons = True
    
#     return render(request, "main/requisition_detail.html", {
#         "requisition": requisition,
#         "requisition_items": requisition_items,
#         "rfq_items": rfq_items,
#         "progress_steps": progress_steps,
#         "current_status_index": current_status_index if current_status_index is not None else 0,
#         "user": user,
#         "active_page": "requisition",
#         "show_buttons": show_buttons,
#         "show_property_custodian_buttons": show_property_custodian_buttons,
#         "show_top_management_buttons": show_top_management_buttons,
#         "show_purchase_management_buttons": show_purchase_management_buttons,
#         "show_input_quotation_button": show_input_quotation_button,
#         # "show_create_po_button": show_create_po_button,
#         "show_quotation_complete_message": show_quotation_complete_message, 
#         "rfq_exists": rfq_exists,
#         "quotations_exist": quotations_exist,  # Optional: pass to template for debugging
#         "suppliers": suppliers,
#     })








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
    
    requisition = get_object_or_404(
        Requisition.objects.select_related('requested_by', 'branch', 'approved_by')
                          .prefetch_related('items__product__product_specification_set'),
        req_id=req_id
    )
    
    requisition_items = requisition.items.select_related('product').all()
    
    progress_steps = [
        {'status': 'PENDING_CUSTODIAN', 'label': 'Property Custodian Review', 'active': False},
        {'status': 'PENDING_TOP_MGMT', 'label': 'Pending Top Management Approval', 'active': False},
        {'status': 'APPROVED_REQUISITION', 'label': 'Approved Requisition', 'active': False},
        {'status': 'PO_APPROVAL', 'label': 'PO Approval', 'active': False},
        {'status': 'TO_BE_DELIVERED', 'label': 'To be Delivered', 'active': False},
        {'status': 'INSPECTION', 'label': 'Inspection', 'active': False},
        {'status': 'FULFILLED', 'label': 'Request Fulfilled', 'active': False},
    ]
    
    current_status_index = None
    for i, step in enumerate(progress_steps):
        if step['status'] == requisition.req_main_status:
            step['active'] = True
            current_status_index = i
            break
    
    if current_status_index is not None:
        for i in range(current_status_index):
            progress_steps[i]['completed'] = True

    show_buttons = False
    show_property_custodian_buttons = False
    show_top_management_buttons = False
    # show_purchase_management_mess = False
    # show_input_quotation_mess = False

    if user.role_id == 4 and requisition.req_main_status == 'PENDING_CUSTODIAN':
        show_buttons = True
        show_property_custodian_buttons = True
    
    elif user.role_id == 1 and requisition.req_main_status == 'PENDING_TOP_MGMT':
        show_buttons = True
        show_top_management_buttons = True



    status_message = None
    if requisition.req_main_status == 'APPROVED_REQUISITION':
        if requisition.req_substatus == 'NONE':
            status_message = 'Requisition Awaiting for RFQ Creation'
        elif requisition.req_substatus == 'RFQ_CREATED':
            status_message = 'Requisition Awaiting for Supplier Quotation Input'
        elif requisition.req_substatus == 'PENDING_PO':
            status_message = 'Requisition Awaiting for PO Creation'

    # elif user.role_id == 3 and requisition.req_main_status == 'APPROVED_REQUISITION':
    #     show_buttons = True
    #     if requisition.req_substatus == 'RFQ_CREATED':
    #         show_input_quotation_mess = True
    #     else:
    #         show_purchase_management_mess = True
    
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
        "status_message": status_message,
        # "show_purchase_management_mess": show_purchase_management_mess,
        # "show_input_quotation_mess": show_input_quotation_mess,
    })
