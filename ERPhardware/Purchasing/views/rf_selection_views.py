# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from Requisition.models import Requisition
from ERP.models import User

@login_required
def rf_selection(request):
    """View for RF Selection page - shows approved requisitions ready for PO creation"""
    # Get the logged-in user from session
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    
    # Get approved requisitions with completed quotations
    approved_requisitions = Requisition.objects.filter(
        req_main_status="APPROVED_REQUISITION",
        req_substatus="QUOTATIONS_COMPLETED"
    ).select_related('requested_by').order_by('-req_requested_date')
    
    context = {
        'approved_requisitions': approved_requisitions,
        'user': user,
    }
    
    return render(request, 'purchasing/rf_selection.html', context)

@login_required
def create_po_from_requisitions(request):
    """Handle PO creation from selected requisitions"""
    if request.method == 'POST':
        user_id = request.session.get("user_id")
        user = User.objects.get(pk=user_id)
        
        requisition_ids = request.POST.getlist('requisition_ids')
        
        if not requisition_ids:
            messages.error(request, 'Please select at least one requisition to create a PO.')
            return redirect('rf_selection')
        
        try:
            # Validate that all requisitions exist and are in correct status
            requisitions = Requisition.objects.filter(
                req_id__in=requisition_ids,
                req_main_status="APPROVED_REQUISITION",
                req_substatus="QUOTATIONS_COMPLETED"
            )
            
            if len(requisitions) != len(requisition_ids):
                messages.error(request, 'Some requisitions are not available or not in correct status.')
                return redirect('rf_selection')
            
            # Create Purchase Orders for each requisition
            created_pos = []
            for requisition in requisitions:
                # Your PO creation logic here
                # Example:
                # po = PurchaseOrder.objects.create(
                #     requisition=requisition,
                #     created_by=user,
                #     status='DRAFT'
                # )
                # created_pos.append(po)
                
                # Update requisition status
                requisition.req_substatus = "PO_IN_PROGRESS"
                requisition.save()
                
                # For demo, just track the IDs
                created_pos.append(requisition.req_id)
            
            messages.success(request, f'Successfully created {len(created_pos)} purchase order(s)!')
            
        except Exception as e:
            messages.error(request, f'Error creating purchase orders: {str(e)}')
        
        return redirect('rf_selection')
    
    return redirect('rf_selection')