# Purchasing/purchasing_staff_sup_manage_views.py

from django.shortcuts import render, redirect
from ERP.models import User

def purchasing_staff_sup_manage(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    return render(request, "purchasing/purchasing_staff_sup_manage.html", {"active_page": "supplier", "user": user})