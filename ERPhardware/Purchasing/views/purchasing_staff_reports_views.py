from django.shortcuts import render, redirect
from ERP.models import User

def purchasing_staff_reports(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    return render(request, "purchasing/purchasing_staff_reports.html", {"active_page": "reports", "user": user})