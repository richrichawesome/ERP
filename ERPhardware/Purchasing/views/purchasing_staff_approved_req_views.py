from django.shortcuts import render, redirect
from ERP.models import User

def purchasing_staff_approved_req(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    return render(request, "purchasing/rfq_creation.html", {"active_page": "requisition", "user": user})

