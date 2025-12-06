from django.db.models import Q
from django.shortcuts import render, redirect
from ERP.models import User
from Property_Custodian.models import Purchase_Order, Discrepancy
from Requisition.models import Requisition

def delivery_management(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    user = User.objects.get(pk=user_id)
    
    # Get only POs that have items in GOOD condition
    po_query = Purchase_Order.objects.filter(
        discrepancy__disc_condition='good'
    ).distinct()
    
    # Get distinct POs and prefetch related data
    # FIXED: Removed 'requisition' from select_related as it doesn't exist
    purchase_orders = po_query.select_related(
        'supplier',
        'user',
        'branch',
        'rfq_supplier',
        'supplier_quotation'
    ).prefetch_related(
        'discrepancy_set__inspected_by',
        'discrepancy_set__product',
        'requisitions',  # FIXED: Use prefetch_related for the reverse relation
        'requisitions__requested_by'  # Also prefetch the requested_by user
    ).order_by('-po_created_at')
    
    # Build PO data list with inspection details (only good items)
    purchase_orders_data = []
    for po in purchase_orders:
        # Get ONLY good condition discrepancies for this PO
        good_discrepancies = po.discrepancy_set.filter(disc_condition='good')
        
        # Get the latest good discrepancy to show inspection details
        latest_good_disc = good_discrepancies.order_by('-inspection_date').first()
        
        if latest_good_disc:
            # Get the first requisition associated with this PO for display purposes
            # In your case, you might want to show all requisitions or pick one
            first_requisition = po.requisitions.first() if po.requisitions.exists() else None
            
            po_data = {
                'po': po,
                'requisition': first_requisition,  # Add the requisition
                'inspected_by': latest_good_disc.inspected_by,
                'inspection_date': latest_good_disc.inspection_date,
                'condition': 'good',
                'good_items_count': good_discrepancies.count(),  # Count of good items
                'requisitions_count': po.requisitions.count()  # How many requisitions linked to this PO
            }
            purchase_orders_data.append(po_data)
    
    context = {
        'user': user,
        'section': 'inventory',
        'active_page': 'delivery_management',
        'purchase_orders_data': purchase_orders_data,
    }
    
    return render(request, 'main/delivery_management.html', context)