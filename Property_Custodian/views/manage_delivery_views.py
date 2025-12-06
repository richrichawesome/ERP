from django.shortcuts import render, redirect, get_object_or_404
from ERP.models import User
from Property_Custodian.models import Purchase_Order, Purchase_Order_Item, Discrepancy, Delivery, DeliveryItem
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from collections import defaultdict

def manage_delivery(request, po_id=None):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    user = User.objects.get(pk=user_id)
    
    # Get specific PO if po_id is provided, otherwise get all POs with good items
    if po_id:
        purchase_order = get_object_or_404(Purchase_Order, po_id=po_id)
        
        # Get all requisitions linked to this PO
        all_requisitions = purchase_order.requisitions.all()
        
        if not all_requisitions.exists():
            return render(request, 'main/manage_delivery.html', {
                'user': user,
                'active_page': 'manage_delivery',
                'error': 'No requisitions found for this purchase order.',
                'single_po': True,
            })
        
        # Get the main/first requisition for display purposes
        main_requisition = all_requisitions.first()
        
        # Get only GOOD condition discrepancies for this PO
        good_discrepancies = Discrepancy.objects.filter(
            purchase_order=purchase_order,
            disc_condition='good'
        ).select_related('product', 'po_item', 'po_item__product', 'inspected_by')
        
        # Get all PO items for this purchase order
        po_items = Purchase_Order_Item.objects.filter(
            purchase_order=purchase_order
        ).select_related('product')
        
        # Get all requisition items from all linked requisitions
        all_requisition_items = RequisitionItem.objects.filter(
            requisition__in=all_requisitions
        ).select_related('requisition', 'product')
        
        # Create a mapping of product to requisition items
        product_to_requisition = {}
        for req_item in all_requisition_items:
            product_to_requisition[req_item.product.prod_id] = {
                'requisition': req_item.requisition,
                'requisition_item': req_item
            }
        
        # DEBUG: Print what we found
        print(f"DEBUG: PO has {po_items.count()} PO items")
        print(f"DEBUG: Found {all_requisition_items.count()} requisition items")
        print(f"DEBUG: Product mapping has {len(product_to_requisition)} products")
        
        # Group PO items by their associated requisition
        requisition_items_dict = defaultdict(list)
        
        # Group items by requisition using product mapping
        for po_item in po_items:
            product_info = product_to_requisition.get(po_item.product.prod_id)
            
            if product_info:
                # This PO item belongs to a specific requisition
                req = product_info['requisition']
                requisition_items_dict[req.req_id].append({
                    'po_item': po_item,
                    'requisition_item': product_info['requisition_item']
                })
                print(f"DEBUG: PO item {po_item.product.prod_name} assigned to REQ-{req.req_id}")
            else:
                # If we can't find a matching requisition item, assign to main requisition
                requisition_items_dict[main_requisition.req_id].append({
                    'po_item': po_item,
                    'requisition_item': None
                })
                print(f"DEBUG: PO item {po_item.product.prod_name} assigned to main REQ-{main_requisition.req_id} (no matching requisition item)")
        
        # Get requisition items for each requisition (simplified version)
        requisition_items_data = []
        for req in all_requisitions:
            items_info = requisition_items_dict.get(req.req_id, [])
            
            items_with_po_info = []
            for item_info in items_info:
                po_item = item_info['po_item']
                req_item = item_info['requisition_item']
                
                # Get requisition item quantity
                req_quantity = req_item.quantity if req_item else 0
                
                items_with_po_info.append({
                    'requisition_item': req_item,
                    'po_item': po_item,
                    'po_quantity': po_item.po_item_ordered_quantity,
                    'req_quantity': req_quantity,
                    'product': po_item.product  # Add product for easier template access
                })
            
            # Also include original requisition items even if not in PO
            if req == main_requisition:
                # For main requisition, also show items that might not be in PO yet
                original_req_items = RequisitionItem.objects.filter(requisition=req).select_related('product')
                for req_item in original_req_items:
                    # Check if this item is already in items_with_po_info
                    already_exists = any(
                        item['requisition_item'] and item['requisition_item'].req_item_id == req_item.req_item_id 
                        for item in items_with_po_info
                    )
                    
                    if not already_exists:
                        items_with_po_info.append({
                            'requisition_item': req_item,
                            'po_item': None,
                            'po_quantity': 0,
                            'req_quantity': req_item.quantity,
                            'product': req_item.product
                        })
            
            requisition_items_data.append({
                'requisition': req,
                'items': items_with_po_info,
                'is_main': req.req_id == main_requisition.req_id,
                'item_count': len(items_with_po_info)
            })
        
        # Organize good discrepancies by product and requisition
        product_requisition_map = {}
        for po_item in po_items:
            product_info = product_to_requisition.get(po_item.product.prod_id)
            if product_info:
                product_requisition_map[po_item.product.prod_id] = product_info['requisition']
            else:
                product_requisition_map[po_item.product.prod_id] = main_requisition
        
        # Group good discrepancies by requisition
        good_discrepancies_by_requisition = defaultdict(list)
        for disc in good_discrepancies:
            req = product_requisition_map.get(disc.product.prod_id, main_requisition)
            good_discrepancies_by_requisition[req.req_id].append({
                'disc': disc,
                'requisition': req
            })
        
        # Create requisition summary for available items
        requisition_summary = []
        for req in all_requisitions:
            good_items_for_req = good_discrepancies_by_requisition.get(req.req_id, [])
            
            total_good_qty = sum(item['disc'].disc_quantity for item in good_items_for_req)
            
            # Get total items count for this requisition
            items_info = requisition_items_dict.get(req.req_id, [])
            
            requisition_summary.append({
                'requisition': req,
                'good_discrepancies': good_items_for_req,
                'good_item_count': len(good_items_for_req),
                'total_good_qty': total_good_qty,
                'is_main': req.req_id == main_requisition.req_id,
                'total_items': len(items_info)
            })
        
        # Check if a delivery already exists for this PO
        existing_delivery = Delivery.objects.filter(purchase_order=purchase_order).first()
        
        context = {
            'user': user,
            'active_page': 'manage_delivery',
            'purchase_order': purchase_order,
            'main_requisition': main_requisition,
            'all_requisitions': all_requisitions,
            'requisition_items_data': requisition_items_data,
            'requisition_summary': requisition_summary,
            'has_multiple_requisitions': all_requisitions.count() > 1,
            'good_discrepancies': good_discrepancies,
            'existing_delivery': existing_delivery,
            'single_po': True,
        }
        
        return render(request, 'main/manage_delivery.html', context)
        
    else:
        # Get all POs with good items for selection
        purchase_orders = Purchase_Order.objects.filter(
            discrepancy__disc_condition='good',
            requisitions__req_main_status='TO_BE_DELIVERED'
        ).distinct().prefetch_related('requisitions', 'supplier')
        
        # Add good item count to each PO
        purchase_orders_with_counts = []
        for po in purchase_orders:
            good_count = Discrepancy.objects.filter(
                purchase_order=po,
                disc_condition='good'
            ).count()
            
            # Get requisitions count for this PO
            requisitions_count = po.requisitions.count()
            
            purchase_orders_with_counts.append({
                'po': po,
                'good_count': good_count,
                'requisitions_count': requisitions_count
            })
        
        context = {
            'user': user,
            'active_page': 'manage_delivery',
            'purchase_orders': purchase_orders_with_counts,
            'single_po': False,
        }
        
        return render(request, 'main/manage_delivery.html', context)


