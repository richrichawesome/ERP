# ERP/ERP/views/add_users_views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import User, Role, Branch
import json
from django.utils.timezone import now

def user_management(request):
    """Main user management page"""
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    # Get current user
    try:
        current_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return redirect('login')
    
    # Get all users with related data
    users = User.objects.select_related('role', 'branch').all().order_by('user_id')
    
    # Get all branches for filter dropdown
    branches = Branch.objects.filter(branch_is_active=True)
    
    return render(request, "main/user_management.html", {
        "section": "user_management",
        "users": users,
        "branches": branches,
        "active_page": "user_management",
        "user": current_user
    })

@csrf_exempt
def get_user(request):
    """Get user details for editing"""
    try:
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User ID is required"
            })
        
        # Get user with related data
        user = User.objects.select_related('role', 'branch').get(pk=user_id)
        
        return JsonResponse({
            "success": True,
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "user_email": user.user_email,
                "user_fname": user.user_fname,
                "user_lname": user.user_lname,
                "is_active": user.is_active,
                "role": {
                    "role_id": user.role.role_id,
                    "role_name": user.role.role_name
                },
                "branch": {
                    "branch_id": user.branch.branch_id,
                    "branch_name": user.branch.branch_name
                }
            }
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "User not found"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
def add_user_api(request):
    """API endpoint to add new user"""
    try:
        data = json.loads(request.body)
        
        # Get data from request
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        fname = data.get("fname")
        lname = data.get("lname")
        role_name = data.get("role_name")
        branch_id = data.get("branch_id")
        
        # Validate required fields
        if not all([username, password, email, fname, lname, role_name, branch_id]):
            return JsonResponse({
                "success": False,
                "error": "All required fields must be filled"
            })
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                "success": False,
                "error": "Username already exists"
            })
        
        # Check if email already exists
        if User.objects.filter(user_email=email).exists():
            return JsonResponse({
                "success": False,
                "error": "Email already exists"
            })
        
        # Get role
        try:
            role = Role.objects.get(role_name=role_name)
        except Role.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": f"Role '{role_name}' not found"
            })
        
        # Get branch
        try:
            branch = Branch.objects.get(pk=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Branch not found"
            })
        
        # Create user
        user = User.objects.create(
            username=username,
            user_password=password,
            user_email=email,
            user_fname=fname,
            user_lname=lname,
            role=role,
            branch=branch,
            is_active=True
        )
        
        return JsonResponse({
            "success": True,
            "message": f"User '{username}' created successfully",
            "user": {
                "user_id": user.user_id,
                "username": user.username
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
def edit_user_api(request):
    """API endpoint to edit user"""
    try:
        data = json.loads(request.body)
        
        # Get data from request
        user_id = data.get("user_id")
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")
        fname = data.get("fname")
        lname = data.get("lname")
        role_name = data.get("role_name")
        branch_id = data.get("branch_id")
        is_active = data.get("is_active")
        
        # Validate required fields
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User ID is required"
            })
        
        # Get user
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            })
        
        # Check if email already exists (excluding current user)
        if email and User.objects.filter(user_email=email).exclude(pk=user_id).exists():
            return JsonResponse({
                "success": False,
                "error": "Email already exists"
            })
        
        # Update fields if provided
        if username:
            # Check if username already exists (excluding current user)
            if User.objects.filter(username=username).exclude(pk=user_id).exists():
                return JsonResponse({
                    "success": False,
                    "error": "Username already exists"
                })
            user.username = username
        
        if password:
            user.user_password = password
        
        if email:
            user.user_email = email
        
        if fname:
            user.user_fname = fname
        
        if lname:
            user.user_lname = lname
        
        if role_name:
            try:
                role = Role.objects.get(role_name=role_name)
                user.role = role
            except Role.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "error": f"Role '{role_name}' not found"
                })
        
        if branch_id:
            try:
                branch = Branch.objects.get(pk=branch_id)
                user.branch = branch
            except Branch.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "error": "Branch not found"
                })
        
        if is_active is not None:
            user.is_active = is_active
        
        user.save()
        
        return JsonResponse({
            "success": True,
            "message": f"User '{user.username}' updated successfully"
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })