from django.shortcuts import render, redirect

def purchasing_staff_dashboard(request):

    return render(request, "main/purchasing_staff_dashboard.html")