@csrf_exempt
def create_delivery(request, po_id):
    """View to create a delivery for a PO"""
    if request.method == 'POST':
        try:
            user_id = request.session.get('user_id')
            if not user_id:
                return JsonResponse({'success': False, 'error': 'User not authenticated'})
            
            user = User.objects.get(pk=user_id)
            purchase_order = get_object_or_404(Purchase_Order, po_id=po_id)
            
            # Get the main/first requisition
            all_requisitions = purchase_order.requisitions.all()
            if not all_requisitions.exists():
                return JsonResponse({'success': False, 'error': 'No requisitions found for this purchase order'})
            
            main_requisition = all_requisitions.first()
            
            # Parse delivery data
            delivery_data = json.loads(request.body)
            delivery_items = delivery_data.get('items', [])
            
            if not delivery_items:
                return JsonResponse({'success': False, 'error': 'No items selected for delivery'})
            
            # Create delivery record
            delivery = Delivery.objects.create(
                purchase_order=purchase_order,     
                requisition=main_requisition,
                delivered_by=purchase_order.supplier,
                delivery_date=timezone.now(),
                delivery_status='IN_TRANSIT',
                delivery_notes=delivery_data.get('notes', '')
            )
            
            # Get all requisition items to find branches
            all_requisition_items = RequisitionItem.objects.filter(
                requisition__in=all_requisitions
            ).select_related('requisition', 'product')
            
            # Create a mapping of product to requisition (for branch info)
            product_to_requisition = {}
            for req_item in all_requisition_items:
                product_to_requisition[req_item.product.prod_id] = req_item.requisition
            
            # Create delivery items with branch information
            for item_data in delivery_items:
                discrepancy = get_object_or_404(Discrepancy, disc_id=item_data['disc_id'])
                
                # Get branch for this delivery item
                branch = None
                
                # Try to find which requisition this product belongs to
                req = product_to_requisition.get(discrepancy.product.prod_id)
                if req:
                    branch = req.branch
                else:
                    # If not found, use main requisition's branch
                    branch = main_requisition.branch
                
                # Create DeliveryItem with branch information
                DeliveryItem.objects.create(
                    delivery=delivery,
                    product=discrepancy.product,
                    purchase_order_item=discrepancy.po_item,
                    branch=branch,
                    quantity_ordered=item_data['quantity'],
                )
            
            # Update ALL requisitions linked to this PO to IN_TRANSIT status
            for req in all_requisitions:
                # UPDATE BOTH MAIN STATUS AND SUB-STATUS
                req.req_main_status = 'INSPECTION'
                req.req_substatus = 'IN_TRANSIT'
                req.save()
                
                # Create status timeline entry
                RequisitionStatusTimeline.objects.create(
                    requisition=req,
                    main_status='INSPECTION',
                    sub_status='IN_TRANSIT',
                    user=user,
                    comment=f'Delivery created by {user.user_fname} {user.user_lname}. Items being delivered.'
                )
            
            return JsonResponse({
                'success': True,
                'message': 'Delivery created successfully!',
                'delivery_id': delivery.delivery_id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})