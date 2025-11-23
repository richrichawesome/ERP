from django.shortcuts import render, redirect
from django.contrib import messages
from ..models import User
from django.utils.timezone import now #para sa last_login field
from Requisition import *

def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User doesn't exist.")
            return render(request, 'main/login.html')
        
        if user.user_password == password:
            if user.is_active:
                user.last_login = now()
                user.save()
                print(f"Role ID: {user.role.role_id if user.role else 'None'}")

                request.session['user_id'] = user.pk
                role_id = user.role.role_id
                if role_id == 1:
                    return redirect('top_management_dashboard')
                
                elif role_id == 2:
                    return redirect('track_requisition')
                
                elif role_id == 3:
                    return redirect('purchasing_staff_dashboard')
                
                elif role_id == 4:
                    return redirect('property_custodian_dashboard')
                
                else:
                    messages.error(request, "Role is not assigned properly.")
                    return render(request, "main/login.html")
            else:
                messages.error(request, "Invalid User.")
                return render(request, 'main/login.html')
        else:
            messages.error(request, "Incorrect password.")
            return render(request, 'main/login.html')
    
    return render(request, 'main/login.html')
