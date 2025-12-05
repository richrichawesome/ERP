from django.shortcuts import render, redirect
from ERP.models import User


def create_po(request):
    user_id = request.session.get("user_id")   # the ID you saved during login
    user = User.objects.get(pk=user_id)
    return render(request, "purchasing/create_po.html", {"active_page": "po",  "user": user})