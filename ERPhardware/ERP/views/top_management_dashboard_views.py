from django.shortcuts import render
from ..models import User
def top_management_dashboard(request):
    user_id = request.session.get('user_id')
    user = User.objects.get(pk=user_id)
    print(user)

    return render(request, "main/top_management_dashboard.html", {"section": "dashboard", "active_page": "dashboard", "user": user})