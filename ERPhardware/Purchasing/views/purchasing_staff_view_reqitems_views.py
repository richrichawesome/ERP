from django.shortcuts import render, get_object_or_404
from Requisition.models import Requisition, RequisitionItem
from ERP.models import User

def purchasing_staff_view_reqitems(request, req_id):

    # Logged-in user
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)

    # Fetch the requisition
    requisition = get_object_or_404(Requisition, pk=req_id)

    # Fetch all items for this requisition
    req_items = RequisitionItem.objects.filter(requisition_id=req_id)

    return render(
        request,
        "purchasing/purchasing_staff_view_reqitems.html",
        {
            "user": user,
            "requisition": requisition,
            "req_items": req_items,
        }
    )
