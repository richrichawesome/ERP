from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from Requisition.models import Requisition, RequisitionStatusTimeline
from Property_Custodian.models import Purchase_Order, Purchase_Order_Item
from ERP.models import User
from Property_Custodian.models import *


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
    
    # Initialize PO info variables
    po_info = None
    inspection_message = None
    has_existing_discrepancies = False  # NEW: Flag to track if PO already has discrepancies

        
    # If status is INSPECTION, try to find the associated PO
    if requisition.req_main_status == 'INSPECTION':
        # Check if requisition has a PO
        if requisition.po:
            purchase_order = requisition.po
            po_info = {
                'po_id': purchase_order.po_id,
                'supplier': purchase_order.supplier.sup_name if purchase_order.supplier else 'Unknown'
            }
            
            # This means inspection has already been completed
            has_existing_discrepancies = Discrepancy.objects.filter(
                purchase_order=purchase_order
            ).exists()
            
            # Create inspection message based on sub-status
            if requisition.req_substatus == 'INSPECTING' and requisition.req_main_status == "INSPECTION":
                inspection_message = f"Currently inspecting PO-{po_info['po_id'] if po_info else 'Unknown'}. Products are being checked for quality and quantity."
            elif requisition.req_substatus == 'INSPECTION':
                inspection_message = f"Items from PO-{po_info['po_id'] if po_info else 'Unknown'} are in transit for delivery."
    
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
    show_purchase_management_buttons = False
    show_to_be_delivered_buttons = False
    show_inspection_buttons = False
    show_delivery_received_buttons = False
    show_complete_buttons = False

    # Property Custodian (role_id == 4) can only see buttons when status is PENDING_CUSTODIAN
    if user.role_id == 4 and requisition.req_main_status == 'PENDING_CUSTODIAN':
        show_buttons = True
        show_property_custodian_buttons = True
    
    # Top Management can only see buttons when status is PENDING_TOP_MGMT
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
    # Purchase Management can only see Create RFQ button when status is APPROVED_REQUISITION
    elif user.role_id == 3 and requisition.req_main_status == 'APPROVED_REQUISITION':
        show_buttons = True
        show_purchase_management_buttons = True
    
    # Property Custodian (role_id == 4) can see approve button when status is TO_BE_DELIVERED
    elif user.role_id == 4 and requisition.req_main_status == 'TO_BE_DELIVERED':
        show_buttons = True
        show_to_be_delivered_buttons = True
        
    # Property Custodian (role_id == 4) can see inspect button when status is INSPECTION
    elif user.role_id == 4 and requisition.req_main_status == 'INSPECTION' and requisition.req_substatus == "PRODUCTS_RECEIVED":
        show_buttons = True
        show_inspection_buttons = True
        
    # Property Custodian (role_id == 4) can see inspect button when status is INSPECTION
    elif user.role_id == 4 and requisition.req_main_status == 'INSPECTION' and requisition.req_substatus == "INSPECTING":
        if not has_existing_discrepancies:
            show_buttons = True
            show_inspection_buttons = True
        else:
            # PO already has discrepancies, inspection already done
            show_buttons = False
        
    elif user.role_id == 2 and requisition.req_main_status == 'INSPECTION' and requisition.req_substatus == "IN_TRANSIT":
        show_buttons = True
        show_complete_buttons = True
    
    # elif user.role_id == 2 and requisition.req_main_status == 'INSPECTION' and requisition.req_substatus == "RECEIVED":
    #     show_buttons = True
    #     show_complete_buttons = True
    #     # if delivery_generated:  # Only show if delivery has been generated
    #     #     show_buttons = True
    #     #     show_delivery_received_buttons = True
    #     # else:
    #     #     show_buttons = False  # Hide button if no delivery generated

    
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
        "show_purchase_management_buttons": show_purchase_management_buttons,
        "show_to_be_delivered_buttons": show_to_be_delivered_buttons,
        "show_inspection_buttons": show_inspection_buttons,
        "show_delivery_received_buttons": show_delivery_received_buttons,
        "show_complete_buttons": show_complete_buttons,
        "po_info": po_info,  
        "inspection_message": inspection_message,  
        "has_existing_discrepancies": has_existing_discrepancies,
    })
    
