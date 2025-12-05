from django.shortcuts import render, redirect
from ERP.models import User


def purchasing_staff_dashboard(request):
    user_id = request.session.get("user_id")   # the ID you saved during login
    user = User.objects.get(pk=user_id)
    return render(request, "purchasing/purchasing_staff_dashboard.html", {"active_page": "dashboard",  "user": user})