from django.shortcuts import render

def top_management_dashboard(request):

    return render(request, "main/top_management_dashboard.html", {"section": "dashboard"})