from django.contrib import admin
from .models import (
    RFQ, RFQ_Item, Supplier, Supplier_Product,
    RFQ_Supplier, Supplier_Category,
    Supplier_Quotation, Supplier_Quotation_Item,
    Purchase_Order, Purchase_Order_Item
)

# ============================
# RFQ Models
# ============================
@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ("rfq_id", "rfq_created_at", "rfq_created_by")
    search_fields = ("rfq_id",)
    list_filter = ("rfq_created_at",)


@admin.register(RFQ_Item)
class RFQItemAdmin(admin.ModelAdmin):
    list_display = ("rfq_item_id", "get_requisition", "product", "rfq_item_req_qty", "rfq_item_req_uom")
    search_fields = ("requisition_item__requisition__req_id", "product__prod_name")
    list_filter = ("product",)

    def get_requisition(self, obj):
        """Display the Requisition ID linked to this RFQ_Item"""
        return f"REQ-{obj.requisition_item.requisition.req_id}"
    get_requisition.short_description = 'Requisition'


# ============================
# Supplier & Related
# ============================
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("sup_id", "sup_name", "sup_contact_person", "sup_phone", "sup_is_active", "sup_created_at")
    search_fields = ("sup_name", "sup_contact_person", "sup_phone")
    list_filter = ("sup_is_active",)


@admin.register(Supplier_Product)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ("sup_prod_id", "supplier", "product", "sup_prod_code", "sup_prod_unit_price", "sup_prod_is_active")
    search_fields = ("sup_prod_code", "supplier__sup_name", "product__prod_name")
    list_filter = ("sup_prod_is_active", "supplier")


@admin.register(RFQ_Supplier)
class RFQSupplierAdmin(admin.ModelAdmin):
    list_display = ("rfq_sup_id", "rfq", "supplier", "rfq_date_sent", "date_responded")
    list_filter = ("supplier",)
    search_fields = ("rfq__req_id", "supplier__sup_name")


@admin.register(Supplier_Category)
class SupplierCategoryAdmin(admin.ModelAdmin):
    list_display = ("sup_cat_id", "supplier", "prod_cat")
    search_fields = ("supplier__sup_name", "prod_cat__prod_cat_name")


# ============================
# Supplier Quotation
# ============================
@admin.register(Supplier_Quotation)
class SupplierQuotationAdmin(admin.ModelAdmin):
    list_display = ("sup_qtn_id", "rfq_supplier", "sup_qtn_total_cost", "sup_qtn_eta", "sup_qtn_valid_until", "sup_qtn_created_at")
    list_filter = ("sup_qtn_valid_until", "sup_qtn_eta")
    search_fields = ("rfq_supplier__supplier__sup_name",)


@admin.register(Supplier_Quotation_Item)
class SupplierQuotationItemAdmin(admin.ModelAdmin):
    list_display = ("sup_qtn_item_id", "supplier_quotation", "product", "sup_qtn_item_unit_price")
    search_fields = ("product__prod_name",)
    list_filter = ("supplier_quotation",)


# ============================
# Purchase Order
# ============================
@admin.register(Purchase_Order)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ("po_id", "supplier", "user", "branch", "po_main_status", "po_total_amount", "po_created_at")
    list_filter = ("po_main_status", "supplier", "branch")
    search_fields = ("po_id", "supplier__sup_name")


@admin.register(Purchase_Order_Item)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ("po_item_id", "purchase_order", "product", "po_item_ordered_quantity", "po_item_unit_price", "po_item_line_total")
    search_fields = ("purchase_order__po_id", "product__prod_name")
    list_filter = ("purchase_order",)
