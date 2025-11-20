from django.shortcuts import render, redirect
from ERP.models import Inventory, User


def track_requisition_page(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    return render(request, "requisition/track_requisition.html", {
        "active_page": "track_requisition",
        "user": user
    })

def redirect_inventory_replenishment_form(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    
    # ADD THESE LINES to fetch inventory data:
    inventory_items = Inventory.objects.filter(
        branch=user.branch,
        product__prod_is_active=True
    ).select_related('product', 'product__category').order_by('product__prod_name')
    
    return render(request, "requisition/inventory_replenishment_form.html", {
        "active_page": "inventory_replenishment",
        "user": user,
        "inventory_items": inventory_items  # ADD THIS
    })


def redirect_internal_transfer_form(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    return render(request, "requisition/internal_transfer_form.html", {
        "active_page": "internal_transfer",
        "user": user
    })
