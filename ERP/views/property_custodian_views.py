from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.paginator import Paginator
import json

# Import models from the correct locations
from Requisition.models import Requisition, RequisitionStatusTimeline
from ERP.models import User

def property_custodian_dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('login')
    
    section = request.GET.get('section', 'requisition')
    
    # Get filter parameters
    req_type = request.GET.get('type', 'all')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    # Set default status based on role_id
    if not status:
        if user.role.role_id == 2:
            status = 'PENDING_CUSTODIAN'
        elif user.role.role_id == 1:
            status = 'PENDING_TOP_MGMT'
        elif user.role.role_id == 3:
            status = 'APPROVED_REQUISITION'
        elif user.role.role_id == 4:
            status = 'TO_BE_DELIVERED'
        else:
            status = 'all'
    
    # Start with all requisitions
    requisitions = Requisition.objects.select_related(
        'requested_by', 'branch'
    ).all().order_by('-req_requested_date')
    
    # If user has role_id 2, filter by user's branch
    if user.role.role_id == 2:
        requisitions = requisitions.filter(branch=user.branch)
    
    # Apply filters
    if req_type != 'all':
        requisitions = requisitions.filter(req_type=req_type)
    
    if status != 'all':
        requisitions = requisitions.filter(req_main_status=status)
    
    if search:
        requisitions = requisitions.filter(
            Q(req_id__icontains=search) |
            Q(requested_by__user_fname__icontains=search) |
            Q(requested_by__user_lname__icontains=search)
        )
    
    # For AJAX requests, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        requisitions_data = []
        for req in requisitions:
            requisitions_data.append({
                'req_id': f'REQ-{req.req_id}',  # Formatted for display
                'req_id_raw': req.req_id,       # Raw ID for URL
                'type': req.get_req_type_display(),
                'type_value': req.req_type,
                'date_requested': req.req_requested_date.strftime('%b %d, %Y'),
                'requested_by': f'{req.requested_by.user_fname} {req.requested_by.user_lname}',
                'branch': req.branch.branch_name,
                'branch_id': req.branch.branch_id,
                'status': req.req_main_status,
                'status_display': req.get_req_main_status_display(),
                # 'detail_url': f'/requisition_detail/{req.req_id}/'  # raw ID here
            })
        
        return JsonResponse({
            'success': True,
            'requisitions': requisitions_data,
            'user_role_id': user.role.role_id,
            'user_branch_id': user.branch.branch_id if user.role.role_id == 2 else None
        })
    
    return render(request, "main/requisition.html", {
        "section": section,
        "requisitions": requisitions,
        "user": user,
        "active_page": "requisition",
        "default_status": status
    })

# @csrf_exempt
# def approve_requisition(request, req_id):
#     """
#     Approve requisition - changes status to APPROVED_REQUISITION
#     """
#     if request.method != 'POST':
#         return JsonResponse({
#             'success': False,
#             'error': 'Invalid request method'
#         }, status=405)
    
#     try:
#         # Get user from session
#         user_id = request.session.get('user_id')
#         if not user_id:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'User not authenticated'
#             }, status=401)
        
#         try:
#             user = User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'User not found'
#             }, status=404)
        
#         # Get the requisition
#         try:
#             requisition = Requisition.objects.get(req_id=req_id)
#         except Requisition.DoesNotExist:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Requisition not found'
#             }, status=404)
        
#         # Update requisition status
#         old_status = requisition.req_main_status
#         requisition.req_main_status = 'APPROVED_REQUISITION'
#         requisition.req_substatus = 'NONE'
#         requisition.approved_by = user
#         requisition.req_approval_date = timezone.now()
#         requisition.save()
        
#         # Create timeline entry
#         RequisitionStatusTimeline.objects.create(
#             requisition=requisition,
#             main_status='APPROVED_REQUISITION',
#             sub_status='NONE',
#             user=user,
#             comment=f'Approved by {user.user_fname} {user.user_lname}'
#         )
        
#         return JsonResponse({
#             'success': True,
#             'message': 'Requisition approved successfully!',
#             'new_status': 'APPROVED_REQUISITION',
#             'old_status': old_status
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)


# @csrf_exempt
# def approve_to_management(request, req_id):
#     """
#     Approve and send to management - changes status to PENDING_TOP_MGMT
#     """
#     if request.method != 'POST':
#         return JsonResponse({
#             'success': False,
#             'error': 'Invalid request method'
#         }, status=405)
    
#     try:
#         # Get user from session
#         user_id = request.session.get('user_id')
#         if not user_id:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'User not authenticated'
#             }, status=401)
        
#         try:
#             user = User.objects.get(pk=user_id)
#         except User.DoesNotExist:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'User not found'
#             }, status=404)
        
#         # Get the requisition
#         try:
#             requisition = Requisition.objects.get(req_id=req_id)
#         except Requisition.DoesNotExist:
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Requisition not found'
#             }, status=404)
        
#         # Update requisition status
#         old_status = requisition.req_main_status
#         requisition.req_main_status = 'PENDING_TOP_MGMT'
#         requisition.req_substatus = 'NONE'
#         requisition.save()
        
#         # Create timeline entry
#         RequisitionStatusTimeline.objects.create(
#             requisition=requisition,
#             main_status='PENDING_TOP_MGMT',
#             sub_status='NONE',
#             user=user,
#             comment=f'Forwarded to Top Management by {user.user_fname} {user.user_lname}'
#         )
        
#         return JsonResponse({
#             'success': True,
#             'message': 'Requisition approved and sent to management successfully!',
#             'new_status': 'PENDING_TOP_MGMT',
#             'old_status': old_status
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=500)