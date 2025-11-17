from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..models import Inventory, Product_Category, Product_Specification, Inventory_Transaction, User, Product, Price_History
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
    
def inventory(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
        
    inventories = Inventory.objects.select_related(
        'product', 
        'product__category', 
        'branch'
    ).prefetch_related(
        'product__product_specification_set'
    ).all().order_by('product__prod_name')
    
    categories = Product_Category.objects.all()
    
    return render(request, "main/top_management_dashboard.html", {
        "section": "inventory", 
        "products": inventories, 
        "categories": categories,
        "user_id": user_id  
    })






















   