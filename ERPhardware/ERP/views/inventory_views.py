from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import Inventory, Product_Category, Product_Specification, Inventory_Transaction, User, Product, Price_History, Branch, Role
from django.utils import timezone
import json

@csrf_exempt  #Note: allow AJAX POST without CSRF token: {{ %csrf_token% }}
def stock_action(request):
    try:
        data = json.loads(request.body)
        inventory_id = data.get("inventory_id")
        quantity = data.get("quantity")
        action_type = data.get("action_type")
        user_id = data.get("user_id")

        # validate input
        if not all([inventory_id, quantity, action_type]):
            return JsonResponse({
                "success": False, 
                "error": "Missing required fields"
            })
        
        #inventory db
        try:
            inventory = Inventory.objects.select_related('product').get(pk=inventory_id)
        except Inventory.DoesNotExist:
            return JsonResponse({
                "success": False, 
                "error": "Inventory not found"
            })
        
        # validate quantity
        try:
            quantity = int(quantity)
            if quantity <= 0:
                return JsonResponse({
                    "success": False, 
                    "error": "Quantity must be positive"
                })
        except (ValueError, TypeError):
            return JsonResponse({
                "success": False, 
                "error": "Invalid quantity"
            })
        
        if not user_id:
            user_id = request.session.get('user_id')
            
        if not user_id:
            return JsonResponse({
                "success": False, 
                "error": "User not authenticated"
            })
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False, 
                "error": "User not found"
            })
        
        # update inventory quantity based on action type == [stock in or stock out]
        old_quantity = inventory.quantity_on_hand

        if action_type == "in":
            inventory.quantity_on_hand += quantity
            trans_type = "stockin"
        elif action_type == "out":
            if inventory.quantity_on_hand < quantity:
                return JsonResponse({
                    "success": False, 
                    "error": f"Insufficient stock. Available: {inventory.quantity_on_hand}"
                })
            inventory.quantity_on_hand -= quantity
            trans_type = "stockout"
        else:
            return JsonResponse({
                "success": False, 
                "error": "Invalid action type. Use 'in' or 'out'"
            })
        
        # update last_updated_at
        inventory.last_updated_at = timezone.now().date()
        inventory.save()

        #query inventory_transaction audit
        transaction = Inventory_Transaction.objects.create(
            inventory=inventory,
            trans_type=trans_type,
            quantity=quantity,
            unit_cost=inventory.product.prod_current_cost,
            user=user
        )

        return JsonResponse({
            "success": True, 
            "new_quantity": inventory.quantity_on_hand,
            "old_quantity": old_quantity,
            "transaction_id": transaction.trans_id,
            "message": f"Stock {action_type} successful"
        })
    
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False, 
            "error": "Invalid JSON"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "success": False, 
            "error": str(e)
        })
    
