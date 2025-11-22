from django.shortcuts import render, redirect
from ERP.models import User

def purchasing_staff_track_progress(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    return render(request, "purchasing/purchasing_staff_track_progress.html", {"active_page": "t_progress", "user": user})