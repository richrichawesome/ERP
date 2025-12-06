# from django.shortcuts import render, redirect
# from ERP.models import User


# def create_po(request):
#     user_id = request.session.get("user_id")   # the ID you saved during login
#     user = User.objects.get(pk=user_id)
#     return render(request, "purchasing/create_po.html", {"active_page": "po",  "user": user})



from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum
from django.utils import timezone
from django.db import transaction
import json
from datetime import date

# Import models
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from ERP.models import Product, Branch, User
from Purchasing.models import Supplier, Supplier_Product, Purchase_Order, Purchase_Order_Item, Supplier_Quotation, RFQ_Supplier


@csrf_exempt
def preview_po_data(request):
    """Generate preview data for PO before creating it - similar to preview_rfq_data"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
    
    try:
        user = User.objects.get(pk=user_id)
        
        # Get selected requisition IDs from POST
        req_ids = request.POST.getlist('req_ids[]')
        if not req_ids:
            return JsonResponse({'success': False, 'error': 'No requisitions selected'}, status=400)
        
        requisitions = Requisition.objects.filter(
            req_id__in=req_ids, 
            req_main_status='APPROVED_REQUISITION',
            req_substatus='PENDING_PO'
        )
        
        if not requisitions.exists():
            return JsonResponse({'success': False, 'error': 'No valid approved requisitions found'}, status=400)
        
        # Get Branch 1 information for Ship To
        try:
            branch = Branch.objects.get(branch_id=1)
        except Branch.DoesNotExist:
            branch = None
        
        # Group products by product name and description (specification)
        grouped_products = {}
        
        for req in requisitions:
            for item in req.items.all():
                key = f"{item.product.prod_name}_{item.product.prod_desc}"
                
                if key not in grouped_products:
                    # Get all active suppliers for this product
                    supplier_products = Supplier_Product.objects.filter(
                        product=item.product,
                        sup_prod_is_active=True
                    ).select_related('supplier')
                    
                    # suppliers_list = []
                    # for sp in supplier_products:
                    #     suppliers_list.append({
                    #         'supplier_id': sp.supplier.sup_id,
                    #         'supplier_name': sp.supplier.sup_name,
                    #         'price': float(sp.sup_prod_unit_price),
                    #         'eta': 'TBD'  # Can add ETA field if needed
                    #     })

                    # suppliers_list = []
                    # for sp in supplier_products:
                    #     # Try to get the latest quotation for this supplier
                    #     try:
                    #         latest_qtn = Supplier_Quotation.objects \
                    #             .filter(rfq_supplier__supplier=sp.supplier) \
                    #             .order_by('-sup_qtn_created_at') \
                    #             .first()
                    #     except Supplier_Quotation.DoesNotExist:
                    #         latest_qtn = None

                    #     suppliers_list.append({
                    #         'supplier_id': sp.supplier.sup_id,
                    #         'supplier_name': sp.supplier.sup_name,
                    #         'price': float(sp.sup_prod_unit_price),
                    #         'eta': (latest_qtn.sup_qtn_eta.strftime('%Y-%m-%d')
                    #                 if latest_qtn and latest_qtn.sup_qtn_eta
                    #                 else 'TBD')
                    #     })






                    suppliers_list = []

                    for sp in supplier_products:
                        # Get the latest supplier quotation for this supplier
                        quotation = Supplier_Quotation.objects.filter(
                            rfq_supplier__supplier=sp.supplier
                        ).order_by('-sup_qtn_created_at').first()

                        # Convert ETA to "X days"
                        if quotation and quotation.sup_qtn_eta:
                            delta_days = (quotation.sup_qtn_eta - date.today()).days
                            eta_str = f"{delta_days} days" if delta_days >= 0 else "Expired"
                            eta_sort = delta_days if delta_days >= 0 else 9999
                        else:
                            eta_str = "TBD"

                        suppliers_list.append({
                            'supplier_id': sp.supplier.sup_id,
                            'supplier_name': sp.supplier.sup_name,
                            'price': float(sp.sup_prod_unit_price),
                            'eta': eta_str,
                            'eta_sort': eta_sort,
                        })

                    # SORT: lowest price first; if tie → earliest ETA
                    suppliers_list.sort(key=lambda s: (s['price'], s['eta_sort']))




                    # suppliers_list = []

                    # for sp in supplier_products:

                    #     # 1. Find the RFQ_Supplier entry for THIS rfq & THIS supplier
                    #     rfq_supplier = RFQ_Supplier.objects.filter(
                    #         rfq=rfq,
                    #         supplier=sp.supplier
                    #     ).first()

                    #     # 2. Find the Supplier_Quotation
                    #     quotation = None
                    #     if rfq_supplier:
                    #         quotation = Supplier_Quotation.objects.filter(
                    #             rfq_supplier=rfq_supplier
                    #         ).first()

                    #     # 3. Convert ETA to “X days”
                    #     if quotation and quotation.sup_qtn_eta:
                    #         days_left = (quotation.sup_qtn_eta - date.today()).days
                    #         eta_label = f"{days_left} days" if days_left >= 0 else "Expired"
                    #     else:
                    #         eta_label = "TBD"

                    #     suppliers_list.append({
                    #         'supplier_id': sp.supplier.sup_id,
                    #         'supplier_name': sp.supplier.sup_name,
                    #         'price': float(sp.sup_prod_unit_price),
                    #         'eta': eta_label
                    #     })














                    
                    grouped_products[key] = {
                        'product_id': item.product.prod_id,
                        'product_name': item.product.prod_name,
                        'specification': item.product.prod_desc,
                        'uom': item.product.prod_unit_of_measure,
                        'quantity': item.quantity,
                        'req_item_ids': [item.req_item_id],
                        'suppliers': suppliers_list
                    }
                else:
                    # Add to existing group
                    grouped_products[key]['quantity'] += item.quantity
                    grouped_products[key]['req_item_ids'].append(item.req_item_id)
        
        # Prepare preview data
        preview_data = {
            'success': True,
            'branch_info': {
                'name': branch.branch_name if branch else '[Main Branch]',
                'address': branch.branch_address if branch else '[Main Branch Address]',
                'phone': branch.branch_phone if branch else '[Main Branch Contact Number]',
            },
            'user_info': {
                'name': f"{user.user_fname} {user.user_lname}",
            },
            'po_info': {
                'requisition_ids': req_ids,
                'requisition_count': len(requisitions),
            },
            'products': list(grouped_products.values())
        }
        
        return JsonResponse(preview_data)
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def create_po_multiple(request):
    """Create POs for multiple requisitions with selected suppliers"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
    
    try:
        user = User.objects.get(pk=user_id)
        
        # Get data from POST
        req_ids = request.POST.getlist('req_ids[]')
        po_data_json = request.POST.get('po_data')
        
        if not req_ids or not po_data_json:
            return JsonResponse({'success': False, 'error': 'Missing required data'}, status=400)
        
        po_data = json.loads(po_data_json)
        
        with transaction.atomic():
            created_pos = []
            
            # Create PO for each supplier group
            for supplier_group in po_data:
                supplier_id = supplier_group.get('supplier_id')
                products = supplier_group.get('products', [])
                
                if not supplier_id or not products:
                    continue
                
                # Calculate totals
                po_total = sum(p['quantity'] * p['unit_price'] for p in products)
                
                # Create PO record
                po = Purchase_Order.objects.create(
                    supplier_id=supplier_id,
                    branch_id=1,  # Always Branch 1
                    user=user,
                    po_main_status='PO_APPROVAL',
                    po_substatus='NONE',
                    po_subtotal=po_total,
                    po_total_amount=po_total
                )
                
                # Create PO items
                for product in products:
                    line_total = product['quantity'] * product['unit_price']
                    Purchase_Order_Item.objects.create(
                        purchase_order=po,
                        product_id=product['product_id'],
                        po_item_ordered_quantity=product['quantity'],
                        po_item_unit_price=product['unit_price'],
                        po_item_line_total=line_total
                    )
                
                created_pos.append({
                    'po_id': po.po_id,
                    'supplier_id': supplier_id,
                    'supplier_name': Supplier.objects.get(sup_id=supplier_id).sup_name,
                    'total': float(po_total)
                })
            
            # Update requisition status and link to first PO
            if created_pos:
                first_po = Purchase_Order.objects.get(po_id=created_pos[0]['po_id'])
                requisitions = Requisition.objects.filter(req_id__in=req_ids)
                
                for req in requisitions:
                    req.req_main_status = 'PO_APPROVAL'
                    req.req_substatus = 'PENDING_APPROVAL'
                    req.po = first_po
                    req.save()
                    
                    # Create timeline entry
                    RequisitionStatusTimeline.objects.create(
                        requisition=req,
                        main_status='PO_APPROVAL',
                        sub_status='PENDING_APPROVAL',
                        user=user,
                        comment='Purchase Order created'
                    )
            
            return JsonResponse({
                'success': True,
                'created_pos': created_pos,
                'message': f'{len(created_pos)} Purchase Order(s) created successfully'
            })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
