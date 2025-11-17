from django.contrib import admin
from .models import Role, Branch, User, Product_Category, Product, Inventory, Inventory_Transaction, Product_Specification, Price_History

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_id', 'role_name', 'role_description')
    search_fields = ('role_name',)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_id', 'branch_name', 'branch_address', 'branch_phone', 'branch_email', 'branch_is_active')
    search_fields = ('branch_name', 'branch_email')
    list_filter = ('branch_is_active',)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'user_id', 'username', 'user_email', 'user_fname', 'user_lname',
        'role', 'branch', 'is_active', 'date_joined', 'last_login'
    )
    list_filter = ('role', 'branch', 'is_active')
    search_fields = ('username', 'user_email', 'user_fname', 'user_lname')

@admin.register(Product_Category)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('prod_cat_id', 'prod_cat_name', 'prod_cat_desc')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('prod_id', 'prod_name', 'prod_desc', 'prod_unit_of_measure', 'prod_current_cost', 'prod_retail_price', 'prod_reorder_threshold', 'prod_is_active', 'prod_created_at', 'prod_updated_at', 'prod_sku')

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display=('inventory_id', 'quantity_on_hand', 'last_updated_at')

@admin.register(Inventory_Transaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display=('trans_id', 'trans_type', 'quantity', 'unit_cost', 'created_at')

@admin.register(Price_History)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display=('price_id', 'cost_price', 'retail_price', 'effective_date')

@admin.register(Product_Specification)
class ProductSpecificationAdmin(admin.ModelAdmin):
    list_display=('prod_spec_id', 'spec_name', 'spec_value')
