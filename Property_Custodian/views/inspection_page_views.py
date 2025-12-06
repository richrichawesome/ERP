from django.shortcuts import render, get_object_or_404, redirect
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from Property_Custodian.models import Purchase_Order, Purchase_Order_Item, Discrepancy, Receiving_Memo
from ERP.models import User, Product  # Added Product import here
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

def inspection_page(request, req_id):
    """View to handle the inspection page for a requisition"""
    
    user_id = request.session.get('user_id')
    
    user = User.objects.get(pk=user_id)
    if not user_id:
        return redirect('login')
    
    # Get the requisition
    requisition = get_object_or_404(Requisition, req_id=req_id)
    
    # Check if requisition is in correct status for inspection
    if requisition.req_main_status != 'INSPECTION':
        return render(request, 'main/inspection_page.html', {
            'error': 'Requisition is not in INSPECTION status. Current status: ' + requisition.get_req_main_status_display(),
            'requisition': requisition
        })
    
    # Only allow inspection if substatus is INSPECTING
    if requisition.req_substatus != 'INSPECTING':
        return render(request, 'main/inspection_page.html', {
            'error': f'Inspection has not been started yet. Please click "Start Inspection" button first. Current substatus: {requisition.get_req_substatus_display()}',
            'requisition': requisition
        })
    
    # Get the purchase order for this requisition
    try:
        purchase_order = Purchase_Order.objects.get(requisition=requisition)
    except Purchase_Order.DoesNotExist:
        return render(request, 'main/inspection_page.html', {
            'error': 'No purchase order found for this requisition. Cannot proceed with inspection.',
            'requisition': requisition
        })
    
    # Get ALL PO items for this purchase order (including items from other requisitions)
    po_items = Purchase_Order_Item.objects.filter(
        purchase_order=purchase_order
    ).select_related('product', 'requisition_item', 'requisition_item__requisition')
    
    if not po_items.exists():
        return render(request, 'main/inspection_page.html', {
            'error': 'No items found in the purchase order. Cannot proceed with inspection.',
            'requisition': requisition,
            'purchase_order': purchase_order
        })
    
    # Group PO items by their associated requisition
    requisition_items_dict = defaultdict(list)
    all_requisitions = []
    
    # Add main requisition
    main_requisition = purchase_order.requisition
    all_requisitions.append(main_requisition)
    
    # Check for additional requisitions through PO items
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
    
    # Create requisition summary for the template
    requisition_summary = []
    for req in all_requisitions:
        items_for_req = requisition_items_dict.get(req.req_id, [])
        total_qty = sum(item.po_item_ordered_quantity for item in items_for_req)
        
        requisition_summary.append({
            'requisition': req,
            'item_count': len(items_for_req),
            'total_quantity': total_qty,
            'is_main': req.req_id == main_requisition.req_id
        })
    
    context = {
        'requisition': requisition,
        'purchase_order': purchase_order,
        'po_items': po_items,
        'requisition_summary': requisition_summary,
        'has_multiple_requisitions': len(all_requisitions) > 1,
        'all_requisitions': all_requisitions,
        'error': None,
        "user": user,
        "active_page": "requisition",
    }
    
    return render(request, 'main/inspection_page.html', context)