def generate_po_preview_data(request):
    """Generate PO preview data with supplier details for display"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    try:
        po_data_json = request.POST.get('po_data')
        if not po_data_json:
            return JsonResponse({'success': False, 'error': 'No PO data provided'}, status=400)
        
        po_data = json.loads(po_data_json)
        
        # Get Branch 1 details for Ship To
        try:
            branch1 = Branch.objects.get(branch_id=1)
        except Branch.DoesNotExist:
            branch1 = None
        
        # Organize POs by supplier
        po_previews = []
        
        for supplier_group in po_data:
            supplier_id = supplier_group.get('supplier_id')
            products = supplier_group.get('products', [])
            
            if not supplier_id or not products:
                continue
            
            # Get supplier details
            supplier = Supplier.objects.get(sup_id=supplier_id)
            
            # Calculate items
            items = []
            subtotal = 0
            
            for product in products:
                quantity = product.get('quantity')
                unit_price = product.get('unit_price')
                total = quantity * unit_price
                subtotal += total
                
                items.append({
                    'product_name': product.get('product_name'),
                    'specification': product.get('specification'),
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total': total
                })
            
            po_previews.append({
                'supplier': {
                    'sup_id': supplier.sup_id,
                    'sup_name': supplier.sup_name,
                    'sup_contact_person': supplier.sup_contact_person,
                    'sup_phone': supplier.sup_phone,
                    'sup_address': supplier.sup_address if supplier.sup_address else 'N/A'
                },
                'ship_to': {
                    'branch_name': branch1.branch_name if branch1 else '[Main Branch]',
                    'branch_phone': branch1.branch_phone if branch1 else '[Contact Number]',
                    'branch_address': branch1.branch_address if branch1 else '[Address]'
                },
                'items': items,
                'subtotal': subtotal
            })
        
        return JsonResponse({
            'success': True,
            'po_previews': po_previews
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)