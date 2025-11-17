from django.shortcuts import render, redirect

def property_custodian_dashboard(request):

    return render(request, "main/property_custodian_dashboard.html")