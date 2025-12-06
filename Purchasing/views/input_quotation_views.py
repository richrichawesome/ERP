# input_quotation_views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json

from Purchasing.models import (
    RFQ, RFQ_Item, RFQ_Supplier, 
    Supplier_Quotation, Supplier_Quotation_Item, 
    Supplier, Supplier_Product, Supplier_Product_PriceHistory
)
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from ERP.models import User


@login_required
def input_quotation(request, rfq_id=None):
    """Display RFQ details for quotation input"""
    if rfq_id:
        rfq = get_object_or_404(RFQ, rfq_id=rfq_id)
        
        rfq_items = RFQ_Item.objects.filter(rfq=rfq).select_related('product')

        # Collect associated requisitions through requisition_item
        requisitions = set()
        for item in rfq_items:
            if item.requisition_item:
                requisitions.add(item.requisition_item.requisition)

        # Prepare items for display
        items_data = []
        for item in rfq_items:
            items_data.append({
                'itemId': item.rfq_item_id,
                'productName': item.product.prod_name,
                'specifications': [
                    {'name': spec.spec_name, 'value': spec.spec_value} 
                    for spec in item.product.product_specification_set.all()
                ],
                'quantity': item.rfq_item_req_qty,
                'uom': item.rfq_item_req_uom or 'Each'
            })

        # Get suppliers who already quoted this RFQ
        existing_suppliers = RFQ_Supplier.objects.filter(rfq=rfq).select_related('supplier')

        context = {
            'rfq': rfq,
            'rfq_items': items_data,
            'requisitions': list(requisitions),
            'existing_suppliers': existing_suppliers,
        }

        return render(request, 'purchasing/quote_creation.html', context)

    return JsonResponse({'error': 'RFQ ID required'}, status=400)


@login_required
def get_rfq_items(request, rfq_id):
    """API endpoint to get RFQ items for quotation input"""
    try:
        rfq = RFQ.objects.get(rfq_id=rfq_id)
        rfq_items = RFQ_Item.objects.filter(rfq=rfq).select_related('product')
        
        items_data = []
        for item in rfq_items:
            # Get product specifications
            specifications = []
            if hasattr(item.product, 'product_specification_set'):
                for spec in item.product.product_specification_set.all():
                    specifications.append({
                        'spec_name': spec.spec_name,
                        'spec_value': spec.spec_value
                    })
            
            items_data.append({
                'rfq_item_id': item.rfq_item_id,
                'product_id': item.product.prod_id,
                'product_name': item.product.prod_name,
                'product_description': item.product.prod_desc,
                'rfq_item_req_uom': item.rfq_item_req_uom,
                'rfq_item_req_qty': item.rfq_item_req_qty,
                'specifications': specifications
            })
        
        return JsonResponse({
            'success': True,
            'rfq_id': rfq_id,
            'items': items_data
        })
        
    except RFQ.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'RFQ not found'
        }, status=404)
    