@csrf_exempt
def edit_product(request):
    try:
        data = json.loads(request.body)
        
        # Get data from request
        product_id = data.get("product_id")
        prod_name = data.get("prod_name")
        prod_desc = data.get("prod_desc")
        prod_unit_of_measure = data.get("prod_unit_of_measure")
        prod_current_cost = data.get("prod_current_cost")
        prod_retail_price = data.get("prod_retail_price")
        prod_reorder_threshold = data.get("prod_reorder_threshold")
        prod_is_active = data.get("prod_is_active")
        spec_name = data.get("spec_name")
        spec_value = data.get("spec_value")
        user_id = data.get("user_id")
        
        # Validate required fields
        if not product_id:
            return JsonResponse({
                "success": False,
                "error": "Product ID is required"
            })
        
        # Get user
        if not user_id:
            user_id = request.session.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User not authenticated"
            })
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            })
        
        # Get product
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Product not found"
            })
        
        # Check if prices changed
        old_cost = product.prod_current_cost
        old_retail = product.prod_retail_price
        price_changed = False
        
        if prod_current_cost is not None:
            new_cost = float(prod_current_cost)
            if new_cost != float(old_cost):
                price_changed = True
        else:
            new_cost = float(old_cost)
        
        if prod_retail_price is not None:
            new_retail = float(prod_retail_price)
            if new_retail != float(old_retail):
                price_changed = True
        else:
            new_retail = float(old_retail)
        
        # Update product fields
        if prod_name:
            product.prod_name = prod_name
        if prod_desc:
            product.prod_desc = prod_desc
        if prod_unit_of_measure:
            product.prod_unit_of_measure = prod_unit_of_measure
        if prod_current_cost is not None:
            product.prod_current_cost = new_cost
        if prod_retail_price is not None:
            product.prod_retail_price = new_retail
        if prod_reorder_threshold is not None:
            product.prod_reorder_threshold = int(prod_reorder_threshold)
        if prod_is_active is not None:
            product.prod_is_active = prod_is_active
        
        product.prod_updated_at = timezone.now()
        product.save()
        
        # Create price history record if prices changed
        if price_changed:
            Price_History.objects.create(
                product=product,
                cost_price=new_cost,
                retail_price=new_retail,
                effective_date=timezone.now().date(),
                user=user
            )
        
        # Update or create product specification
        if spec_name and spec_value:
            # Get existing specification or create new one
            spec = product.product_specification_set.first()
            if spec:
                spec.spec_name = spec_name
                spec.spec_value = spec_value
                spec.save()
            else:
                Product_Specification.objects.create(
                    product=product,
                    spec_name=spec_name,
                    spec_value=spec_value
                )
        
        return JsonResponse({
            "success": True,
            "message": "Product updated successfully",
            "price_changed": price_changed,
            "product": {
                "prod_id": product.prod_id,
                "prod_name": product.prod_name,
                "prod_desc": product.prod_desc,
                "prod_unit_of_measure": product.prod_unit_of_measure,
                "prod_current_cost": str(product.prod_current_cost),
                "prod_retail_price": str(product.prod_retail_price),
                "prod_reorder_threshold": product.prod_reorder_threshold,
                "prod_is_active": product.prod_is_active
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        })
    except ValueError as e:
        return JsonResponse({
            "success": False,
            "error": f"Invalid value: {str(e)}"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

# ari chen
@csrf_exempt
def add_product(request):
    try:
        data = json.loads(request.body)
        
        # get data
        prod_name = data.get("prod_name")
        prod_desc = data.get("prod_desc")
        prod_unit_of_measure = data.get("prod_unit_of_measure")
        prod_current_cost = data.get("prod_current_cost")
        prod_retail_price = data.get("prod_retail_price")
        prod_reorder_threshold = data.get("prod_reorder_threshold")
        prod_sku = data.get("prod_sku")
        category_id = data.get("category_id")
        branch_id = data.get("branch_id")
        specifications = data.get("specifications", [])  # Get specifications as list
        user_id = data.get("user_id")
        
        # validate fields
        if not all([prod_name, prod_current_cost, prod_retail_price, prod_reorder_threshold, prod_sku, category_id, branch_id]):
            return JsonResponse({
                "success": False,
                "error": "All required fields must be filled"
            })
        
        # user
        if not user_id:
            user_id = request.session.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User not authenticated"
            })
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            })
        
        # category
        try:
            category = Product_Category.objects.get(pk=category_id)
        except Product_Category.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Category not found"
            })
        
        # branch
        try:
            branch = Branch.objects.get(pk=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Branch not found"
            })
        
        # SKU validation
        if Product.objects.filter(prod_sku=prod_sku).exists():
            return JsonResponse({
                "success": False,
                "error": "SKU already exists"
            })
        
        # create product
        product = Product.objects.create(
            prod_name=prod_name,
            prod_desc=prod_desc or "",
            prod_unit_of_measure=prod_unit_of_measure or "pcs",
            prod_current_cost=float(prod_current_cost),
            prod_retail_price=float(prod_retail_price),
            prod_reorder_threshold=int(prod_reorder_threshold),
            prod_sku=prod_sku,
            category=category,
            prod_is_active=True
        )
        
        # create inventory record for this product in the selected branch
        inventory = Inventory.objects.create(
            product=product,
            branch=branch,
            user=user,
            quantity_on_hand=0,
            last_updated_at=timezone.now().date()
        )
        
        # create price history record
        Price_History.objects.create(
            product=product,
            cost_price=float(prod_current_cost),
            retail_price=float(prod_retail_price),
            effective_date=timezone.now().date(),
            user=user
        )
        
        # create product specifications from the list
        for spec in specifications:
            if spec.get('name') and spec.get('value'):
                Product_Specification.objects.create(
                    product=product,
                    spec_name=spec['name'],
                    spec_value=spec['value']
                )
        
        return JsonResponse({
            "success": True,
            "message": "Product added successfully",
            "product": {
                "prod_id": product.prod_id,
                "prod_name": product.prod_name,
                "prod_sku": product.prod_sku,
                "inventory_id": inventory.inventory_id
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "error": "Invalid JSON"
        })
    except ValueError as e:
        return JsonResponse({
            "success": False,
            "error": f"Invalid value: {str(e)}"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
def remove_product(request):
    try:
        data = json.loads(request.body)
        
        # get data
        product_id = data.get("product_id")
        user_id = data.get("user_id")
        
        # validate fields
        if not product_id:
            return JsonResponse({
                "success": False,
                "error": "Product ID is required"
            })
        
        # get user
        if not user_id:
            user_id = request.session.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User not authenticated"
            })
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            })
        
        # get product
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Product not found"
            })
        
        # validate product that has inventory records with quantity > 0
        inventory_with_stock = Inventory.objects.filter(
            product=product, 
            quantity_on_hand__gt=0
        ).exists()
        
        if inventory_with_stock:
            return JsonResponse({
                "success": False,
                "error": "Cannot remove product with existing stock. Please stock out all quantities first."
            })
        
        # store product info for response before deletion
        product_info = {
            "prod_id": product.prod_id,
            "prod_name": product.prod_name,
            "prod_sku": product.prod_sku
        }
        
        # delete the product
        product.delete()
        
        return JsonResponse({
            "success": True,
            "message": f"Product '{product_info['prod_name']}' has been removed successfully",
            "removed_product": product_info
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
    
def inventory(request):
    print("Inventory view called!")
    user_id = request.session.get('user_id')
    
    user = User.objects.get(pk=user_id)
    if not user_id:
        return redirect('login')
    print(user_id)
    
        
    inventories = Inventory.objects.select_related(
        'product', 
        'product__category', 
        'branch'
    ).prefetch_related(
        'product__product_specification_set'
    ).filter(product__prod_is_active=True).order_by('product__prod_name') #set main inventory to show only is_active == True
    
    categories = Product_Category.objects.all()
    branches = Branch.objects.filter(branch_is_active=True)
    
    return render(request, "main/inventory.html", {
        "section": "inventory", 
        "products": inventories, 
        "categories": categories,
        "branches": branches,
        "user_id": user_id,
        "active_page": "inventory",
        "user": user
    })
@csrf_exempt
def get_inactive_products(request):
    try:
        # Get all inactive products with their inventory information
        inactive_inventories = Inventory.objects.select_related(
            'product', 
            'branch'
        ).filter(product__prod_is_active=False).order_by('product__prod_name')
        
        inactive_products = []
        for inventory in inactive_inventories:
            inactive_products.append({
                'prod_id': inventory.product.prod_id,
                'prod_name': inventory.product.prod_name,
                'prod_sku': inventory.product.prod_sku,
                'branch_name': inventory.branch.branch_name,
                'last_updated': inventory.last_updated_at.strftime('%Y-%m-%d') if inventory.last_updated_at else 'Never',
                'inventory_id': inventory.inventory_id
            })
        
        return JsonResponse({
            "success": True,
            "inactive_products": inactive_products
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })

@csrf_exempt
def reactivate_product(request):
    try:
        data = json.loads(request.body)
        
        product_id = data.get("product_id")
        user_id = data.get("user_id")
        
        if not product_id:
            return JsonResponse({
                "success": False,
                "error": "Product ID is required"
            })
        
        # Get user
        if not user_id:
            user_id = request.session.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User not authenticated"
            })
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            })
        
        # Get product
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Product not found"
            })
        
        # Reactivate the product
        product.prod_is_active = True
        product.prod_updated_at = timezone.now()
        product.save()
        
        return JsonResponse({
            "success": True,
            "message": f"Product '{product.prod_name}' has been reactivated successfully"
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
def get_movement_history(request):
    """Get inventory movement history with date range filter"""
    try:
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        
        if not from_date or not to_date:
            return JsonResponse({
                "success": False,
                "error": "Both from_date and to_date are required"
            })
        
        # Parse dates
        from datetime import datetime
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                "success": False,
                "error": "Invalid date format. Use YYYY-MM-DD"
            })
        
        # Get user role to filter by branch if needed
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User not authenticated"
            })
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            })
        
        # Build query
        transactions_query = Inventory_Transaction.objects.select_related(
            'inventory__product',
            'inventory__branch',
            'user'
        ).filter(
            created_at__date__gte=from_date_obj,
            created_at__date__lte=to_date_obj
        )
        
        # If user is branch manager (role_id = 2), filter by their branch
        if user.role.role_id == 2:
            transactions_query = transactions_query.filter(
                inventory__branch=user.branch
            )
        
        transactions_query = transactions_query.order_by('-created_at')
        
        # Format transaction data
        transactions = []
        for trans in transactions_query:
            transactions.append({
                'trans_id': trans.trans_id,
                'created_at': trans.created_at.strftime('%Y-%m-%d %H:%M'),
                'product_name': trans.inventory.product.prod_name,
                'product_sku': trans.inventory.product.prod_sku,
                'trans_type': trans.trans_type,
                'quantity': trans.quantity,
                'unit_cost': str(trans.unit_cost),
                'user_name': f"{trans.user.user_fname} {trans.user.user_lname}",
                'branch_name': trans.inventory.branch.branch_name
            })
        
        return JsonResponse({
            "success": True,
            "transactions": transactions,
            "count": len(transactions)
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })
    
