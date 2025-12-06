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
        
        # Get only GOOD condition discrepancies for this PO
        good_discrepancies = Discrepancy.objects.filter(
            purchase_order=purchase_order,
            disc_condition='good'
        ).select_related('product', 'po_item', 'po_item__product', 'inspected_by')
        
        # Get the requisition for this PO (main requisition)
        main_requisition = purchase_order.requisition
        
        # Get all PO items for this purchase order
        po_items = Purchase_Order_Item.objects.filter(
            purchase_order=purchase_order
        ).select_related(
            'requisition_item', 
            'requisition_item__requisition',
            'requisition_item__requisition__requested_by',
            'requisition_item__requisition__requested_by__branch',
            'product'
        )
        
        # Group PO items by their associated requisition
        requisition_items_dict = defaultdict(list)
        all_requisitions = []
        
        # Add main requisition
        all_requisitions.append(main_requisition)
        
        # Group items by requisition
        for po_item in po_items:
            if po_item.requisition_item:
                req = po_item.requisition_item.requisition
                requisition_items_dict[req.req_id].append(po_item)
                
                # Add to all_requisitions if not already there
                if req not in all_requisitions:
                    all_requisitions.append(req)
            else:
                # If no requisition_item link, assume it belongs to main requisition
                requisition_items_dict[main_requisition.req_id].append(po_item)
        
        # Get requisition items for each requisition
        requisition_items_data = []
        for req in all_requisitions:
            # Get requisition items for this requisition
            req_items = RequisitionItem.objects.filter(
                requisition=req
            ).select_related('product')
            
            # Get PO items for this requisition
            po_items_for_req = requisition_items_dict.get(req.req_id, [])
            
            # Match requisition items with PO items
            items_with_po_info = []
            for req_item in req_items:
                # Find matching PO item
                po_item_match = None
                for po_item in po_items_for_req:
                    if po_item.product.prod_id == req_item.product.prod_id:
                        po_item_match = po_item
                        break
                
                # Get requisition item quantity
                req_quantity = 0
                if hasattr(req_item, 'ri_quantity'):
                    req_quantity = req_item.ri_quantity
                elif hasattr(req_item, 'quantity'):
                    req_quantity = req_item.quantity
                elif hasattr(req_item, 'req_quantity'):
                    req_quantity = req_item.req_quantity
                elif hasattr(req_item, 'item_quantity'):
                    req_quantity = req_item.item_quantity
                
                items_with_po_info.append({
                    'requisition_item': req_item,
                    'po_item': po_item_match,
                    'po_quantity': po_item_match.po_item_ordered_quantity if po_item_match else 0,
                    'req_quantity': req_quantity
                })
            
            requisition_items_data.append({
                'requisition': req,
                'items': items_with_po_info,
                'is_main': req.req_id == main_requisition.req_id
            })
        
        # Organize good discrepancies by product and requisition
        product_requisition_map = {}
        for po_item in po_items:
            if po_item.requisition_item:
                product_requisition_map[po_item.product.prod_id] = po_item.requisition_item.requisition
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
            
            requisition_summary.append({
                'requisition': req,
                'good_discrepancies': good_items_for_req,
                'good_item_count': len(good_items_for_req),
                'total_good_qty': total_good_qty,
                'is_main': req.req_id == main_requisition.req_id
            })
        
        # Check if a delivery already exists for this PO
        existing_delivery = Delivery.objects.filter(purchase_order=purchase_order).first()
        
        context = {
            'user': user,
            'active_page': 'manage_delivery',
            'purchase_order': purchase_order,
            'main_requisition': main_requisition,
            'requisition_items_data': requisition_items_data,  # For displaying requisition items
            'requisition_summary': requisition_summary,  # For available items
            'all_requisitions': all_requisitions,
            'has_multiple_requisitions': len(all_requisitions) > 1,
            'good_discrepancies': good_discrepancies,
            'existing_delivery': existing_delivery,
            'single_po': True,
        }
        
        return render(request, 'main/manage_delivery.html', context)  # MAKE SURE THIS LINE IS PROPERLY INDENTED
        
    else:
        # Get all POs with good items for selection
        purchase_orders = Purchase_Order.objects.filter(
            discrepancy__disc_condition='good',
            requisition__req_main_status='TO_BE_DELIVERED'
        ).distinct().select_related('requisition', 'supplier')
        
        # Add good item count to each PO
        purchase_orders_with_counts = []
        for po in purchase_orders:
            good_count = Discrepancy.objects.filter(
                purchase_order=po,
                disc_condition='good'
            ).count()
            
            purchase_orders_with_counts.append({
                'po': po,
                'good_count': good_count
            })
        
        context = {
            'user': user,
            'active_page': 'manage_delivery',
            'purchase_orders': purchase_orders_with_counts,
            'single_po': False,
        }
        
        return render(request, 'main/manage_delivery.html', context)  # MAKE SURE THIS LINE IS PROPERLY INDENTED


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
            
            # Parse delivery data
            delivery_data = json.loads(request.body)
            delivery_items = delivery_data.get('items', [])
            
            if not delivery_items:
                return JsonResponse({'success': False, 'error': 'No items selected for delivery'})
            
            main_requisition = purchase_order.requisition
            
            # Create delivery record
            delivery = Delivery.objects.create(
                purchase_order=purchase_order,     
                requisition=main_requisition,
                delivered_by=purchase_order.supplier,
                delivery_date=timezone.now(),
                delivery_status='IN_TRANSIT',
                delivery_notes=delivery_data.get('notes', '')
            )
            
            # Create delivery items with branch information
            for item_data in delivery_items:
                discrepancy = get_object_or_404(Discrepancy, disc_id=item_data['disc_id'])
                
                # Get branch for this delivery item
                branch = None
                
                # Method 1: Try to get branch through requisition_item
                if discrepancy.po_item.requisition_item:
                    # Get requisition from requisition_item
                    requisition = discrepancy.po_item.requisition_item.requisition
                    branch = requisition.branch
                else:
                    # Method 2: If no requisition_item link, use main requisition's branch
                    branch = purchase_order.requisition.branch
                
                # Create DeliveryItem with branch information
                DeliveryItem.objects.create(
                    delivery=delivery,
                    product=discrepancy.product,
                    purchase_order_item=discrepancy.po_item,
                    branch=branch,  # Save the branch
                    quantity_ordered=item_data['quantity'],
                )
            
            # Update ALL requisitions linked to this PO to IN_TRANSIT status
            po_items = Purchase_Order_Item.objects.filter(
                purchase_order=purchase_order
            ).select_related('requisition_item__requisition')
            
            updated_requisitions = set()
            
            for po_item in po_items:
                if po_item.requisition_item:
                    requisition = po_item.requisition_item.requisition
                    if requisition.req_id not in updated_requisitions:
                        # UPDATE BOTH MAIN STATUS AND SUB-STATUS
                        requisition.req_main_status = 'INSPECTION'
                        requisition.req_substatus = 'IN_TRANSIT'
                        requisition.save()
                        
                        # Create status timeline entry
                        RequisitionStatusTimeline.objects.create(
                            requisition=requisition,
                            sub_status='IN_TRANSIT',
                            user=user,
                            comment=f'Delivery created by {user.user_fname} {user.user_lname}. Items being delivered.'
                        )
                        updated_requisitions.add(requisition.req_id)
            
            # Also update the main requisition if not already updated
            if main_requisition.req_id not in updated_requisitions:
                main_requisition.req_main_status = 'INSPECTION'
                main_requisition.req_substatus = 'IN_TRANSIT'
                main_requisition.save()
                
                RequisitionStatusTimeline.objects.create(
                    requisition=main_requisition,
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