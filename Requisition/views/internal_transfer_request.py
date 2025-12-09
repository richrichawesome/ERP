# Requisition/views/internal_transfer_request.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from Requisition.models import Requisition, RequisitionStatusTimeline, RequisitionItem
from ERP.models import User
import json


def internal_transfer_request_detail(request, req_id):
    """
    Display the details of an internal transfer request with role-based action buttons
    """
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.select_related('branch', 'role').get(pk=user_id)
        user_branch_id = user.branch.branch_id
        user_role_id = user.role.role_id
    except User.DoesNotExist:
        request.session.flush()
        return redirect('login')
    
    requisition = get_object_or_404(
        Requisition, 
        req_id=req_id, 
        req_type='INTERNAL_TRANSFER'
    )
    
    # Get timeline statuses ordered by date
    timeline = requisition.timeline.select_related('user').order_by('changed_at')
    
    # Get specific status entries for progress bar
    custodian_status = timeline.filter(
        main_status='PENDING_CUSTODIAN'
    ).first()
    
    management_status = timeline.filter(
        main_status='PENDING_TOP_MGMT'
    ).first()
    
    approved_requisition_status = timeline.filter(
        main_status='APPROVED_REQUISITION'
    ).first()
    
    sender_confirmation_status = timeline.filter(
        main_status='SENDER_CONFIRMATION'
    ).first()
    
    fulfilled_status = timeline.filter(
        main_status='FULFILLED'
    ).first()
    
    # Check if management was skipped (direct approval)
    skipped_management = False
    if approved_requisition_status and not management_status:
        skipped_management = True
    
    # Determine current step for progress bar
    current_step = requisition.req_main_status
    
    # Determine which action buttons to show based on role and status
    show_custodian_buttons = False
    show_management_buttons = False
    show_sender_accept_buttons = False
    show_receive_button = False
    
    # 1. Property Custodian Review (role_id = 4)
    if (current_step == 'PENDING_CUSTODIAN' and 
        user_role_id == 4 and
        not requisition.req_rejection_reason):
        show_custodian_buttons = True
    
    # 2. Top Management Approval (role_id = 1)
    if (current_step == 'PENDING_TOP_MGMT' and 
        user_role_id == 1 and
        not requisition.req_rejection_reason):
        show_management_buttons = True
    
    # 3. Sender Confirmation (role_id = 2, sender branch)
    if (current_step == 'APPROVED_REQUISITION' and 
        user_role_id == 2 and
        requisition.sender_branch and
        user_branch_id == requisition.sender_branch.branch_id and
        not requisition.req_rejection_reason):
        show_sender_accept_buttons = True
    
    # 4. Fulfillment/Receive (role_id = 2, receiving branch, in-transit)
    if (current_step == 'SENDER_CONFIRMATION' and 
        requisition.req_substatus == 'IN_TRANSIT' and
        user_role_id == 2 and
        user_branch_id == requisition.branch.branch_id and
        not requisition.req_rejection_reason):
        show_receive_button = True
    
    context = {
        'requisition': requisition,
        'custodian_status': custodian_status,
        'management_status': management_status,
        'confirmation_status': sender_confirmation_status,
        'fulfilled_status': fulfilled_status,
        'skipped_management': skipped_management,
        'current_step': current_step,
        'show_custodian_buttons': show_custodian_buttons,
        'show_management_buttons': show_management_buttons,
        'show_sender_accept_buttons': show_sender_accept_buttons,
        'show_receive_button': show_receive_button,
        'user': user,
        'user_id': user_id,
        'user_branch_id': user_branch_id,
        'user_role_id': user_role_id,
    }
    
    return render(request, 'requisition/internal_transfer_request_details.html', context)


