import json
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from datetime import datetime

from ERP.models import Inventory, Product, User, Product_Specification
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from Requisition.utils import generate_requisition_pdf

# def inventory_items_view(request):
#     inventory_items = Inventory.objects.select_related('product').all()
    
#     # Build a dictionary of product_id -> spec dictionary
#     product_specs = {}
#     for item in inventory_items:
#         specs_qs = Product_Specification.objects.filter(product=item.product)
#         specs_dict = {spec.spec_name: spec.spec_value for spec in specs_qs}
#         product_specs[item.product.prod_id] = specs_dict
    
#     context = {
#         'inventory_items': inventory_items,
#         'product_specs': product_specs,
#     }
#     return render(request, 'requisition/inventory_list.html', context)

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