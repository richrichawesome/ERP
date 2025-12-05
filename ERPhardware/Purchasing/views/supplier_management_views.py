# Purchasing/views/supplier_management_views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
import json

from ERP.models import User, Product, Product_Specification, Product_Category
from Purchasing.models import *


@login_required
def purchasing_staff_sup_manage(request):
    """Display supplier management page with list of suppliers"""
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    
    # Get all active suppliers
    suppliers = Supplier.objects.filter(sup_is_active=True).order_by('sup_name')
    
    context = {
        "active_page": "supplier",
        "user": user,
        "suppliers": suppliers
    }
    
    return render(request, "purchasing/purchasing_staff_sup_manage.html", context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def create_supplier(request):
    """Create a new supplier"""
    try:
        data = json.loads(request.body)
        
        # Check for duplicate supplier name
        if Supplier.objects.filter(sup_name__iexact=data['name']).exists():
            return JsonResponse({
                'success': False,
                'error': 'A supplier with this name already exists.'
            }, status=400)
        
        # Create supplier
        supplier = Supplier.objects.create(
            sup_name=data['name'],
            sup_phone=data['phone'],
            sup_email=data.get('email', ''),
            sup_address=data.get('address', ''),
            sup_contact_person=data['contact_person'],
            sup_payment_terms=data.get('payment_terms', ''),
            sup_delivery_terms=data.get('delivery_terms', ''),
            sup_is_active=True
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier created successfully',
            'supplier_id': supplier.sup_id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def supplier_catalog(request, supplier_id):
    """Display supplier catalog page"""
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    
    supplier = get_object_or_404(Supplier, sup_id=supplier_id)
    
    # Get all products offered by this supplier
    supplier_products = Supplier_Product.objects.filter(
        supplier=supplier,
        sup_prod_is_active=True
    ).select_related('product', 'product__category').order_by('product__prod_name')
    
    # Add specifications to each product
    for sp in supplier_products:
        specs = Product_Specification.objects.filter(product=sp.product)
        sp.specs_list = [(spec.spec_name, spec.spec_value) for spec in specs]
    
    # Get unique categories offered by supplier
    categories = Product_Category.objects.filter(
        product__supplier_product__supplier=supplier,
        product__supplier_product__sup_prod_is_active=True
    ).distinct().order_by('prod_cat_name')
    
    context = {
        "active_page": "supplier",
        "user": user,
        "supplier": supplier,
        "supplier_products": supplier_products,
        "categories": categories
    }
    
    return render(request, "purchasing/supplier_catalog.html", context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def update_supplier(request, supplier_id):
    """Update supplier information"""
    try:
        supplier = get_object_or_404(Supplier, sup_id=supplier_id)
        data = json.loads(request.body)
        
        # Check for duplicate name (excluding current supplier)
        if Supplier.objects.filter(
            sup_name__iexact=data['name']
        ).exclude(sup_id=supplier_id).exists():
            return JsonResponse({
                'success': False,
                'error': 'A supplier with this name already exists.'
            }, status=400)
        
        # Update supplier
        supplier.sup_name = data['name']
        supplier.sup_phone = data['phone']
        supplier.sup_email = data.get('email', '')
        supplier.sup_address = data.get('address', '')
        supplier.sup_contact_person = data['contact_person']
        supplier.sup_payment_terms = data.get('payment_terms', '')
        supplier.sup_delivery_terms = data.get('delivery_terms', '')
        supplier.sup_updated_at = timezone.now()
        supplier.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def add_product_to_supplier(request, supplier_id):
    """Display page to add products to supplier catalog"""
    user_id = request.session.get("user_id")
    user = User.objects.get(pk=user_id)
    
    supplier = get_object_or_404(Supplier, sup_id=supplier_id)
    
    # Get products NOT already in supplier's catalog
    existing_product_ids = Supplier_Product.objects.filter(
        supplier=supplier,
        sup_prod_is_active=True
    ).values_list('product_id', flat=True)
    
    available_products = Product.objects.filter(
        prod_is_active=True
    ).exclude(
        prod_id__in=existing_product_ids
    ).select_related('category').order_by('prod_name')
    
    # Add specifications to each product
    for product in available_products:
        specs = Product_Specification.objects.filter(product=product)
        product.specs_list = [(spec.spec_name, spec.spec_value) for spec in specs]
    
    # Get all categories
    categories = Product_Category.objects.all().order_by('prod_cat_name')
    
    context = {
        "active_page": "supplier",
        "user": user,
        "supplier": supplier,
        "available_products": available_products,
        "categories": categories
    }
    
    return render(request, "purchasing/add_product_to_supplier.html", context)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def save_supplier_products(request, supplier_id):
    """Save products to supplier catalog"""
    try:
        supplier = get_object_or_404(Supplier, sup_id=supplier_id)
        data = json.loads(request.body)
        items = data.get('items', [])
        
        if not items:
            return JsonResponse({
                'success': False,
                'error': 'No products provided'
            }, status=400)
        
        # Create supplier products
        for item_data in items:
            product = Product.objects.get(prod_id=item_data['product_id'])
            
            # Check if product already exists for this supplier
            if Supplier_Product.objects.filter(
                supplier=supplier,
                product=product,
                sup_prod_is_active=True
            ).exists():
                continue
            
            Supplier_Product.objects.create(
                supplier=supplier,
                product=product,
                sup_prod_code=item_data.get('product_code', product.prod_sku),
                sup_prod_unit_price=item_data['unit_price']
            )
            
            # Create supplier-category relationship if not exists
            if not Supplier_Category.objects.filter(
                supplier=supplier,
                prod_cat=product.category
            ).exists():
                Supplier_Category.objects.create(
                    supplier=supplier,
                    prod_cat=product.category
                )
        
        return JsonResponse({
            'success': True,
            'message': f'{len(items)} product(s) added to supplier catalog',
            'redirect_url': f'/supplier-catalog/{supplier_id}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def update_product_price(request, supplier_product_id):
    """Update product price in supplier catalog and create price history"""
    try:
        supplier_product = get_object_or_404(
            Supplier_Product,
            sup_prod_id=supplier_product_id
        )
        
        data = json.loads(request.body)
        new_price = data.get('unit_price')
        
        if not new_price or float(new_price) <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Invalid price'
            }, status=400)
        
        # Get the old price before updating
        old_price = supplier_product.sup_prod_unit_price
        
        # Only create history if price actually changed
        if old_price != float(new_price):
            # Create price history entry
            from Purchasing.models import Supplier_Product_PriceHistory
            
            # Get the actual User instance from session
            user_id = request.session.get("user_id")
            if user_id:
                user_instance = User.objects.get(pk=user_id)
            else:
                # Fallback to request.user if session user_id not available
                user_instance = request.user if request.user.is_authenticated else None
            
            Supplier_Product_PriceHistory.objects.create(
                supplier_product=supplier_product,
                price=old_price,  # Store the old price in history
                changed_by=user_instance
            )
        
        # Update the current price
        supplier_product.sup_prod_unit_price = new_price
        supplier_product.sup_prod_last_updated_price = timezone.now()
        supplier_product.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Price updated successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def get_price_history(request, supplier_product_id):
    """Get price history for a supplier product"""
    try:
        supplier_product = get_object_or_404(
            Supplier_Product,
            sup_prod_id=supplier_product_id
        )
        
        # Get price history ordered by most recent first
        price_history = Supplier_Product_PriceHistory.objects.filter(
            supplier_product=supplier_product
        ).order_by('-changed_at')
        
        history_data = []
        for history in price_history:
            changed_by_name = "System"
            if history.changed_by:
                # Use the custom User model fields
                user = history.changed_by
                changed_by_name = f"{user.user_fname} {user.user_lname}".strip()
                if not changed_by_name:  # Fallback to username if names are empty
                    changed_by_name = user.username
            
            history_data.append({
                'price': float(history.price),
                'changed_at': history.changed_at.strftime("%b %d, %Y %H:%M"),
                'changed_by': changed_by_name
            })
        
        # Add current price as the most recent entry
        current_price_data = {
            'price': float(supplier_product.sup_prod_unit_price),
            'changed_at': supplier_product.sup_prod_last_updated_price.strftime("%b %d, %Y %H:%M"),
            'changed_by': 'Current Price',
            'is_current': True
        }
        
        return JsonResponse({
            'success': True,
            'product_name': f"{supplier_product.product.prod_name} ({supplier_product.sup_prod_code})",
            'supplier_name': supplier_product.supplier.sup_name,
            'current_price': current_price_data,
            'history': history_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)