@require_http_methods(["POST"])
def custodian_approve_direct(request, req_id):
    """
    Property Custodian directly approves the requisition
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        # Verify user is property custodian (role_id = 4)
        if user.role.role_id != 4:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        if requisition.req_main_status != 'PENDING_CUSTODIAN':
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Update requisition status
        requisition.req_main_status = 'APPROVED_REQUISITION'
        requisition.req_substatus = 'NONE'
        requisition.approved_by = user
        requisition.req_approval_date = timezone.now()
        requisition.save()
        
        # Add timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='APPROVED_REQUISITION',
            sub_status='NONE',
            user=user,
            comment='Directly approved by Property Custodian'
        )
        
        return JsonResponse({'success': True, 'message': 'Requisition approved successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def custodian_send_to_management(request, req_id):
    """
    Property Custodian sends requisition to top management for approval
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        if user.role.role_id != 4:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        if requisition.req_main_status != 'PENDING_CUSTODIAN':
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Update requisition status
        requisition.req_main_status = 'PENDING_TOP_MGMT'
        requisition.req_substatus = 'NONE'
        requisition.save()
        
        # Add timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='PENDING_TOP_MGMT',
            sub_status='NONE',
            user=user,
            comment='Sent to Top Management for approval'
        )
        
        return JsonResponse({'success': True, 'message': 'Sent to Top Management for approval'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def custodian_reject(request, req_id):
    """
    Property Custodian rejects the requisition
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        if user.role.role_id != 4:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        if requisition.req_main_status != 'PENDING_CUSTODIAN':
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Get rejection reason
        try:
            data = json.loads(request.body)
            rejection_reason = data.get('reason', 'Rejected by Property Custodian')
        except:
            rejection_reason = 'Rejected by Property Custodian'
        
        # Update requisition
        requisition.req_rejection_reason = rejection_reason
        requisition.save()
        
        return JsonResponse({'success': True, 'message': 'Requisition rejected'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def management_approve(request, req_id):
    """
    Top Management approves the requisition
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        if user.role.role_id != 1:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        if requisition.req_main_status != 'PENDING_TOP_MGMT':
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Update requisition status
        requisition.req_main_status = 'APPROVED_REQUISITION'
        requisition.req_substatus = 'NONE'
        requisition.approved_by = user
        requisition.req_approval_date = timezone.now()
        requisition.save()
        
        # Add timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='APPROVED_REQUISITION',
            sub_status='NONE',
            user=user,
            comment='Approved by Top Management'
        )
        
        return JsonResponse({'success': True, 'message': 'Requisition approved successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def management_reject(request, req_id):
    """
    Top Management rejects the requisition
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        if user.role.role_id != 1:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        if requisition.req_main_status != 'PENDING_TOP_MGMT':
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Get rejection reason
        try:
            data = json.loads(request.body)
            rejection_reason = data.get('reason', 'Rejected by Top Management')
        except:
            rejection_reason = 'Rejected by Top Management'
        
        # Update requisition
        requisition.req_rejection_reason = rejection_reason
        requisition.save()
        
        return JsonResponse({'success': True, 'message': 'Requisition rejected'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def sender_accept(request, req_id):
    """
    Sender Branch Manager accepts and sets items to in-transit
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        # Verify user is branch manager (role_id = 2) from sender branch
        if user.role.role_id != 2:
            return JsonResponse({'success': False, 'error': 'Unauthorized - Not a Branch Manager'}, status=403)
        
        if not requisition.sender_branch or user.branch.branch_id != requisition.sender_branch.branch_id:
            return JsonResponse({'success': False, 'error': 'Unauthorized - Not from sender branch'}, status=403)
        
        if requisition.req_main_status != 'APPROVED_REQUISITION':
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Update requisition status to in-transit
        requisition.req_main_status = 'SENDER_CONFIRMATION'
        requisition.req_substatus = 'IN_TRANSIT'
        requisition.save()
        
        # Add timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='SENDER_CONFIRMATION',
            sub_status='IN_TRANSIT',
            user=user,
            comment='Accepted by sender branch - Items in transit'
        )
        
        return JsonResponse({'success': True, 'message': 'Transfer accepted - Items marked as in transit'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def sender_reject(request, req_id):
    """
    Sender Branch Manager rejects the requisition
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        if user.role.role_id != 2:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        if not requisition.sender_branch or user.branch.branch_id != requisition.sender_branch.branch_id:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
        if requisition.req_main_status != 'APPROVED_REQUISITION':
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        
        # Get rejection reason
        try:
            data = json.loads(request.body)
            rejection_reason = data.get('reason', 'Rejected by sender branch')
        except:
            rejection_reason = 'Rejected by sender branch'
        
        # Update requisition
        requisition.req_rejection_reason = rejection_reason
        requisition.save()
        
        return JsonResponse({'success': True, 'message': 'Transfer request rejected'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(["POST"])
def receive_items(request, req_id):
    """
    Receiving Branch Manager receives the items
    """
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)
        
        user = get_object_or_404(User, pk=user_id)
        
        requisition = get_object_or_404(Requisition, req_id=req_id, req_type='INTERNAL_TRANSFER')
        
        # Verify user is branch manager (role_id = 2) from receiving branch
        if user.role.role_id != 2:
            return JsonResponse({'success': False, 'error': 'Unauthorized - Not a Branch Manager'}, status=403)
        
        if user.branch.branch_id != requisition.branch.branch_id:
            return JsonResponse({'success': False, 'error': 'Unauthorized - Not from receiving branch'}, status=403)
        
        if requisition.req_main_status != 'SENDER_CONFIRMATION' or requisition.req_substatus != 'IN_TRANSIT':
            return JsonResponse({'success': False, 'error': 'Invalid status - Items not in transit'}, status=400)
        
        # Update requisition status to fulfilled
        requisition.req_main_status = 'FULFILLED'
        requisition.req_substatus = 'NONE'
        requisition.save()
        
        # Add timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='FULFILLED',
            sub_status='NONE',
            user=user,
            comment='Items received and transfer fulfilled'
        )
        
        return JsonResponse({'success': True, 'message': 'Items received successfully - Transfer fulfilled'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def internal_transfer_request(request):
    """
    List view for internal transfer requests
    """
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.select_related('branch', 'role').get(pk=user_id)
        user_branch_id = user.branch.branch_id
        role_id = user.role.role_id
        role_name = user.role.role_name
        branch_name = user.branch.branch_name
    except User.DoesNotExist:
        request.session.flush()
        return redirect('login')
    
    # Get internal transfer requests
    requisitions = Requisition.objects.filter(
        req_type='INTERNAL_TRANSFER',
        sender_branch_id=user_branch_id,
    ).exclude(
        branch_id=user_branch_id
    ).select_related(
        'requested_by',
        'branch',
        'sender_branch',
        'sender_user'
    ).prefetch_related('items').order_by('-req_requested_date')
    
    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_query = request.GET.get('search', '')
        
        if search_query:
            requisitions = requisitions.filter(
                Q(req_id__icontains=search_query) |
                Q(requested_by__user_fname__icontains=search_query) |
                Q(requested_by__user_lname__icontains=search_query) |
                Q(branch__branch_name__icontains=search_query)
            )
        
        requests_data = []
        for req in requisitions:
            items_count = req.items.count()
            
            requested_by_name = "N/A"
            if req.requested_by:
                requested_by_name = f"{req.requested_by.user_fname} {req.requested_by.user_lname}".strip()
                if not requested_by_name:
                    requested_by_name = req.requested_by.username
            
            requests_data.append({
                'req_id': req.req_id,
                'req_id_display': f"REQ-{req.req_id}",
                'requested_by_name': requested_by_name,
                'destination_branch_name': req.branch.branch_name if req.branch else 'N/A',
                'req_requested_date': req.req_requested_date.strftime('%Y-%m-%d %H:%M:%S'),
                'status': req.req_main_status,
                'substatus': req.req_substatus,
                'items_count': items_count,
            })
        
        return JsonResponse({
            'success': True,
            'requests': requests_data,
        })
    
    context = {
        'user': user,
        'user_id': user_id,
        'user_branch_id': user_branch_id,
        'user_branch_name': branch_name,
        'requisitions': requisitions,
        'active_page': 'internal_transfer_request',
    }
    
    return render(request, 'requisition/internal_transfer_request.html', context)