def product_management(request):
    user_id = request.session.get('user_id')
    
    if not user_id:
        return redirect('login')
    
    user = User.objects.get(pk=user_id)
    
    categories = Product_Category.objects.all()
    products = Product.objects.all()
    
    return render(request, "main/product_management.html", {
        "section": "product_management",
        "categories": categories,
        "user_id": user_id,
        "active_page": "product_management",
        "user": user,
        "products": products
    })

@csrf_exempt
def get_product(request):
    """Get product details including specifications for editing"""
    try:
        product_id = request.GET.get('product_id')
        
        if not product_id:
            return JsonResponse({
                "success": False,
                "error": "Product ID is required"
            })
        
        # Get product with related data
        product = Product.objects.select_related('category').get(pk=product_id)
        
        # Get specifications
        specifications = []
        for spec in product.product_specification_set.all():
            specifications.append({
                'spec_name': spec.spec_name,
                'spec_value': spec.spec_value
            })
        
        return JsonResponse({
            "success": True,
            "product": {
                "prod_id": product.prod_id,
                "prod_name": product.prod_name,
                "prod_desc": product.prod_desc,
                "prod_unit_of_measure": product.prod_unit_of_measure,
                "prod_current_cost": str(product.prod_current_cost),
                "prod_retail_price": str(product.prod_retail_price),
                "prod_reorder_threshold": product.prod_reorder_threshold,
                "prod_sku": product.prod_sku,
                "prod_is_active": product.prod_is_active,
                "category": {
                    "prod_cat_id": product.category.prod_cat_id,
                    "prod_cat_name": product.category.prod_cat_name
                }
            },
            "specifications": specifications
        })
        
    except Product.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Product not found"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })
    
