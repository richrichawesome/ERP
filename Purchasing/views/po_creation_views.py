
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

# Import models from the correct locations
from Requisition.models import Requisition, RequisitionStatusTimeline
from ERP.models import User




def po_creation(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(pk=user_id)
    if not user_id:
        return redirect('login')
    
    section = request.GET.get('section', 'requisition')
    
    # Get filter parameters
    # req_type = request.GET.get('type', 'all')
    status = request.GET.get('status', 'APPROVED_REQUISITION')
    search = request.GET.get('search', '')
    
    

    # Start with only INV_REPLENISHMENT requisitions
    requisitions = Requisition.objects.select_related(
        'requested_by', 'branch'
    ).filter(
        req_type='INV_REPLENISHMENT'  # Only show inventory replenishment requisitions
    ).order_by('-req_requested_date')

    
    
    
    if status != 'all':
        # SPECIAL CASE: For APPROVED_REQUISITION status, only show those with NONE substatus
        if status == 'APPROVED_REQUISITION':
            requisitions = requisitions.filter(
                req_main_status=status,
                req_substatus='PENDING_PO'  # Only show APPROVED_REQUISITION with NONE substatus
            )
        else:
            # For all other statuses, just filter by main status
            requisitions = requisitions.filter(req_main_status=status)
    
    if search:
        requisitions = requisitions.filter(
            Q(req_id=search) 
            # Q(requested_by__user_fname__icontains=search) |
            # Q(requested_by__user_lname__icontains=search)
        )
    
    return render(request, "purchasing/po_creation.html", {
        "section": section,
        "requisitions": requisitions,
        "user": user,
        "active_page": "po"
    })
