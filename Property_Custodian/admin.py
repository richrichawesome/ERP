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