@csrf_exempt
@require_http_methods(["POST"])
def add_supplier(request):
    """
    Add a new supplier from the quotation input modal
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        sup_name = data.get('sup_name', '').strip()
        sup_phone = data.get('sup_phone', '').strip()
        
        if not sup_name:
            return JsonResponse({'success': False, 'error': 'Supplier name is required'}, status=400)
        
        if not sup_phone:
            return JsonResponse({'success': False, 'error': 'Contact number is required'}, status=400)
        
        # Check if supplier with same name already exists
        if Supplier.objects.filter(sup_name__iexact=sup_name).exists():
            return JsonResponse({
                'success': False, 
                'error': f'Supplier with name "{sup_name}" already exists'
            }, status=400)
        
        with transaction.atomic():
            # Create new supplier
            supplier = Supplier.objects.create(
                sup_name=sup_name,
                sup_phone=sup_phone,
                sup_email=data.get('sup_email', '').strip(),
                sup_address=data.get('sup_address', '').strip(),
                sup_contact_person=data.get('sup_contact_person', '').strip() or 'Unknown',
                sup_payment_terms=data.get('sup_payment_terms', '').strip(),
                sup_delivery_terms=data.get('sup_delivery_terms', '').strip(),
                sup_is_active=True
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier added successfully',
            'supplier': {
                'sup_id': supplier.sup_id,
                'sup_name': supplier.sup_name,
                'sup_phone': supplier.sup_phone,
                'sup_email': supplier.sup_email,
                'sup_contact_person': supplier.sup_contact_person
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in add_supplier: {error_detail}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)





@csrf_exempt
@require_http_methods(["POST"])
def save_supplier_quotation(request):
    """
    Save supplier quotation for an RFQ
    This is called when 'Save Quotation for this Supplier' button is clicked
    Also updates Supplier_Product and creates Supplier_Product_PriceHistory entries
    
    NOTE: This does NOT update requisition substatus - that happens in complete_quotation_input
    """
    try:
        data = json.loads(request.body)
        quotation_data = data.get('quotation_data')
        
        if not quotation_data:
            return JsonResponse({'error': 'No quotation data provided'}, status=400)
        
        rfq_id = quotation_data.get('rfq_id')
        supplier_id = quotation_data.get('supplier_id')
        
        if not rfq_id or not supplier_id:
            return JsonResponse({'error': 'RFQ ID and Supplier ID are required'}, status=400)
        
        with transaction.atomic():
            # Get User from session
            user_id = request.session.get("user_id")
            if not user_id:
                return JsonResponse({'error': 'User not authenticated'}, status=401)
            
            current_user = User.objects.get(pk=user_id)
            
            # Get RFQ and Supplier
            rfq = get_object_or_404(RFQ, rfq_id=rfq_id)
            supplier = get_object_or_404(Supplier, sup_id=supplier_id)
            
            # Create or update RFQ_Supplier
            rfq_supplier, created = RFQ_Supplier.objects.get_or_create(
                rfq=rfq,
                supplier=supplier,
                defaults={'rfq_date_sent': timezone.now()}
            )
            
            # Check if quotation already exists for this supplier
            existing_quotation = Supplier_Quotation.objects.filter(
                rfq_supplier=rfq_supplier
            ).first()
            
            if existing_quotation:
                # Update existing quotation
                supplier_quotation = existing_quotation
                supplier_quotation.sup_qtn_eta = quotation_data.get('eta')
                supplier_quotation.sup_qtn_valid_until = quotation_data.get('valid_until')
                
                # Delete old quotation items
                Supplier_Quotation_Item.objects.filter(
                    supplier_quotation=supplier_quotation
                ).delete()
            else:
                # Create new Supplier Quotation
                supplier_quotation = Supplier_Quotation.objects.create(
                    rfq_supplier=rfq_supplier,
                    sup_qtn_total_cost=Decimal('0.00'),
                    sup_qtn_eta=quotation_data.get('eta'),
                    sup_qtn_valid_until=quotation_data.get('valid_until'),
                    sup_qtn_created_at=timezone.now()
                )
            
            # Process quotation items
            total_cost = Decimal('0.00')
            items = quotation_data.get('items', [])
            
            for item_data in items:
                rfq_item_id = item_data.get('rfq_item_id')
                unit_price = Decimal(str(item_data.get('unit_price', 0)))
                
                if rfq_item_id and unit_price > 0:
                    rfq_item = get_object_or_404(RFQ_Item, rfq_item_id=rfq_item_id)
                    product = rfq_item.product
                    quantity = rfq_item.rfq_item_req_qty
                    
                    # Create Supplier_Quotation_Item
                    Supplier_Quotation_Item.objects.create(
                        supplier_quotation=supplier_quotation,
                        rfq_item=rfq_item,
                        product=product,
                        sup_qtn_item_unit_price=unit_price
                    )
                    
                    # Calculate line total
                    line_total = quantity * unit_price
                    total_cost += line_total
                    
                    # Update or Create Supplier_Product
                    supplier_product, sp_created = Supplier_Product.objects.get_or_create(
                        supplier=supplier,
                        product=product,
                        defaults={
                            'sup_prod_code': f"{supplier.sup_id}-{product.prod_id}",
                            'sup_prod_unit_price': unit_price,
                            'sup_prod_last_updated_price': timezone.now(),
                            'sup_prod_is_active': True
                        }
                    )
                    
                    # If supplier_product already exists, check if price changed
                    if not sp_created:
                        old_price = supplier_product.sup_prod_unit_price
                        if old_price != unit_price:
                            # Price changed, update it
                            supplier_product.sup_prod_unit_price = unit_price
                            supplier_product.sup_prod_last_updated_price = timezone.now()
                            supplier_product.save()
                            
                            # Create price history entry
                            Supplier_Product_PriceHistory.objects.create(
                                supplier_product=supplier_product,
                                price=unit_price,
                                changed_by=current_user,
                                changed_at=timezone.now()
                            )
                    else:
                        # New supplier_product, create initial price history
                        Supplier_Product_PriceHistory.objects.create(
                            supplier_product=supplier_product,
                            price=unit_price,
                            changed_by=current_user,
                            changed_at=timezone.now()
                        )
            
            # Update total cost
            supplier_quotation.sup_qtn_total_cost = total_cost
            supplier_quotation.save()
            
            # Update RFQ_Supplier responded date
            rfq_supplier.date_responded = timezone.now()
            rfq_supplier.save()
            
            # DO NOT UPDATE REQUISITION SUBSTATUS HERE
            # It will be updated when user clicks "Done Quotation"
        
        return JsonResponse({
            'success': True,
            'message': 'Quotation saved successfully',
            'quotation_id': supplier_quotation.sup_qtn_id,
            'total_cost': float(total_cost)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found in session'}, status=401)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in save_supplier_quotation: {error_detail}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def complete_quotation_input(request):
    """
    Mark quotation input as complete and update requisition status to PENDING_PO
    This is called when 'Done Quotation' button is clicked
    """
    try:
        data = json.loads(request.body)
        rfq_id = data.get('rfq_id')
        
        if not rfq_id:
            return JsonResponse({'error': 'RFQ ID is required'}, status=400)
        
        # Check user authentication
        user_id = request.session.get("user_id")
        if not user_id:
            return JsonResponse({'error': 'User not authenticated'}, status=401)
        
        with transaction.atomic():
            current_user = User.objects.get(pk=user_id)
            
            # Get RFQ
            rfq = get_object_or_404(RFQ, rfq_id=rfq_id)
            
            # Verify that at least one quotation exists
            quotation_count = Supplier_Quotation.objects.filter(
                rfq_supplier__rfq=rfq
            ).count()
            
            if quotation_count == 0:
                return JsonResponse({
                    'success': False,
                    'error': 'No quotations have been saved yet'
                }, status=400)
            
            # Get all requisitions related to this RFQ
            # Use the same pattern as create_rfq_multiple
            requisitions = Requisition.objects.filter(rfq=rfq)
            
            if not requisitions.exists():
                return JsonResponse({
                    'success': False,
                    'error': 'No requisitions found for this RFQ'
                }, status=400)
            
            print(f"DEBUG: Found {requisitions.count()} requisitions for RFQ {rfq_id}")
            
            # Update all related requisitions to PENDING_PO substatus
            updated_count = 0
            for req in requisitions:
                print(f"DEBUG: Updating REQ-{req.req_id} from {req.req_substatus} to PENDING_PO")
                
                # Update the requisition substatus - same pattern as create_rfq_multiple
                req.req_substatus = 'PENDING_PO'
                req.save()
                updated_count += 1
                
                # Verify the save
                req.refresh_from_db()
                print(f"DEBUG: After save, REQ-{req.req_id} substatus is now: {req.req_substatus}")
                
                # Create timeline entry for tracking - same pattern as create_rfq_multiple
                RequisitionStatusTimeline.objects.create(
                    requisition=req,
                    main_status=req.req_main_status,
                    sub_status='PENDING_PO',
                    user=current_user,
                    comment=f'Quotation input completed for RFQ-{rfq_id}. {quotation_count} supplier quotation(s) received.'
                )
        
        print(f"DEBUG: Transaction committed. Updated {updated_count} requisitions.")
        
        return JsonResponse({
            'success': True,
            'message': f'Quotation input completed. {updated_count} requisition(s) updated to PENDING_PO status.',
            'updated_requisitions': updated_count,
            'quotation_count': quotation_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found in session'}, status=401)
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error in complete_quotation_input: {error_detail}")
        return JsonResponse({'error': str(e)}, status=500)


def get_product_specifications(product):
    """Helper function to get product specifications as formatted string"""
    if hasattr(product, 'product_specification_set'):
        specs = product.product_specification_set.all()
        if specs.exists():
            return ", ".join([f"{spec.spec_name}: {spec.spec_value}" for spec in specs])
    return "No specifications"