@csrf_exempt
def save_inspection_discrepancies(request, req_id):
    """View to save inspection discrepancies when inspection is completed"""
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
            
            # Get the purchase order
            try:
                purchase_order = Purchase_Order.objects.get(requisition=requisition)
            except Purchase_Order.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'No purchase order found'
                })
            
            # Parse the inspection data from request
            inspection_data = json.loads(request.body)
            items_data = inspection_data.get('items', {})
            
            discrepancies_created = 0
            
            # Process each item
            for po_item_id, item_data in items_data.items():
                po_item = get_object_or_404(Purchase_Order_Item, po_item_id=po_item_id)
                
                # Save GOOD condition items
                if item_data.get('good', {}).get('quantity', 0) > 0:
                    Discrepancy.objects.create(
                        purchase_order=purchase_order,
                        po_item=po_item,
                        product=po_item.product,
                        disc_condition='good',
                        disc_quantity=item_data['good']['quantity'],
                        notes=item_data['good'].get('notes', ''),
                        inspected_by=user
                    )
                    discrepancies_created += 1
                
                # Save DAMAGED condition items
                if item_data.get('damaged', {}).get('quantity', 0) > 0:
                    Discrepancy.objects.create(
                        purchase_order=purchase_order,
                        po_item=po_item,
                        product=po_item.product,
                        disc_condition='damaged',
                        disc_quantity=item_data['damaged']['quantity'],
                        damage_type=item_data['damaged'].get('type', ''),
                        inspected_by=user
                    )
                    discrepancies_created += 1
                
                # Save MISSING condition items
                if item_data.get('missing', {}).get('quantity', 0) > 0:
                    Discrepancy.objects.create(
                        purchase_order=purchase_order,
                        po_item=po_item,
                        product=po_item.product,
                        disc_condition='missing',
                        disc_quantity=item_data['missing']['quantity'],
                        missing_reason=item_data['missing'].get('reason', ''),
                        inspected_by=user
                    )
                    discrepancies_created += 1
                
                # Save EXCESS condition items
                if item_data.get('excess', {}).get('quantity', 0) > 0:
                    Discrepancy.objects.create(
                        purchase_order=purchase_order,
                        po_item=po_item,
                        product=po_item.product,
                        disc_condition='excess',
                        disc_quantity=item_data['excess']['quantity'],
                        excess_action=item_data['excess'].get('action', ''),
                        inspected_by=user
                    )
                    discrepancies_created += 1
                
                # Save WRONG ITEM condition
                if item_data.get('wrong', {}).get('quantity', 0) > 0:
                    Discrepancy.objects.create(
                        purchase_order=purchase_order,
                        po_item=po_item,
                        product=po_item.product,
                        disc_condition='wrong',
                        disc_quantity=item_data['wrong']['quantity'],
                        correct_item=item_data['wrong'].get('correctItem', ''),
                        inspected_by=user
                    )
                    discrepancies_created += 1
            
            # Update requisition status to IN_TRANSIT
            old_substatus = requisition.req_substatus
            requisition.save()
            
            # Create status timeline entry
            RequisitionStatusTimeline.objects.create(
                requisition=requisition,
                main_status='INSPECTION',
                sub_status='IN_TRANSIT',  
                user=user,
                comment=f'Inspection completed by {user.user_fname} {user.user_lname}. {discrepancies_created} discrepancy records created. Products now in transit.'
            )
            
            # Store the timestamp before creating the memo to capture only new discrepancies
            inspection_timestamp = timezone.now()
            
            # Create Receiving Memo
            receiving_memo = Receiving_Memo.objects.create(
                delivery=None,  # Link to delivery if you have delivery record
                purchase_order=purchase_order,  # Added this
                requisition=requisition,  # Added this
                generated_by=user,
                rm_date=inspection_timestamp,
                rm_notes=f'Inspection completed for REQ-{requisition.req_id}, PO-{purchase_order.po_id}. {discrepancies_created} discrepancy records created.'
            )
            
            # Get only the discrepancies created in THIS inspection session (last few seconds)
            time_window = inspection_timestamp - timedelta(seconds=5)
            
            discrepancies = Discrepancy.objects.filter(
                purchase_order=purchase_order,
                inspected_by=user,
                inspection_date__gte=time_window  # Only discrepancies created in the last 5 seconds
            ).select_related('product', 'po_item')
            
            # Prepare memo data
            memo_data = {
                'rm_id': receiving_memo.rm_id,
                'requisition': {
                    'req_id': requisition.req_id,
                    'requested_by': f"{requisition.requested_by.user_fname} {requisition.requested_by.user_lname}"
                },
                'purchase_order': {
                    'po_id': purchase_order.po_id,
                    'supplier': purchase_order.supplier.sup_name
                },
                'inspector': f"{user.user_fname} {user.user_lname}",
                'inspection_date': timezone.now().strftime('%B %d, %Y %I:%M %p'),
                'items': []
            }
            
            # Group discrepancies by product
            product_discrepancies = defaultdict(list)
            
            for disc in discrepancies:
                product_discrepancies[disc.product.prod_id].append({
                    'condition': disc.disc_condition,
                    'quantity': disc.disc_quantity,
                    'notes': disc.notes or disc.damage_type or disc.missing_reason or disc.excess_action or disc.correct_item or ''
                })
            
            # Format items for memo
            for prod_id, discs in product_discrepancies.items():
                product = Product.objects.get(prod_id=prod_id)
                po_item = Purchase_Order_Item.objects.get(purchase_order=purchase_order, product=product)
                
                item_data = {
                    'name': product.prod_name,
                    'ordered_qty': po_item.po_item_ordered_quantity,
                    'conditions': {}
                }
                
                for disc in discs:
                    condition = disc['condition'].title()
                    if condition not in item_data['conditions']:
                        item_data['conditions'][condition] = {
                            'quantity': 0,
                            'notes': []
                        }
                    item_data['conditions'][condition]['quantity'] += disc['quantity']
                    if disc['notes']:
                        item_data['conditions'][condition]['notes'].append(disc['notes'])
                
                memo_data['items'].append(item_data)
            
            return JsonResponse({
                'success': True,
                'message': f'Inspection completed successfully! {discrepancies_created} discrepancy records saved.',
                'show_memo': True,
                'memo_data': memo_data,
                'redirect_url': f'/requisition_detail/{req_id}/'
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