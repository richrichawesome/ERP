# Requisition/views/internal_transfer.py

from datetime import datetime
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.urls import reverse

from ERP.models import Inventory, Product, Product_Specification, User, Branch
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from Requisition.utils import generate_internal_transfer_pdf


@login_required
def internal_transfer_form(request):
    """
    Display the internal transfer form showing current branch inventory 
    and other branches' inventory
    """
    print("🔍 === DEBUG: INTERNAL TRANSFER VIEW CALLED ===")
    
    try:
        # Get current user
        user_id = request.session.get("user_id")
        print(f"📱 Session user_id: {user_id}")
        
        if not user_id:
            print("❌ No user_id in session!")
            context = {
                'current_inventory': [],
                'other_branches': [],
                'user': None,
                'error': 'Please log in again',
                'active_page': 'inventory_replenishment',
            }
            return render(request, 'requisition/internal_transfer_form.html', context)
        
        # Get user and their branch
        user = User.objects.get(user_id=user_id)
        current_branch = user.branch
        print(f"✅ User: {user.username} (ID: {user.user_id})")
        print(f"🏢 Current branch: {current_branch.branch_name}")
        
        # Get current branch inventory
        current_inventory = Inventory.objects.filter(
            branch=current_branch,
            product__prod_is_active=True
        ).select_related('product', 'product__category').order_by('product__prod_name')
        
        print(f"📊 Found {current_inventory.count()} items in current branch")
        
        # Add specifications to current inventory
        for item in current_inventory:
            specs = Product_Specification.objects.filter(product=item.product)
            item.specs_list = [(spec.spec_name, spec.spec_value) for spec in specs]
        
        # Get all other branches
        other_branches = Branch.objects.exclude(branch_id=current_branch.branch_id)
        
        # For each branch, get their inventory
        branches_with_inventory = []
        for branch in other_branches:
            inventory = Inventory.objects.filter(
                branch=branch,
                product__prod_is_active=True
            ).select_related('product', 'product__category').order_by('product__prod_name')
            
            # Add specifications
            for item in inventory:
                specs = Product_Specification.objects.filter(product=item.product)
                item.specs_list = [(spec.spec_name, spec.spec_value) for spec in specs]
            
            branches_with_inventory.append({
                'branch': branch,
                'inventory': inventory
            })
            
            print(f"🏢 Branch: {branch.branch_name} - {inventory.count()} items")
        
        context = {
            'current_inventory': current_inventory,
            'other_branches': branches_with_inventory,
            'user': user,
            'current_branch': current_branch,
            "active_page": "internal_transfer",
        }
        
        print("🎯 === DEBUG: RENDERING TEMPLATE ===")
        return render(request, 'requisition/internal_transfer_form.html', context)
    
    except User.DoesNotExist:
        print(f"❌ ERROR: No User found with ID: {user_id}")
        context = {
            'current_inventory': [],
            'other_branches': [],
            'user': None,
            'error': 'User not found in system'
        }
        return render(request, 'requisition/internal_transfer_form.html', context)
    
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        context = {
            'current_inventory': [],
            'other_branches': [],
            'user': None,
            'error': str(e)
        }
        return render(request, 'requisition/internal_transfer_form.html', context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def create_internal_transfer(request):
    """
    Handle the submission of internal transfer requisition
    """
    try:
        # Parse JSON data
        data = json.loads(request.body)
        items = data.get('items', [])
        notes = data.get('notes', '')
        date_required_str = data.get('date_required')
        sender_branch_id = data.get('sender_branch_id')
        
        print(f"🔍 Creating internal transfer requisition")
        print(f"📦 Items: {len(items)}")
        print(f"📅 Date required: {date_required_str}")
        print(f"🏢 Sender branch ID: {sender_branch_id}")

        # Validate items
        if not items:
            return JsonResponse({
                'success': False,
                'error': 'No items provided in the requisition'
            }, status=400)
        
        # Validate date required
        if not date_required_str:
            return JsonResponse({
                'success': False,
                'error': 'Date required is missing'
            }, status=400)
        
        # Validate sender branch
        if not sender_branch_id:
            return JsonResponse({
                'success': False,
                'error': 'Sender branch is missing'
            }, status=400)
        
        # Convert date string to date object
        try:
            date_required = datetime.strptime(date_required_str, '%Y-%m-%d').date()
            if date_required < timezone.now().date():
                return JsonResponse({
                    'success': False,
                    'error': 'Date required cannot be in the past'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid date format'
            }, status=400)

        # Get current user (requester)
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not logged in. Please log in again.'
            }, status=401)
            
        user = User.objects.get(user_id=user_id)
        requester_branch = user.branch
        
        # Get sender branch
        sender_branch = Branch.objects.get(branch_id=sender_branch_id)
        
        print(f"👤 Requester: {user.username} from {requester_branch.branch_name}")
        print(f"📤 Sender branch: {sender_branch.branch_name}")
        
        # Validate stock availability in sender branch
        for item_data in items:
            try:
                product = Product.objects.get(prod_id=item_data['product_id'])
                sender_inventory = Inventory.objects.get(
                    branch=sender_branch,
                    product=product
                )
                
                requested_qty = item_data['quantity']
                available_qty = sender_inventory.quantity_on_hand
                
                if requested_qty > available_qty:
                    return JsonResponse({
                        'success': False,
                        'error': f'Insufficient stock for {product.prod_name}. Available: {available_qty}, Requested: {requested_qty}'
                    }, status=400)
                    
            except Product.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f"Product with ID {item_data['product_id']} not found"
                }, status=404)
            except Inventory.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f"{product.prod_name} not found in {sender_branch.branch_name} inventory"
                }, status=404)
        
        # Create Requisition record
        requisition = Requisition.objects.create(
            requested_by=user,
            branch=requester_branch,
            sender_branch=sender_branch,
            sender_user=None,  # Will be set when sender approves
            req_type='INTERNAL_TRANSFER',
            req_main_status='PENDING_CUSTODIAN',
            req_substatus='NONE',
            req_notes=notes if notes else None,
            req_date_required=date_required,
            req_requested_date=timezone.now()
        )
        
        print(f"✅ Created requisition: REQ-{requisition.req_id}")
        
        # Create RequisitionItem records
        for item_data in items:
            product = Product.objects.get(prod_id=item_data['product_id'])
            
            RequisitionItem.objects.create(
                requisition=requisition,
                product=product,
                quantity=item_data['quantity'],
                uom=item_data['uom']
            )
            print(f"📦 Added item: {product.prod_name} x {item_data['quantity']} {item_data['uom']}")
        
        # Create initial timeline entry
        RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='PENDING_CUSTODIAN',
            sub_status=None,
            user=user,
            changed_at=timezone.now(),
            comment='Internal transfer requisition created and submitted for approval'
        )
        
        print(f"📋 Created timeline entry")
        
        # Generate RF PDF
        try:
            rf_url = generate_internal_transfer_pdf(requisition)
            print(f"📄 Generated RF: {rf_url}")
        except Exception as pdf_error:
            print(f"⚠️ RF generation failed: {pdf_error}")
            import traceback
            traceback.print_exc()
            rf_url = None
        
        # Prepare response
        response_data = {
            'success': True,
            'requisition_id': requisition.req_id,
            'requisition_number': f'REQ-{requisition.req_id:06d}',
            'message': f'Internal transfer requisition REQ-{requisition.req_id:06d} submitted successfully!',
            'rf_url': rf_url,
            'redirect_url': reverse('track_requisition')
        }
        
        print(f"🎯 Internal transfer requisition submission completed")
        return JsonResponse(response_data)
    
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found. Please log in again.'
        }, status=404)
    
    except Branch.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Sender branch not found.'
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data format'
        }, status=400)
    
    except Exception as e:
        print(f"❌ Error creating internal transfer: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)