@csrf_exempt
def approve_to_be_delivered(request, req_id):
    """View to handle TO_BE_DELIVERED approval by property custodian - updates ALL requisitions in the same PO"""
    if request.method == 'POST':
        try:
            # Get the clicked requisition
            requisition = get_object_or_404(Requisition, req_id=req_id)
            user_id = request.session.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'User not authenticated'
                })
            
            user = User.objects.get(pk=user_id)
            
            # Check if this requisition has a purchase order
            if not requisition.po:
                return JsonResponse({
                    'success': False,
                    'error': 'This requisition has no associated purchase order.'
                })
            
            # Get the purchase order associated with this requisition
            purchase_order = requisition.po
            po_id = purchase_order.po_id
            print(f"DEBUG: Found PO-{po_id} associated with REQ-{req_id}")
            
            # Now find ALL requisitions linked to this PO (through the reverse relation)
            # Using the related_name 'requisitions' from Purchase_Order model
            all_linked_requisitions = purchase_order.requisitions.all()
            print(f"DEBUG: Found {all_linked_requisitions.count()} requisitions linked to PO-{po_id}")
            
            # Update ALL linked requisitions
            updated_count = 0
            for req in all_linked_requisitions:
                old_status = req.req_main_status
                req.req_main_status = 'INSPECTION'
                req.req_substatus = 'PRODUCTS_RECEIVED'
                req.save()
                updated_count += 1
                
                # Create status timeline entry for each requisition
                RequisitionStatusTimeline.objects.create(
                    requisition=req,
                    main_status='INSPECTION',
                    sub_status='PRODUCTS_RECEIVED',
                    user=user,
                    comment=f'Products from PO-{po_id} received by {user.user_fname} {user.user_lname}'
                )
                
                print(f"DEBUG: Updated REQ-{req.req_id} from {old_status} to INSPECTION")
            
            # Also update the purchase order status
            purchase_order.po_main_status = 'INSPECTION'
            purchase_order.po_substatus = 'PRODUCTS_RECEIVED'
            purchase_order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Products received! {updated_count} requisition(s) updated to Inspection status.',
                'new_status': 'INSPECTION',
                'requisitions_updated': updated_count,
                'po_id': po_id
            })
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def approve_requisition(request, req_id):
    """Approve requisition - changes status to APPROVED_REQUISITION"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'APPROVED_REQUISITION'
        requisition.req_substatus = 'NONE'
        requisition.approved_by = user
        requisition.req_approval_date = timezone.now()
        requisition.save()
        
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='APPROVED_REQUISITION',
            sub_status='NONE',
            user=user,
            comment=f'Approved by {user.user_fname} {user.user_lname}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Requisition approved successfully!',
            'new_status': 'APPROVED_REQUISITION',
            'old_status': old_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def approve_to_management(request, req_id):
    """Approve and send to management - changes status to PENDING_TOP_MGMT"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'PENDING_TOP_MGMT'
        requisition.req_substatus = 'NONE'
        requisition.save()
        
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='PENDING_TOP_MGMT',
            sub_status='NONE',
            user=user,
            comment=f'Forwarded to Top Management by {user.user_fname} {user.user_lname}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Requisition approved and sent to management successfully!',
            'new_status': 'PENDING_TOP_MGMT',
            'old_status': old_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
def start_inspection(request, req_id):
    """View to handle starting inspection by property custodian - updates ALL requisitions in the same PO"""
    if request.method == 'POST':
        try:
            requisition = get_object_or_404(Requisition, req_id=req_id)
            user_id = request.session.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'User not authenticated'
                })
            
            user = User.objects.get(pk=user_id)
            
            # Check if requisition has a PO
            if not requisition.po:
                return JsonResponse({
                    'success': False,
                    'error': 'This requisition has no associated purchase order.'
                })
            
            # Get the purchase order
            purchase_order = requisition.po
            po_id = purchase_order.po_id
            
            # Get ALL requisitions linked to this PO
            all_linked_requisitions = purchase_order.requisitions.all()
            
            # Update ALL linked requisitions to INSPECTING sub-status
            for req in all_linked_requisitions:
                # Update only sub-status to INSPECTING (main status remains INSPECTION)
                req.req_substatus = 'INSPECTING'
                req.save()
                
                # Create status timeline entry for each requisition
                RequisitionStatusTimeline.objects.create(
                    requisition=req,
                    main_status='INSPECTION',
                    sub_status='INSPECTING',
                    user=user,
                    comment=f'Inspection started for PO-{po_id} by {user.user_fname} {user.user_lname}'
                )
            
            # Update purchase order status as well
            purchase_order.po_substatus = 'INSPECTING'
            purchase_order.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Inspection started for all requisitions in PO!',
                'new_substatus': 'INSPECTING',
                'po_id': po_id
            })
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