@csrf_exempt
def get_products_not_in_inventory(request):
    """Get products that are not in inventory for a specific branch"""
    try:
        branch_id = request.GET.get('branch_id')
        
        if not branch_id:
            return JsonResponse({
                "success": False,
                "error": "Branch ID is required"
            })
        
        # Get all products
        all_products = Product.objects.filter(prod_is_active=True)
        
        # Get products already in inventory for this branch
        existing_inventory = Inventory.objects.filter(
            branch_id=branch_id,
            product__prod_is_active=True
        ).values_list('product_id', flat=True)
        
        # Filter out products already in inventory
        available_products = all_products.exclude(prod_id__in=existing_inventory)
        
        # Format product data
        products_list = []
        for product in available_products:
            products_list.append({
                'prod_id': product.prod_id,
                'prod_name': product.prod_name,
                'prod_sku': product.prod_sku,
                'prod_unit_of_measure': product.prod_unit_of_measure,
                'prod_current_cost': str(product.prod_current_cost),
                'prod_retail_price': str(product.prod_retail_price),
                'category': product.category.prod_cat_name if product.category else 'Uncategorized'
            })
        
        return JsonResponse({
            "success": True,
            "products": products_list
        })
        
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })
    
@csrf_exempt
def add_product_to_inventory(request):
    """Add an existing product to a branch's inventory"""
    try:
        data = json.loads(request.body)
        
        branch_id = data.get("branch_id")
        product_id = data.get("product_id")
        user_id = data.get("user_id")
        
        if not all([branch_id, product_id]):
            return JsonResponse({
                "success": False,
                "error": "Branch ID and Product ID are required"
            })
        
        # Get user
        if not user_id:
            user_id = request.session.get('user_id')
        
        if not user_id:
            return JsonResponse({
                "success": False,
                "error": "User not authenticated"
            })
        
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "User not found"
            })
        
        # Get branch and product
        try:
            branch = Branch.objects.get(pk=branch_id)
        except Branch.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Branch not found"
            })
        
        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                "success": False,
                "error": "Product not found"
            })
        
        # Check if product is already in inventory for this branch
        if Inventory.objects.filter(product=product, branch=branch).exists():
            return JsonResponse({
                "success": False,
                "error": "This product is already in this branch's inventory"
            })
        
        # Create inventory record with quantity 0
        inventory = Inventory.objects.create(
            product=product,
            branch=branch,
            user=user,
            quantity_on_hand=0,
            last_updated_at=timezone.now().date()
        )
        
        return JsonResponse({
            "success": True,
            "message": f"'{product.prod_name}' has been added to {branch.branch_name} inventory",
            "inventory_id": inventory.inventory_id
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