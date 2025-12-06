# quote_creation_views.py
from django.shortcuts import render, redirect
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

# Import models from the correct locations
from Requisition.models import Requisition, RequisitionStatusTimeline
from ERP.models import User
from Purchasing.models import RFQ, RFQ_Item, Supplier



def quote_creation(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(pk=user_id)
    if not user_id:
        return redirect('login')
    
    section = request.GET.get('section', 'input_quotation')
    
    # Get filter parameters
    status = request.GET.get('status', 'APPROVED_REQUISITION')
    search = request.GET.get('search', '')
    
    # Start with only INV_REPLENISHMENT requisitions
    requisitions = Requisition.objects.select_related(
        'requested_by', 'branch'
    ).filter(
        req_type='INV_REPLENISHMENT'  # Only show inventory replenishment requisitions
    ).order_by('-req_requested_date')
    
    # Apply filters
    if status != 'all':
        # SPECIAL CASE: For APPROVED_REQUISITION status, only show those with RFQ_CREATED substatus
        if status == 'APPROVED_REQUISITION':
            requisitions = requisitions.filter(
                req_main_status=status,
                req_substatus='RFQ_CREATED'  # Only show APPROVED_REQUISITION with RFQ_CREATED substatus
            )
        else:
            # For all other statuses, just filter by main status
            requisitions = requisitions.filter(req_main_status=status)
    
    if search:
        requisitions = requisitions.filter(
            Q(req_id=search) |
            Q(rfq_id=search) 
        )
    
    # Group requisitions by RFQ for display
    rfq_data = []
    
    # Get unique RFQs from filtered requisitions
    rfqs_with_requisitions = {}
    for requisition in requisitions:
        if requisition.rfq:
            rfq_id = requisition.rfq.rfq_id
            if rfq_id not in rfqs_with_requisitions:
                rfqs_with_requisitions[rfq_id] = {
                    'rfq': requisition.rfq,
                    'requisitions': []
                }
            rfqs_with_requisitions[rfq_id]['requisitions'].append(requisition)
    
    # Prepare data for each RFQ
    for rfq_id, data in rfqs_with_requisitions.items():
        rfq = data['rfq']
        requisitions_for_rfq = data['requisitions']
        
        # Get requisition IDs as comma-separated string
        req_ids = [f"REQ-{req.req_id}" for req in requisitions_for_rfq]
        
        # Get the first requisition for type and status (they should all be the same)
        if requisitions_for_rfq:
            sample_req = requisitions_for_rfq[0]
            rfq_data.append({
                'rfq_id': rfq.rfq_id,
                'rfq_display': f"RFQ-{rfq.rfq_id}",
                'requisition_ids': ', '.join(req_ids),
                'req_type': sample_req.get_req_type_display(),
                'main_status': sample_req.req_main_status,
                'sub_status': sample_req.req_substatus,
                'status_display': f"{sample_req.get_req_main_status_display()} - {sample_req.get_req_substatus_display()}",
                'created_at': rfq.rfq_created_at.strftime('%B %d, %Y'),
                'created_by': f"{rfq.rfq_created_by.user_fname} {rfq.rfq_created_by.user_lname}"
            })



        # Get all active suppliers
    suppliers = Supplier.objects.filter(sup_is_active=True).order_by('sup_name')
    
    
    
    return render(request, "purchasing/quote_creation.html", {
        "section": section,
        "rfq_data": rfq_data,  # Changed from requisitions to rfq_data
        "user": user,
        "active_page": "input_quotation" , # Changed from "requisition"
        "suppliers": suppliers,
    })