#rework dapat
@csrf_exempt
def confirm_delivery_received(request, req_id):
    """View to handle delivery received confirmation when items are IN_TRANSIT"""
    if request.method == 'POST':
        try:
            # Get the clicked requisition
            requisition = get_object_or_404(Requisition, req_id=req_id)
            user_id = request.session.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'User not authenticated'
                })
            
            user = User.objects.get(pk=user_id)
            
            # Check if this requisition has a purchase order
            if not requisition.po:
                return JsonResponse({
                    'success': False,
                    'error': 'This requisition has no associated purchase order.'
                })
            
            # Get the purchase order associated with this requisition
            purchase_order = requisition.po
            po_id = purchase_order.po_id
            
            # Get ALL requisitions linked to this PO
            all_linked_requisitions = purchase_order.requisitions.all()
            
            # Update ALL linked requisitions to FULFILLED status
            updated_count = 0
            for req in all_linked_requisitions:
                old_status = req.req_main_status
                old_substatus = req.req_substatus
                req.req_main_status = 'INSPECTION'
                req.req_substatus = 'RECEIVED'
                req.save()
                updated_count += 1
                
                # Create status timeline entry for each requisition
                RequisitionStatusTimeline.objects.create(
                    requisition=req,
                    main_status='INSPECTION',
                    sub_status='RECEIVED',
                    user=user,
                    comment=f'Delivery from PO-{po_id} received and confirmed by {user.user_fname} {user.user_lname}. Requisition fulfilled.'
                )
                
                print(f"DEBUG: Updated REQ-{req.req_id} from {old_status}/{old_substatus} to FULFILLED")
            
            # Update purchase order status
            purchase_order.po_main_status = 'INSPECTION'
            purchase_order.po_substatus = 'RECEIVED'
            purchase_order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Delivery confirmed! {updated_count} requisition(s) marked as fulfilled.',
                'new_status': 'FULFILLED',
                'requisitions_updated': updated_count,
                'po_id': po_id
            })
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
def complete_requisition(request, req_id):
    """View for Purchase Management to mark requisition as FULFILLED and add to inventory"""
    if request.method == 'POST':
        try:
            # Get the clicked requisition
            requisition = get_object_or_404(Requisition, req_id=req_id)
            user_id = request.session.get('user_id')
            
            if not user_id:
                return JsonResponse({
                    'success': False,
                    'error': 'User not authenticated'
                })
            
            user = User.objects.get(pk=user_id)
            
            # Only Purchase Management (role_id == 2) can do this
            if user.role_id != 2:
                return JsonResponse({
                    'success': False,
                    'error': 'Only Purchase Management can mark requisition as fulfilled'
                })
            
            # Check if this requisition has a purchase order
            if not requisition.po:
                return JsonResponse({
                    'success': False,
                    'error': 'This requisition has no associated purchase order.'
                })
            
            # Get the purchase order
            purchase_order = requisition.po
            po_id = purchase_order.po_id
            
            # Check if delivery has been generated for this PO
            delivery_exists = Delivery.objects.filter(purchase_order=purchase_order).exists()
            if not delivery_exists:
                return JsonResponse({
                    'success': False,
                    'error': f'No delivery has been generated for PO-{po_id}.'
                })
            
            # Get the delivery
            delivery = Delivery.objects.filter(purchase_order=purchase_order).first()
            
            # Check if delivery is in IN_TRANSIT status
            if delivery.delivery_status != 'IN_TRANSIT':
                return JsonResponse({
                    'success': False,
                    'error': f'Delivery #{delivery.delivery_id} is not in transit. Current status: {delivery.delivery_status}'
                })
            
            # Get ALL requisitions linked to this PO
            all_linked_requisitions = purchase_order.requisitions.all()
            
            # Update ALL linked requisitions to FULFILLED status
            updated_count = 0
            for req in all_linked_requisitions:
                old_status = req.req_main_status
                old_substatus = req.req_substatus
                req.req_main_status = 'FULFILLED'
                req.req_substatus = 'NONE'
                req.save()
                updated_count += 1
                
                # Create status timeline entry for each requisition
                RequisitionStatusTimeline.objects.create(
                    requisition=req,
                    main_status='FULFILLED',
                    sub_status='NONE',
                    user=user,
                    comment=f'Requisition fulfilled by Purchase Management {user.user_fname} {user.user_lname} after delivery confirmation.'
                )
                
                print(f"DEBUG: Updated REQ-{req.req_id} from {old_status}/{old_substatus} to FULFILLED")
            
            # Update purchase order status
            purchase_order.po_main_status = 'FULFILLED'
            purchase_order.po_substatus = 'NONE'
            purchase_order.save()
            
            # Update delivery status to DELIVERED
            delivery.delivery_status = 'DELIVERED'
            delivery.delivery_completed_date = timezone.now()
            delivery.completed_by = user
            delivery.save()
            
            # Add delivery items to inventory
            delivery_items = DeliveryItem.objects.filter(delivery=delivery).select_related('product', 'branch')
            
            # Check if delivery has items
            if not delivery_items.exists():
                return JsonResponse({
                    'success': False,
                    'error': f'Delivery #{delivery.delivery_id} has no items to add to inventory.'
                })
            
            inventory_updates = 0
            inventory_transactions = 0
            
            for delivery_item in delivery_items:
                print(f"DEBUG: Processing delivery item - Product: {delivery_item.product.prod_name}, Branch: {delivery_item.branch.branch_name}")
                
                # Check if inventory already exists for this product and branch
                try:
                    inventory = Inventory.objects.get(
                        product=delivery_item.product,
                        branch=delivery_item.branch
                    )
                    print(f"DEBUG: Existing inventory found - Old Qty: {inventory.quantity_on_hand}")
                    
                    # Update existing inventory
                    inventory.quantity_on_hand += delivery_item.quantity_ordered
                    inventory.last_updated_at = timezone.now().date()
                    inventory.user = user
                    inventory.save()
                    print(f"DEBUG: Updated inventory - New Qty: {inventory.quantity_on_hand}")
                    
                except Inventory.DoesNotExist:
                    # Create new inventory
                    print(f"DEBUG: Creating new inventory record")
                    inventory = Inventory.objects.create(
                        product=delivery_item.product,
                        branch=delivery_item.branch,
                        user=user,
                        quantity_on_hand=delivery_item.quantity_ordered,
                        last_updated_at=timezone.now().date()
                    )
                    print(f"DEBUG: Created new inventory with Qty: {inventory.quantity_on_hand}")
                
                inventory_updates += 1
                
                # Get product current cost - handle if it's None
                product_cost = delivery_item.product.prod_current_cost or 0
                print(f"DEBUG: Product cost: {product_cost}")
                
                # Create inventory transaction for stock in
                try:
                    Inventory_Transaction.objects.create(
                        trans_type='stockin',
                        quantity=delivery_item.quantity_ordered,
                        unit_cost=product_cost,
                        inventory=inventory,  # Link to the inventory we just saved
                        user=user,
                        created_at=timezone.now()
                    )
                    print(f"DEBUG: Created inventory transaction")
                    inventory_transactions += 1
                except Exception as e:
                    print(f"ERROR creating transaction: {str(e)}")
                
                print(f"DEBUG: Added {delivery_item.quantity_ordered} units of {delivery_item.product.prod_name} to {delivery_item.branch.branch_name} inventory")
            
            return JsonResponse({
                'success': True,
                'message': f'✅ Requisition(s) marked as fulfilled! {updated_count} requisition(s) completed. Added {inventory_updates} items to inventory.',
                'new_status': 'FULFILLED',
                'requisitions_updated': updated_count,
                'inventory_updates': inventory_updates,
                'inventory_transactions': inventory_transactions,
                'po_id': po_id,
                'delivery_id': delivery.delivery_id
            })
            
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})