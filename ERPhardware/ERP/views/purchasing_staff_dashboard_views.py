from django.shortcuts import render, redirect
from ..models import User

def purchasing_staff_dashboard(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(pk=user_id)
    print(user)

    return render(request, "main/purchasing_staff_dashboard.html", {"section": "dashboard", "active_page": "dashboard", "user": user})