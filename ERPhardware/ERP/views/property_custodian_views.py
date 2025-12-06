from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
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
    status = request.GET.get('status', '')  # Don't set default here yet
    search = request.GET.get('search', '')
    
    # Set default status based on SPECIFIC Property Custodian user
    if not status:  # Only set default if no status is specified in URL
        # HARDCODED: Replace 'propertycustodian' with the ACTUAL username of your Property Custodian
        property_custodian_usernames = [
            'propertycustodian',  # Add the actual username here
            'property_custodian',
            'prop_custodian'
            # Add any other usernames that should be treated as Property Custodian
        ]
        
        # Check if current user is one of the Property Custodian users
        current_username = getattr(user, 'username', '').lower()
        if current_username in property_custodian_usernames:
            status = 'TO_BE_DELIVERED'
        else:
            # All other users (Admin, Top Management, Purchasing Staff) see All Status
            status = 'all'
    
    # Start with all requisitions
    requisitions = Requisition.objects.select_related(
        'requested_by', 'branch'
    ).all().order_by('-req_requested_date')
    
    
    return render(request, "main/requisition.html", {
        "section": section,
        "requisitions": requisitions,
        "user": user,
        "active_page": "req_main",
    })

