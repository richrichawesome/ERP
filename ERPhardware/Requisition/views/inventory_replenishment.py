# Requisition/views/inventory_replenishment.py

from datetime import datetime
import json
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.urls import reverse

from ERP.models import Inventory, Product, Product_Specification, User
from Requisition.models import Requisition, RequisitionItem, RequisitionStatusTimeline
from Requisition.utils import generate_requisition_pdf

# @login_required
# def inventory_replenishment_form(request):
#     """
#     Display the inventory replenishment form with all inventory items
#     """
#     print("🔍 === DEBUG: VIEW FUNCTION CALLED ===")
    
#     try:
#         # METHOD: Use session user_id (your current approach)
#         user_id = request.session.get("user_id")
#         print(f"📱 Session user_id: {user_id}")
        
#         if not user_id:
#             print("❌ No user_id in session!")
#             # Handle this case
#             context = {
#                 'inventory_items': [],
#                 'user': None,
#                 'error': 'Please log in again'
#             }
#             return render(request, 'requisition/inventory_replenishment_form.html', context)
        
#         # Get user from your custom User model using session user_id
#         user = User.objects.get(user_id=user_id)
#         print(f"✅ Custom User found: {user.username} (ID: {user.user_id})")
#         print(f"🏢 User branch: {user.branch}")
        
#         # Get inventory for this user's branch
#         inventory_items = Inventory.objects.filter(
#             branch=user.branch,
#             product__prod_is_active=True
#         ).select_related('product', 'product__category').order_by('product__prod_name')
        
#         print(f"📊 Found {inventory_items.count()} inventory items for {user.username}'s branch")
        
#         # Show what we found
#         for item in inventory_items:
#             print(f"   - {item.product.prod_name}: {item.quantity_on_hand}")
        
#         context = {
#             'inventory_items': inventory_items,
#             'user': user,
#         }
        
#         print("🎯 === DEBUG: RENDERING TEMPLATE ===")
#         return render(request, 'requisition/inventory_replenishment_form.html', context)
    
#     except User.DoesNotExist:
#         print(f"❌ ERROR: No custom User found with ID: {user_id}")
#         context = {
#             'inventory_items': [],
#             'user': None,
#             'error': 'User not found in system'
#         }
#         return render(request, 'requisition/inventory_replenishment_form.html', context)
    
#     except Exception as e:
#         print(f"❌ UNEXPECTED ERROR: {e}")
#         import traceback
#         traceback.print_exc()
#         context = {
#             'inventory_items': [],
#             'user': None,
#             'error': str(e)
#         }
#         return render(request, 'requisition/inventory_replenishment_form.html', context)

