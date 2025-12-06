from django.contrib import admin
from django.utils.html import format_html
from .models import *

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = [
        'delivery_id',
        'purchase_order',
        'requisition',
        'delivery_status',
        'delivery_date',
        'delivered_by',
        'inspected_by',
        'created_at'
    ]
    
    list_filter = [
        'delivery_status',
        'delivery_date',
        'created_at',
        'delivered_by',
        'inspected_by'
    ]
    
    search_fields = [
        'delivery_id',
        'purchase_order__po_id',
        'requisition__req_id',
        'delivery_notes',
        'delivered_by__sup_name',
        'inspected_by__username'
    ]
    
    list_editable = ['delivery_status']
    
    raw_id_fields = [
        'purchase_order',
        'requisition',
        'delivered_by',
        'inspected_by'
    ]
    
    readonly_fields = [
        'delivered_at',
        'created_at',
    ]
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Delivery Information', {
            'fields': (
                'purchase_order',
                'requisition',
                'delivery_status'
            )
        }),
        ('Delivery Dates', {
            'fields': (
                'delivery_date',
                'delivered_at'
            )
        }),
        ('Personnel', {
            'fields': (
                'delivered_by',
                'inspected_by'
            )
        }),
        ('Additional Information', {
            'fields': (
                'delivery_notes',
                'created_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize database queries by selecting related objects"""
        return super().get_queryset(request).select_related(
            'purchase_order',
            'requisition',
            'delivered_by',
            'inspected_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Set inspected_by to current user if not set"""
        if not obj.inspected_by and not change:
            obj.inspected_by = request.user
        super().save_model(request, obj, form, change)
    
    # Custom admin actions
    actions = ['mark_as_delivered', 'mark_as_in_transit']
    
    def mark_as_delivered(self, request, queryset):
        """Custom admin action to mark deliveries as delivered"""
        updated = queryset.update(delivery_status='delivered')
        self.message_user(request, f'{updated} deliveries marked as delivered.')
    mark_as_delivered.short_description = "Mark selected deliveries as delivered"
    
    def mark_as_in_transit(self, request, queryset):
        """Custom admin action to mark deliveries as in transit"""
        updated = queryset.update(delivery_status='to_be_delivered')
        self.message_user(request, f'{updated} deliveries marked as to be delivered.')
    mark_as_in_transit.short_description = "Mark selected deliveries as to be delivered"


@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = [
        'delivery_item_id',
        'delivery',
        'product',
        'branch_display',  # Added branch display
        'purchase_order_item',
        'quantity_ordered',
        'quantity_delivered',
        'quantity_accepted',
        'quantity_rejected_display',
        'created_at'
    ]
    
    list_filter = [
        'delivery',
        'created_at',
        'purchase_order_item',
        'branch',  # Added branch filter
    ]
    
    search_fields = [
        'delivery__delivery_id',
        'product__prod_name',
        'purchase_order_item__po_item_id',
        'inspection_notes',
        'branch__branch_name',  # Added branch search
    ]
    
    list_editable = [
        'quantity_delivered',
        'quantity_accepted'
    ]
    
    raw_id_fields = [
        'delivery',
        'purchase_order_item',
        'product',
        'branch',  # Added branch as raw_id field
    ]
    
    readonly_fields = [
        'created_at',
        'quantity_rejected_display'
    ]
    
    fieldsets = (
        ('Item Information', {
            'fields': (
                'delivery',
                'purchase_order_item',
                'product',
                'branch',  # Added branch to fields
            )
        }),
        ('Quantities', {
            'fields': (
                'quantity_ordered',
                'quantity_delivered',
                'quantity_accepted',
                'quantity_rejected_display'
            )
        }),
        ('Inspection Details', {
            'fields': (
                'inspection_notes',
                'created_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def branch_display(self, obj):
        """Display branch information"""
        if obj.branch:
            return obj.branch.branch_name
        return "No branch assigned"
    branch_display.short_description = 'Branch'
    branch_display.admin_order_field = 'branch__branch_name'
    
    def quantity_rejected_display(self, obj):
        """Display rejected quantity with color coding"""
        rejected = obj.quantity_rejected
        color = 'red' if rejected > 0 else 'green'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            rejected
        )
    quantity_rejected_display.short_description = 'Quantity Rejected'
    
    def get_queryset(self, request):
        """Optimize database queries by selecting related objects"""
        return super().get_queryset(request).select_related(
            'delivery',
            'purchase_order_item',
            'product',
            'branch',  # Added branch to select_related
            'purchase_order_item__product'
        )
    
    def save_model(self, request, obj, form, change):
        """Ensure quantities are valid before saving"""
        if obj.quantity_delivered < 0:
            obj.quantity_delivered = 0
        if obj.quantity_accepted < 0:
            obj.quantity_accepted = 0
        if obj.quantity_accepted > obj.quantity_delivered:
            obj.quantity_accepted = obj.quantity_delivered
        
        super().save_model(request, obj, form, change)
    
    # Custom admin actions
    actions = ['accept_all_items', 'reset_quantities', 'assign_to_main_branch']
    
    def accept_all_items(self, request, queryset):
        """Custom admin action to accept all delivered items"""
        for item in queryset:
            item.quantity_accepted = item.quantity_delivered
            item.save()
        self.message_user(request, f'{queryset.count()} items accepted.')
    accept_all_items.short_description = "Accept all delivered quantities for selected items"
    
    def reset_quantities(self, request, queryset):
        """Custom admin action to reset delivered and accepted quantities"""
        updated = queryset.update(quantity_delivered=0, quantity_accepted=0)
        self.message_user(request, f'{updated} items quantities reset to zero.')
    reset_quantities.short_description = "Reset delivered and accepted quantities to zero"
    
    def assign_to_main_branch(self, request, queryset):
        """Custom admin action to assign items to main branch from purchase order"""
        updated_count = 0
        for item in queryset:
            if item.purchase_order_item and item.purchase_order_item.purchase_order:
                main_branch = item.purchase_order_item.purchase_order.branch
                item.branch = main_branch
                item.save()
                updated_count += 1
        self.message_user(request, f'{updated_count} items assigned to their purchase order branch.')
    assign_to_main_branch.short_description = "Assign to purchase order branch"


# Your existing admin registrations remain the same
@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ('rfq_id', 'rfq_created_at', 'rfq_created_by')
    list_filter = ('rfq_created_at',)
    search_fields = ('rfq_id', 'rfq_created_by__req_id')
    date_hierarchy = 'rfq_created_at'

@admin.register(RFQ_Item)
class RFQ_ItemAdmin(admin.ModelAdmin):
    list_display = ('rfq_item_id', 'requisition', 'product', 'rfq_item_req_qty', 'rfq_item_req_uom')
    list_filter = ('rfq_item_req_uom',)
    search_fields = ('requisition__req_id', 'product__prod_name')
    raw_id_fields = ('requisition', 'product')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('sup_id', 'sup_name', 'sup_phone', 'sup_email', 'sup_contact_person', 'sup_is_active', 'sup_created_at')
    list_filter = ('sup_is_active', 'sup_created_at')
    search_fields = ('sup_name', 'sup_phone', 'sup_email', 'sup_contact_person')
    list_editable = ('sup_is_active',)
    date_hierarchy = 'sup_created_at'

@admin.register(Supplier_Product)
class Supplier_ProductAdmin(admin.ModelAdmin):
    list_display = ('sup_prod_id', 'sup_prod_code', 'supplier', 'product', 'sup_prod_unit_price', 'sup_prod_is_active', 'sup_prod_last_updated_price')
    list_filter = ('sup_prod_is_active', 'sup_prod_last_updated_price')
    search_fields = ('sup_prod_code', 'supplier__sup_name', 'product__prod_name')
    list_editable = ('sup_prod_unit_price', 'sup_prod_is_active')
    raw_id_fields = ('supplier', 'product')

@admin.register(RFQ_Supplier)
class RFQ_SupplierAdmin(admin.ModelAdmin):
    list_display = ('rfq_sup_id', 'rfq', 'supplier', 'rfq_date_sent', 'date_responded')
    list_filter = ('rfq_date_sent', 'date_responded')
    search_fields = ('rfq__req_id', 'supplier__sup_name')
    raw_id_fields = ('rfq', 'supplier')
    date_hierarchy = 'rfq_date_sent'

@admin.register(Supplier_Category)
class Supplier_CategoryAdmin(admin.ModelAdmin):
    list_display = ('sup_cat_id', 'supplier', 'prod_cat')
    list_filter = ('prod_cat',)
    search_fields = ('supplier__sup_name', 'prod_cat__prod_cat_name')
    raw_id_fields = ('supplier', 'prod_cat')

@admin.register(Supplier_Quotation)
class Supplier_QuotationAdmin(admin.ModelAdmin):
    list_display = ('sup_qtn_id', 'rfq_supplier', 'sup_qtn_total_cost', 'sup_qtn_eta', 'sup_qtn_valid_until', 'sup_qtn_created_at')
    list_filter = ('sup_qtn_eta', 'sup_qtn_valid_until', 'sup_qtn_created_at')
    search_fields = ('rfq_supplier__supplier__sup_name', 'sup_qtn_id')
    raw_id_fields = ('rfq_supplier',)
    date_hierarchy = 'sup_qtn_created_at'

@admin.register(Supplier_Quotation_Item)
class Supplier_Quotation_ItemAdmin(admin.ModelAdmin):
    list_display = ('sup_qtn_item_id', 'supplier_quotation', 'rfq_item', 'product', 'sup_qtn_item_unit_price')
    search_fields = ('supplier_quotation__sup_qtn_id', 'product__prod_name')
    raw_id_fields = ('supplier_quotation', 'rfq_item', 'product')

@admin.register(Purchase_Order)
class Purchase_OrderAdmin(admin.ModelAdmin):
    list_display = ('po_id', 'supplier', 'requisition', 'user', 'branch', 'po_main_status', 'po_substatus', 'po_date_sent_to_sup', 'po_total_amount', 'po_created_at')
    list_filter = ('po_main_status', 'po_substatus', 'po_date_sent_to_sup', 'po_created_at', 'branch')
    search_fields = ('po_id', 'supplier__sup_name', 'requisition__req_id')
    list_editable = ('po_main_status', 'po_substatus')
    raw_id_fields = ('supplier', 'requisition', 'user', 'branch')
    date_hierarchy = 'po_created_at'

@admin.register(Purchase_Order_Item)
class Purchase_Order_ItemAdmin(admin.ModelAdmin):
    list_display = ('po_item_id', 'purchase_order', 'product', 'po_item_ordered_quantity', 'po_item_unit_price', 'po_item_line_total')
    search_fields = ('purchase_order__po_id', 'product__prod_name')
    raw_id_fields = ('purchase_order', 'product')

@admin.register(Discrepancy)
class DiscrepancyAdmin(admin.ModelAdmin):
    list_display = [
        'disc_id', 
        'purchase_order', 
        'product', 
        'disc_condition', 
        'disc_quantity', 
        'inspected_by', 
        'inspection_date'
    ]
    
    list_filter = [
        'disc_condition',
        'inspection_date',
        'inspected_by',
        'purchase_order'
    ]
    
    search_fields = [
        'disc_id',
        'product__prod_name',
        'purchase_order__po_id',
        'notes',
        'inspected_by__username'
    ]
    
    readonly_fields = ['inspection_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'purchase_order', 
                'po_item', 
                'product',
                'disc_condition',
                'disc_quantity'
            )
        }),
        ('Condition Details', {
            'fields': (
                'notes',
                'damage_type', 
                'missing_reason',
                'excess_action',
                'correct_item'
            ),
            'description': 'Fill only the field relevant to the selected condition'
        }),
        ('Inspection Details', {
            'fields': (
                'inspected_by',
                'inspection_date'
            )
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        """
        Dynamically show/hide condition-specific fields based on selected condition
        """
        fieldsets = super().get_fieldsets(request, obj)
        
        if obj:
            # Hide irrelevant condition fields based on current condition
            condition_fields = {
                'good': ['notes'],
                'damaged': ['damage_type'],
                'missing': ['missing_reason'],
                'excess': ['excess_action'],
                'wrong': ['correct_item']
            }
            
            relevant_fields = condition_fields.get(obj.disc_condition, [])
            
            # Modify the condition details fieldset to only show relevant fields
            for fieldset in fieldsets:
                if fieldset[0] == 'Condition Details':
                    fieldset[1]['fields'] = relevant_fields
                    break
        
        return fieldsets
    
    def save_model(self, request, obj, form, change):
        """
        Automatically set the inspected_by field to the current user
        when creating a new discrepancy
        """
        if not obj.pk:  # If object is being created
            obj.inspected_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """
        Optimize database queries by selecting related objects
        """
        return super().get_queryset(request).select_related(
            'purchase_order',
            'product',
            'inspected_by'
        )
    
    def get_readonly_fields(self, request, obj=None):
        """
        Make inspection_date and inspected_by read-only after creation
        """
        if obj:  # Editing an existing object
            return self.readonly_fields + ['inspected_by']
        return self.readonly_fields

    # Custom admin actions
    actions = ['mark_as_resolved']
    
    def mark_as_resolved(self, request, queryset):
        """
        Custom admin action to mark discrepancies as resolved
        """
        updated = queryset.update(disc_condition='good')
        self.message_user(request, f'{updated} discrepancies marked as resolved.')
    mark_as_resolved.short_description = "Mark selected discrepancies as resolved"

@admin.register(Receiving_Memo)
class Receiving_MemoAdmin(admin.ModelAdmin):
    list_display = ('rm_id', 'delivery', 'rm_date', 'generated_by', 'created_at')
    list_filter = ('rm_date', 'created_at')
    search_fields = ('delivery__delivery_id', 'generated_by__username')
    raw_id_fields = ('delivery', 'generated_by')
    date_hierarchy = 'rm_date'

@admin.register(Acknowledgment_Receipt)
class Acknowledgment_ReceiptAdmin(admin.ModelAdmin):
    list_display = ('ar_id', 'ar_number', 'delivery', 'ar_date', 'generated_by', 'created_at')
    list_filter = ('ar_date', 'created_at')
    search_fields = ('ar_number', 'delivery__delivery_id', 'generated_by__username')
    raw_id_fields = ('delivery', 'generated_by')
    date_hierarchy = 'ar_date'

@admin.register(Discrepancy_Report)
class Discrepancy_ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'delivery', 'report_type', 'status', 'reported_by', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('report_id', 'delivery__delivery_id', 'reported_by__username')
    list_editable = ('status',)
    raw_id_fields = ('delivery', 'reported_by')
    date_hierarchy = 'created_at'

@admin.register(Return_Request)
class Return_RequestAdmin(admin.ModelAdmin):
    list_display = ('return_id', 'delivery_product', 'return_reason_preview', 'return_date', 'return_status', 'quantity_to_return', 'requested_by', 'created_at')
    list_filter = ('return_status', 'return_date', 'created_at')
    search_fields = ('return_id', 'delivery_product__product__prod_name', 'requested_by__username')
    list_editable = ('return_status', 'quantity_to_return')
    raw_id_fields = ('delivery_product', 'requested_by')
    date_hierarchy = 'return_date'
    
    def return_reason_preview(self, obj):
        return obj.return_reason[:50] + '...' if len(obj.return_reason) > 50 else obj.return_reason
    return_reason_preview.short_description = 'Return Reason'