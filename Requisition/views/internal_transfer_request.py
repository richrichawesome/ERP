# Requisition/views/internal_transfer_request.py

import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json

from Requisition.models import Requisition, RequisitionStatusTimeline, RequisitionItem
from ERP.models import User, Inventory, Inventory_Transaction, Branch

def internal_transfer_request(request):
    """
    List view for internal transfer requests (outgoing from user's branch)
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
    
    # Get internal transfer requests where current user's branch is the sender
    requisitions = Requisition.objects.filter(
        req_type='INTERNAL_TRANSFER',
        sender_branch_id=user_branch_id,  # Only show transfers where user's branch is the sender
    ).select_related(
        'requested_by',
        'branch',  # This is the destination branch
        'sender_branch',
        'sender_user'
    ).prefetch_related('items').order_by('-req_requested_date')
    

    # Handle AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        
        # Apply search filter
        if search_query:
            requisitions = requisitions.filter(
                Q(req_id__icontains=search_query) |
                Q(requested_by__user_fname__icontains=search_query) |
                Q(requested_by__user_lname__icontains=search_query) |
                Q(branch__branch_name__icontains=search_query)  # Search by destination branch
            )
        
        # Apply status filter
        if status_filter:
            requisitions = requisitions.filter(req_main_status=status_filter)
        
        requests_data = []
        for req in requisitions:
            items_count = req.items.count()
            
            requested_by_name = "N/A"
            if req.requested_by:
                requested_by_name = f"{req.requested_by.user_fname} {req.requested_by.user_lname}".strip()
                if not requested_by_name:
                    requested_by_name = req.requested_by.username
            
            destination_branch_name = "N/A"
            if req.branch:
                destination_branch_name = req.branch.branch_name
            
            # Custom status display mapping based on your dropdown options
            status_display = get_status_display(req.req_main_status)
            
            requests_data.append({
                'req_id': req.req_id,
                'req_id_display': f"REQ-{req.req_id}",
                'requested_by_name': requested_by_name,
                'destination_branch_name': destination_branch_name,
                'req_requested_date': req.req_requested_date.strftime('%Y-%m-%d %H:%M:%S'),
                'status': req.req_main_status,
                'status_display': status_display,
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


def get_status_display(status_code):
    """
    Custom status display mapping for internal transfers
    """
    status_mapping = {
        'PENDING_CUSTODIAN': 'Pending Custodian Approval',
        'PENDING_TOP_MGMT': 'Pending Top Management',
        'APPROVED_REQUISITION': 'Approved',
        'SENDER_CONFIRMATION': 'Sender Confirmation',
        'FULFILLED': 'Fulfilled',
        'REJECTED': 'Rejected',
        # Default fallbacks from constants if not in our custom mapping
        'PO_APPROVAL': 'PO Approval',
        'TO_BE_DELIVERED': 'To be Delivered',
        'INSPECTION': 'Inspection',
    }
    
    return status_mapping.get(status_code, status_code)

def internal_transfer_request_detail(request, req_id):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    user = User.objects.get(pk=user_id)
    requisition = get_object_or_404(
        Requisition.objects.select_related('requested_by', 'branch', 'sender_user', 'sender_branch', 'approved_by'),
        req_id=req_id
    )
    
    requisition_items = requisition.items.select_related('product').all()
    timeline_entries = requisition.timeline.select_related('user').order_by('-changed_at')

    rf_file_info = None
    if requisition.rf_file:
        rf_file_info = {
            'name': os.path.basename(requisition.rf_file.name),
            'url': requisition.rf_file.url if hasattr(requisition.rf_file, 'url') else None
        }

    # Determine which buttons to show
    show_buttons = False
    show_property_custodian_buttons = False
    show_top_management_buttons = False
    show_sender_confirmation_buttons = False
    show_fulfillment_buttons = False
    
    # Property Custodian (role_id == 4) can only see buttons when status is PENDING_CUSTODIAN
    if user.role_id == 4 and requisition.req_main_status == 'PENDING_CUSTODIAN':
        show_buttons = True
        show_property_custodian_buttons = True
    
    # Top Management (role_id == 1) can only see buttons when status is PENDING_TOP_MGMT
    elif user.role_id == 1 and requisition.req_main_status == 'PENDING_TOP_MGMT':
        show_buttons = True
        show_top_management_buttons = True
    
    # Sender Confirmation (role_id == 1 and user's branch matches sender_branch)
    elif (user.role_id == 2 and 
          requisition.req_main_status == 'APPROVED_REQUISITION' and
          requisition.sender_branch and 
          user.branch.branch_id == requisition.sender_branch.branch_id):
        show_buttons = True
        show_sender_confirmation_buttons = True

    elif (user.role_id == 2 and 
          requisition.req_main_status == 'SENDER_CONFIRMATION' and requisition.req_substatus == 'IN_TRANSIT' and
          requisition.branch == user.branch):
        show_buttons = True
        show_fulfillment_buttons = True
    
    return render(request, "requisition/internal_transfer_request_details.html", {
        "requisition": requisition,
        "requisition_items": requisition_items,
        "timeline_entries": timeline_entries,
        "user": user,
        "active_page": "internal_transfer_request",
        "show_buttons": show_buttons,
        "show_property_custodian_buttons": show_property_custodian_buttons,
        "show_top_management_buttons": show_top_management_buttons,
        "show_sender_confirmation_buttons": show_sender_confirmation_buttons,
        "show_fulfillment_buttons": show_fulfillment_buttons,
        "rf_file_info": rf_file_info,
    })


@csrf_exempt
def custodian_approve_direct(request, req_id):
    """Property Custodian approves transfer directly to SENDER_CONFIRMATION"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if user is Property Custodian (role_id == 4)
        if user.role_id != 4:
            return JsonResponse({
                'success': False,
                'error': 'Only Property Custodian can perform this action'
            }, status=403)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if requisition is in correct status
        # if requisition.req_main_status != 'PENDING_CUSTODIAN':
        #     return JsonResponse({
        #         'success': False,
        #         'error': f'Requisition is not in PENDING_CUSTODIAN status. Current status: {requisition.req_main_status}'
        #     }, status=400)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'APPROVED_REQUISITION'
        requisition.req_substatus = 'NONE'
        requisition.approved_by = user
        requisition.req_approval_date = timezone.now()
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='APPROVED_REQUISITION',
            sub_status='NONE',
            user=user,
            comment=f'Approved directly by Property Custodian {user.user_fname} {user.user_lname}. Sent to sender branch for confirmation.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Internal transfer approved directly! Sent to sender branch for confirmation.',
            'new_status': 'APPROVED_REQUISITION',
            'old_status': old_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def custodian_send_to_management(request, req_id):
    """Property Custodian approves and sends to Top Management"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if user is Property Custodian (role_id == 4)
        if user.role_id != 4:
            return JsonResponse({
                'success': False,
                'error': 'Only Property Custodian can perform this action'
            }, status=403)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if requisition is in correct status
        # if requisition.req_main_status != 'PENDING_CUSTODIAN':
        #     return JsonResponse({
        #         'success': False,
        #         'error': f'Requisition is not in PENDING_CUSTODIAN status. Current status: {requisition.req_main_status}'
        #     }, status=400)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'PENDING_TOP_MGMT'
        requisition.req_substatus = 'NONE'
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='PENDING_TOP_MGMT',
            sub_status='NONE',
            user=user,
            comment=f'Sent to Top Management by Property Custodian {user.user_fname} {user.user_lname} for approval.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Internal transfer sent to Top Management for approval!',
            'new_status': 'PENDING_TOP_MGMT',
            'old_status': old_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def custodian_reject(request, req_id):
    """Property Custodian rejects the internal transfer request"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if user is Property Custodian (role_id == 4)
        if user.role_id != 4:
            return JsonResponse({
                'success': False,
                'error': 'Only Property Custodian can perform this action'
            }, status=403)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if requisition is in correct status
        # if requisition.req_main_status != 'PENDING_CUSTODIAN':
        #     return JsonResponse({
        #         'success': False,
        #         'error': f'Requisition is not in PENDING_CUSTODIAN status. Current status: {requisition.req_main_status}'
        #     }, status=400)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        # Get rejection reason from request body
        data = json.loads(request.body)
        rejection_reason = data.get('reason', '').strip()
        
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'error': 'Rejection reason is required'
            }, status=400)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'REJECTED'  # Changed to FULFILLED for rejected status
        requisition.req_substatus = 'NONE'
        requisition.req_rejection_reason = rejection_reason
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='REJECTED',
            sub_status='NONE',
            user=user,
            comment=f'Rejected by Property Custodian {user.user_fname} {user.user_lname}. Reason: {rejection_reason}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Internal transfer rejected successfully!',
            'new_status': 'REJECTED',
            'old_status': old_status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def management_approve(request, req_id):
    """Top Management approves the internal transfer request"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if user is Top Management (role_id == 1)
        if user.role_id != 1:
            return JsonResponse({
                'success': False,
                'error': 'Only Top Management can perform this action'
            }, status=403)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if requisition is in correct status
        if requisition.req_main_status != 'PENDING_TOP_MGMT':
            return JsonResponse({
                'success': False,
                'error': f'Requisition is not in PENDING_TOP_MGMT status. Current status: {requisition.req_main_status}'
            }, status=400)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'APPROVED_REQUISITION'
        requisition.req_substatus = 'NONE'
        requisition.approved_by = user
        requisition.req_approval_date = timezone.now()
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='APPROVED_REQUISITION',
            sub_status='NONE',
            user=user,
            comment=f'Approved by Top Management {user.user_fname} {user.user_lname}. Sent to sender branch for confirmation.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Internal transfer approved by Top Management! Sent to sender branch for confirmation.',
            'new_status': 'APPROVED_REQUISITION',
            'old_status': old_status
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def management_reject(request, req_id):
    """Top Management rejects the internal transfer request"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if user is Top Management (role_id == 1)
        if user.role_id != 1:
            return JsonResponse({
                'success': False,
                'error': 'Only Top Management can perform this action'
            }, status=403)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if requisition is in correct status
        if requisition.req_main_status != 'PENDING_TOP_MGMT':
            return JsonResponse({
                'success': False,
                'error': f'Requisition is not in PENDING_TOP_MGMT status. Current status: {requisition.req_main_status}'
            }, status=400)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        # Get rejection reason from request body
        data = json.loads(request.body)
        rejection_reason = data.get('reason', '').strip()
        
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'error': 'Rejection reason is required'
            }, status=400)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'REJECTED'  # Changed to FULFILLED for rejected status
        requisition.req_substatus = 'NONE'
        requisition.req_rejection_reason = rejection_reason
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='REJECTED',
            sub_status='NONE',
            user=user,
            comment=f'Rejected by Top Management {user.user_fname} {user.user_lname}. Reason: {rejection_reason}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Internal transfer rejected by Top Management!',
            'new_status': 'REJECTED',
            'old_status': old_status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def sender_accept(request, req_id):
    """Sender branch accepts the transfer - marks as IN_TRANSIT"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if user is authorized (Top Management at sender branch)
        if user.role_id != 2:
            return JsonResponse({
                'success': False,
                'error': 'Only Top Management can perform this action'
            }, status=403)
        
        # Check if user's branch matches sender_branch
        if not requisition.sender_branch or user.branch.branch_id != requisition.sender_branch.branch_id:
            return JsonResponse({
                'success': False,
                'error': 'You are not authorized to accept this transfer. You must be from the sender branch.'
            }, status=403)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        old_status = requisition.req_main_status
        old_substatus = requisition.req_substatus
        
        # Update to SENDER_CONFIRMATION status with IN_TRANSIT substatus
        requisition.req_main_status = 'SENDER_CONFIRMATION'
        requisition.req_substatus = 'IN_TRANSIT'
        requisition.sender_user = user
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='SENDER_CONFIRMATION',
            sub_status='IN_TRANSIT',
            user=user,
            comment=f'Transfer accepted by {user.user_fname} {user.user_lname} from {requisition.sender_branch.branch_name}. Items are in transit.'
        )
        
        # Process inventory transfer
        try:
            process_inventory_transfer(requisition, user)
        except Exception as e:
            # Log the error but don't fail the request
            print(f"Error processing inventory transfer: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': 'Transfer accepted successfully! Items are now in transit.',
            'new_status': 'SENDER_CONFIRMATION',
            'new_substatus': 'IN_TRANSIT',
            'old_status': old_status,
            'old_substatus': old_substatus
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def sender_reject(request, req_id):
    """Sender branch rejects the transfer"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if user is authorized (Top Management at sender branch)
        if user.role_id != 1:
            return JsonResponse({
                'success': False,
                'error': 'Only Top Management can perform this action'
            }, status=403)
        
        # Check if user's branch matches sender_branch
        if not requisition.sender_branch or user.branch.branch_id != requisition.sender_branch.branch_id:
            return JsonResponse({
                'success': False,
                'error': 'You are not authorized to reject this transfer. You must be from the sender branch.'
            }, status=403)
        
        # Check if requisition is in correct status
        if requisition.req_main_status != 'SENDER_CONFIRMATION':
            return JsonResponse({
                'success': False,
                'error': f'Requisition is not in SENDER_CONFIRMATION status. Current status: {requisition.req_main_status}'
            }, status=400)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        # Get rejection reason from request body
        data = json.loads(request.body)
        rejection_reason = data.get('reason', '').strip()
        
        if not rejection_reason:
            return JsonResponse({
                'success': False,
                'error': 'Rejection reason is required'
            }, status=400)
        
        old_status = requisition.req_main_status
        requisition.req_main_status = 'REJECTED'  
        requisition.req_substatus = 'NONE'
        requisition.req_rejection_reason = f"Rejected by sender branch: {rejection_reason}"
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='REJECTED',
            sub_status='NONE',
            user=user,
            comment=f'Transfer rejected by {user.user_fname} {user.user_lname} from {requisition.sender_branch.branch_name}. Reason: {rejection_reason}'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Transfer rejected successfully!',
            'new_status': 'REJECTED',
            'old_status': old_status
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
def receive_items(request, req_id):
    """Destination branch receives the items - completes the transfer"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request method'
        }, status=405)
    
    try:
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not authenticated'
            }, status=401)
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        try:
            requisition = Requisition.objects.get(req_id=req_id)
        except Requisition.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Requisition not found'
            }, status=404)
        
        # Check if user is from destination branch (role_id == 2 for Purchase Management)
        if user.role_id != 2:
            return JsonResponse({
                'success': False,
                'error': 'Only Purchase Management can receive items'
            }, status=403)
        
        # Check if user's branch matches destination branch
        if user.branch.branch_id != requisition.branch.branch_id:
            return JsonResponse({
                'success': False,
                'error': 'You are not authorized to receive these items. You must be from the destination branch.'
            }, status=403)
        
        # Check if requisition is in correct status
        if requisition.req_main_status != 'SENDER_CONFIRMATION' or requisition.req_substatus != 'IN_TRANSIT':
            return JsonResponse({
                'success': False,
                'error': f'Items are not in transit. Current status: {requisition.req_main_status} - {requisition.req_substatus}'
            }, status=400)
        
        # Check if requisition is Internal Transfer type
        if requisition.req_type != 'INTERNAL_TRANSFER':
            return JsonResponse({
                'success': False,
                'error': 'This action is only for Internal Transfer requisitions'
            }, status=400)
        
        old_status = requisition.req_main_status
        old_substatus = requisition.req_substatus
        
        # Update to FULFILLED status with RECEIVED substatus
        requisition.req_main_status = 'FULFILLED'
        requisition.req_substatus = 'NONE'
        requisition.save()
        
        # Create status timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='FULFILLED',
            sub_status='NONE',
            user=user,
            comment=f'Items received by {user.user_fname} {user.user_lname} at {requisition.branch.branch_name}. Transfer completed.'
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Items received successfully! Transfer completed.',
            'new_substatus': 'NONE',
            'old_status': old_status,
            'old_substatus': old_substatus
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def process_inventory_transfer(requisition, user):
    """Process inventory transfer when sender accepts the transfer"""
    try:
        # Get all items from the requisition
        requisition_items = requisition.items.select_related('product').all()
        
        for item in requisition_items:
            # Get product current cost
            product_cost = item.product.prod_current_cost or 0
            
            # 1. Reduce inventory at sender branch
            sender_inventory, created = Inventory.objects.get_or_create(
                product=item.product,
                branch=requisition.sender_branch,
                defaults={
                    'quantity_on_hand': 0,
                    'last_updated_at': timezone.now().date(),
                    'user': user
                }
            )
            
            # Check if sender has enough stock
            if sender_inventory.quantity_on_hand < item.quantity:
                raise Exception(f"Insufficient stock at sender branch. Product: {item.product.prod_name}, Available: {sender_inventory.quantity_on_hand}, Requested: {item.quantity}")
            
            # Reduce sender inventory
            sender_inventory.quantity_on_hand -= item.quantity
            sender_inventory.last_updated_at = timezone.now().date()
            sender_inventory.user = user
            sender_inventory.save()
            
            # Create transfer_out transaction for sender
            Inventory_Transaction.objects.create(
                trans_type='transfer_out',
                quantity=item.quantity,
                unit_cost=product_cost,
                inventory=sender_inventory,
                user=user,
                created_at=timezone.now()
            )
            
            # 2. Increase inventory at destination branch
            dest_inventory, created = Inventory.objects.get_or_create(
                product=item.product,
                branch=requisition.branch,
                defaults={
                    'quantity_on_hand': 0,
                    'last_updated_at': timezone.now().date(),
                    'user': user
                }
            )
            
            # Increase destination inventory
            dest_inventory.quantity_on_hand += item.quantity
            dest_inventory.last_updated_at = timezone.now().date()
            dest_inventory.user = user
            dest_inventory.save()
            
            # Create transfer_in transaction for destination
            Inventory_Transaction.objects.create(
                trans_type='transfer_in',
                quantity=item.quantity,
                unit_cost=product_cost,
                inventory=dest_inventory,
                user=user,
                created_at=timezone.now()
            )
            
        return True
        
    except Exception as e:
        # Revert changes if any error occurs
        print(f"Error in inventory transfer: {str(e)}")
        raise e