@login_required
def inventory_replenishment_form(request):
    """
    Display the inventory replenishment form with all inventory items
    """
    print("🔍 === DEBUG: VIEW FUNCTION CALLED ===")
    
    try:
        # METHOD: Use session user_id
        user_id = request.session.get("user_id")
        print(f"📱 Session user_id: {user_id}")
        
        if not user_id:
            print("❌ No user_id in session!")
            context = {
                'inventory_items': [],
                'user': None,
                'error': 'Please log in again'
            }
            return render(request, 'requisition/inventory_replenishment_form.html', context)
        
        # Get user from your custom User model using session user_id
        user = User.objects.get(user_id=user_id)
        print(f"✅ Custom User found: {user.username} (ID: {user.user_id})")
        print(f"🏢 User branch: {user.branch}")
        
        # Get inventory for this user's branch
        inventory_items = Inventory.objects.filter(
            branch=user.branch,
            product__prod_is_active=True
        ).select_related('product', 'product__category').order_by('product__prod_name')
        
        print(f"📊 Found {inventory_items.count()} inventory items for {user.username}'s branch")
        
        # ADD THIS: Get specifications for each product
        for item in inventory_items:
            # Get all specifications for this product
            specs = Product_Specification.objects.filter(product=item.product)
            # Convert to list of (key, value) tuples for the template
            item.specs_list = [(spec.spec_name, spec.spec_value) for spec in specs]
            print(f"   - {item.product.prod_name}: {len(item.specs_list)} specs")
        
        context = {
            'inventory_items': inventory_items,
            'user': user,
        }
        
        print("🎯 === DEBUG: RENDERING TEMPLATE ===")
        return render(request, 'requisition/inventory_replenishment_form.html', context)
    
    except User.DoesNotExist:
        print(f"❌ ERROR: No custom User found with ID: {user_id}")
        context = {
            'inventory_items': [],
            'user': None,
            'error': 'User not found in system'
        }
        return render(request, 'requisition/inventory_replenishment_form.html', context)
    
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        context = {
            'inventory_items': [],
            'user': None,
            'error': str(e)
        }
        return render(request, 'requisition/inventory_replenishment_form.html', context)

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def create_inventory_replenishment(request):
    """
    Handle the submission of inventory replenishment requisition
    Creates Requisition, RequisitionItem, RequisitionStatusTimeline records
    and generates PDF
    """
    try:
        # Parse JSON data from request
        data = json.loads(request.body)
        items = data.get('items', [])
        notes = data.get('notes', '')
        date_required_str = data.get('date_required')  # ADD THIS
        
        print(f"📝 Creating requisition with {len(items)} items")
        print(f"📅 Date required: {date_required_str}")

        # Validate that items exist
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
        
        # Convert date string to date object
        try:
            date_required = datetime.strptime(date_required_str, '%Y-%m-%d').date()
            # Validate that date is not in the past
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

        # Get current user from session
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'User not logged in. Please log in again.'
            }, status=401)
            
        user = User.objects.get(user_id=user_id)
        print(f"👤 Creating requisition for user: {user.username}, Branch: {user.branch}")
        
        # 1. Create Requisition record
        requisition = Requisition.objects.create(
            requested_by=user,
            branch=user.branch,
            req_type='INV_REPLENISHMENT',
            req_main_status='PENDING_CUSTODIAN',  # Main status: Pending for Custodian Approval
            req_substatus='None',  # Sub-status: None
            req_notes=notes if notes else None,
            req_date_required=date_required,  # ADD THIS
            req_requested_date=timezone.now()
        )
        
        print(f"✅ Created requisition: REQ-{requisition.req_id}")
        print(f"📅 Requisition required by: {requisition.req_date_required}")
        
        # 2. Create RequisitionItem records for each product
        requisition_items = []
        for item_data in items:
            try:
                product = Product.objects.get(prod_id=item_data['product_id'])
                
                requisition_item = RequisitionItem.objects.create(
                    requisition=requisition,
                    product=product,
                    quantity=item_data['quantity'],
                    uom=item_data['uom']
                )
                requisition_items.append(requisition_item)
                print(f"📦 Added item: {product.prod_name} x {item_data['quantity']} {item_data['uom']}")
                
            except Product.DoesNotExist:
                # Rollback transaction if product not found
                raise Exception(f"Product with ID {item_data['product_id']} not found")
        
        # 3. Create initial timeline entry for history tracking
        timeline_entry = RequisitionStatusTimeline.objects.create(
            requisition=requisition,
            main_status='PENDING_CUSTODIAN',  # Main status: Pending for Custodian Approval
            sub_status=None,  # Sub-status: null
            user=user,
            changed_at=timezone.now(),
            comment='Requisition created and submitted for approval'
        )
        
        print(f"📋 Created timeline entry: {timeline_entry.main_status}")
        
        # 4. Generate RF (Requisition Form) PDF and save to database
        try:
            rf_url = generate_requisition_pdf(requisition)
            print(f"📄 Generated RF: {rf_url}")
            
            # The RF file is now automatically saved to requisition.rf_file
            # and stored in media/rfs/ folder
            
        except Exception as pdf_error:
            print(f"⚠️ RF generation failed: {pdf_error}")
            rf_url = None

        
        # 5. Prepare success response
        response_data = {
            'success': True,
            'requisition_id': requisition.req_id,
            'requisition_number': f'REQ-{requisition.req_id:06d}',
            'message': f'Requisition REQ-{requisition.req_id:06d} submitted successfully!',
            'rf_url': rf_url,  # CHANGED: pdf_url → rf_url
            'redirect_url': reverse('track_requisition')
        }
        
        print(f"🎯 Requisition submission completed successfully")
        return JsonResponse(response_data)
    
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User not found. Please log in again.'
        }, status=404)
    
    except Product.DoesNotExist as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data format'
        }, status=400)
    
    except Exception as e:
        print(f"❌ Error creating requisition: {e}")
        return JsonResponse({
            'success': False,
            'error': f'An error occurred while creating the requisition: {str(e)}'
        }, status=500)
    
# Add this to your views
from django.http import HttpResponse
from Requisition.utils import generate_requisition_pdf

def test_pdf_generation(request, req_id):
    """Test PDF generation for a specific requisition"""
    try:
        requisition = Requisition.objects.get(req_id=req_id)
        pdf_url = generate_requisition_pdf(requisition)
        
        return HttpResponse(f"""
            <h1>PDF Generation Test</h1>
            <p>Requisition: REQ-{requisition.req_id:06d}</p>
            <p>PDF URL: <a href="{pdf_url}" target="_blank">{pdf_url}</a></p>
            <p>RF File in DB: {requisition.rf_file.name if requisition.rf_file else 'None'}</p>
            <p>RF File Path: {requisition.rf_file.path if requisition.rf_file else 'None'}</p>
            <p>File exists: {os.path.exists(requisition.rf_file.path) if requisition.rf_file else 'False'}</p>
        """)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")