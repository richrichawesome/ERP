# Requisition\views\requisition_management.py

import json
import os
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from datetime import datetime

from ERP.models import Inventory, Product, User, Product_Specification
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from Requisition.utils import generate_requisition_pdf


def serve_rf_file(request, filename):
    """
    Serve RF (Requisition Form) PDF files from Requisition/media/rfs directory
    """
    try:
        from django.apps import apps
        requisition_app_path = apps.get_app_config('Requisition').path
        file_path = os.path.join(requisition_app_path, 'media', 'rfs', filename)
        
        print(f"📁 Looking for file at: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            raise Http404("RF file not found")
        
        print(f"✅ Serving file: {filename}")
        return FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=filename
        )
    except Exception as e:
        print(f"❌ Error serving RF file: {e}")
        raise Http404("RF file not found")


def inventory_items_view(request):
    inventory_items = Inventory.objects.select_related('product').all()
    
    for item in inventory_items:
        specs_qs = Product_Specification.objects.filter(product=item.product)
        # Convert to list of tuples for template iteration
        item.specs_list = [(spec.spec_name, spec.spec_value) for spec in specs_qs]

    context = {
        'inventory_items': inventory_items,
    }
    return render(request, 'requisition/inventory_replenishment_form.html', context)


@login_required
def requisition_list(request):
    """
    List all requisitions (placeholder for now)
    """
    user_id = request.session.get('user_id', 1)
    user = User.objects.get(user_id=user_id)
    
    requisitions = Requisition.objects.filter(
        requested_by=user
    ).order_by('-req_requested_date')
    
    context = {
        'requisitions': requisitions,
        'user': user,
    }
    
    return render(request, 'requisition/requisition_list.html', context)


@login_required
def requisition_detail(request, req_id):
    """
    View requisition details
    """
    requisition = Requisition.objects.get(req_id=req_id)
    items = RequisitionItem.objects.filter(requisition=requisition)
    timeline = RequisitionStatusTimeline.objects.filter(
        requisition=requisition
    ).order_by('changed_at')
    
    context = {
        'requisition': requisition,
        'items': items,
        'timeline': timeline,
    }
    
    return render(request, 'requisition/requisition_detail.html', context)