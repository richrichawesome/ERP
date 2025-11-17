from django.shortcuts import render, redirect

def branch_manager_dashboard(request):

    return render(request, "main/branch_manager_dashboard.html")