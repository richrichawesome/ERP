from django.shortcuts import render, redirect
from ERP.models import User

def purchasing_staff_inventory(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    return render(request, "main/inventory.html", {"active_page": "inventory", "user": user})