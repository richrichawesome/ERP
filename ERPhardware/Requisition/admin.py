# Requisition/admin.py

from django.contrib import admin
from .models import Requisition, RequisitionItem, RequisitionStatusTimeline

# Register your models here.

class RequisitionItemInline(admin.TabularInline):
    """Inline editing for Requisition Items"""
    model = RequisitionItem
    extra = 1  # Number of empty forms to display
    fields = ('product', 'quantity', 'uom')
    readonly_fields = ('product', 'quantity', 'uom')

class RequisitionStatusTimelineInline(admin.TabularInline):
    """Inline editing for Status Timeline"""
    model = RequisitionStatusTimeline
    extra = 0  # No empty forms by default
    readonly_fields = ('changed_at', 'user', 'main_status', 'sub_status', 'comment')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Prevent adding timeline entries from admin (they should be system-generated)
        return False

@admin.register(Requisition)
class RequisitionAdmin(admin.ModelAdmin):
    """Admin interface for Requisition model"""
    list_display = (
        'req_id', 
        'get_requisition_number',
        'requested_by', 
        'branch', 
        'sender_user',          # NEW
        'sender_branch',        # NEW
        'req_type', 
        'req_main_status',
        'req_substatus',
        'req_date_required',
        'req_requested_date'
    )
    
    list_filter = (
        'req_type',
        'req_main_status',
        'req_substatus',
        'branch',
        'sender_branch', 
        'req_requested_date'
    )
    
    search_fields = (
        'req_id',
        'requested_by__username',
        'requested_by__user_fname',
        'requested_by__user_lname',
        'branch__branch_name',
        'sender_user__username',        # NEW
        'sender_user__user_fname',      # NEW
        'sender_user__user_lname',      # NEW
        'sender_branch__branch_name'    # NEW
    )
    
    readonly_fields = ('req_id', 'req_requested_date')
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'req_id',
                'requested_by',
                'branch',
                'sender_user',        # NEW
                'sender_branch',      # NEW
                'req_type'
            )
        }),
        ('Status Information', {
            'fields': (
                'req_main_status',
                'req_substatus',
                'req_requested_date',
                'req_approval_date'
            )
        }),
        ('Additional Information', {
            'fields': (
                'req_notes',
                'req_rejection_reason',
                'delivery_receipt_num',
                'rf_file',  # FIXED: Changed from 'rfq_pdf' to 'rf_file'
                'approved_by'
            )
        }),
    )
    
    inlines = [RequisitionItemInline, RequisitionStatusTimelineInline]
    
    def get_requisition_number(self, obj):
        return f"REQ-{obj.req_id:06d}"
    get_requisition_number.short_description = 'Requisition Number'
    get_requisition_number.admin_order_field = 'req_id'

@admin.register(RequisitionItem)
class RequisitionItemAdmin(admin.ModelAdmin):
    """Admin interface for RequisitionItem model"""
    list_display = (
        'req_item_id',
        'requisition',
        'product',
        'quantity',
        'uom'
    )
    
    list_filter = (
        'uom',
        'requisition__req_type',
    )
    
    search_fields = (
        'product__prod_name',
        'requisition__req_id',
    )
    
    readonly_fields = ('req_item_id',)

@admin.register(RequisitionStatusTimeline)
class RequisitionStatusTimelineAdmin(admin.ModelAdmin):
    """Admin interface for RequisitionStatusTimeline model"""
    list_display = (
        'history_id',
        'requisition',
        'main_status',
        'sub_status',
        'user',
        'changed_at'
    )
    
    list_filter = (
        'main_status',
        'sub_status',
        'changed_at',
    )
    
    search_fields = (
        'requisition__req_id',
        'user__username',
        'comment'
    )
    
    readonly_fields = ('history_id', 'changed_at')
    
    def has_add_permission(self, request):
        # Prevent manually adding timeline entries
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deleting timeline entries (they're historical records)
        return False