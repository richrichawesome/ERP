from django.shortcuts import render, redirect
from ..models import User, Role, Branch
from django.contrib import messages
from django.utils.timezone import now #para sa last_login field

def add_users(request):
    branches = Branch.objects.all()
    user_id = request.session.get('user_id')
    user = User.objects.get(pk=user_id)
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        role_name = request.POST.get('acc-role')
        branch_id = request.POST.get('branch')
        

        role = Role.objects.get(role_name=role_name)
        branch = Branch.objects.get(branch_id=branch_id)
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "main/top_management_dashboard.html", {
                "section": "add_users",
                "branches": branches
            })
        
        user = User(
            username=username,
            user_password=password,
            user_email=email,
            user_fname=fname,
            user_lname=lname,
            role=role,
            branch=branch,
            is_active=True
        )
        user.save()
        messages.success(request, f"User '{username}' successfully created!")
        return redirect('top_management_dashboard')
        
    return render(request, "main/add_users.html", {"section": "add_users", "branches": branches, "active_page": "add_users", "user": user})