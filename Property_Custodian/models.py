from django.db import models
from django.utils import timezone
from ERP.models import *
from Requisition.models import *
from Requisition.constants import *
from decimal import *
from Purchasing.models import *
    
class Discrepancy(models.Model):
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('missing', 'Missing'),
        ('excess', 'Excess'),
        ('wrong', 'Wrong Item'),
    ]
    
    disc_id = models.AutoField(primary_key=True)
    purchase_order = models.ForeignKey('Purchase_Order', on_delete=models.CASCADE)
    po_item = models.ForeignKey('Purchase_Order_Item', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    # Condition and quantities
    disc_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    disc_quantity = models.IntegerField()
    
    # Additional details based on condition
    notes = models.TextField(blank=True, null=True)  # For 'good' condition
    damage_type = models.TextField(blank=True, null=True)  # For 'damaged'
    missing_reason = models.TextField(blank=True, null=True)  # For 'missing'
    excess_action = models.TextField(blank=True, null=True)  # For 'excess'
    correct_item = models.TextField(blank=True, null=True)  # For 'wrong' item
    
    # Tracking
    inspected_by = models.ForeignKey(User, on_delete=models.CASCADE)
    inspection_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inspection_discrepancy'
        ordering = ['-inspection_date']
    
    def __str__(self):
        return f"Inspection {self.disc_id} - {self.disc_condition} - {self.product.prod_name}"

# class Purchase_Order_Item(models.Model):
#     po_item_id = models.AutoField(primary_key=True)
#     purchase_order = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE)  # PO_ID
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)               # PROD_ID

#     po_item_ordered_quantity = models.IntegerField()                             
#     po_item_unit_price = models.DecimalField(max_digits=12, decimal_places=2)    
#     po_item_line_total = models.DecimalField(max_digits=14, decimal_places=2)     

#     # ADD THIS FIELD to link to requisition item mao ni gamit para 1 po multiple reqs
#     requisition_item = models.ForeignKey(
#         'Requisition.RequisitionItem', 
#         on_delete=models.SET_NULL, 
#         null=True, 
#         blank=True,
#         related_name='po_items'
#     )
    
#     def __str__(self):
#         return f"{self.product.prod_name} - {self.po_item_ordered_quantity}"
class Delivery(models.Model):
    DELIVERY_STATUS_CHOICES = [
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
    ]
    delivery_id = models.AutoField(primary_key=True)
    # Timestamps
    delivery_date = models.DateTimeField(null=True, blank=True)  # Actual delivery date
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    #status
    delivery_status = models.CharField(max_length=20, choices=DELIVERY_STATUS_CHOICES, default='to_be_delivered')
    delivery_notes = models.TextField(blank=True, null=True)
    
    # Foreign Keys
    purchase_order = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE)  # Direct link to requisition
    
    delivered_by = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='deliveries_made')
    inspected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspected_deliveries')

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Deliveries'


    
    def save(self, *args, **kwargs):
        # Auto-set delivered_at when status changes
        if self.pk:
            old_instance = Delivery.objects.get(pk=self.pk)
            if old_instance.delivery_status != self.delivery_status and self.delivery_status == 'delivered':
                self.delivered_at = timezone.now()
                if not self.delivery_date:
                    self.delivery_date = timezone.now()
        elif self.delivery_status == 'delivered':
            self.delivered_at = timezone.now()
            if not self.delivery_date:
                self.delivery_date = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_total_ordered(self):
        """Get total quantity ordered across all items"""
        return self.items.aggregate(total=models.Sum('quantity_ordered'))['total'] or 0
    
    def get_total_accepted(self):
        """Get total quantity accepted (good items)"""
        return self.items.aggregate(total=models.Sum('quantity_accepted'))['total'] or 0
    
    def get_total_rejected(self):
        """Get total quantity rejected (bad items)"""
        return self.items.aggregate(total=models.Sum('quantity_rejected'))['total'] or 0
    
class DeliveryItem(models.Model):
    delivery_item_id = models.AutoField(primary_key=True)

    # Links
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name='items')
    purchase_order_item = models.ForeignKey(Purchase_Order_Item, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)

    # Quantities
    quantity_ordered = models.IntegerField()
    quantity_delivered = models.IntegerField(default=0)
    quantity_accepted = models.IntegerField(default=0)
    
    inspection_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        unique_together = ['delivery', 'purchase_order_item']

    def __str__(self):
        return f"{self.product.prod_name} - PO Item {self.purchase_order_item.po_item_id}"
    
    @property
    def quantity_rejected(self):
        """Calculate rejected quantity automatically"""
        return self.quantity_delivered - self.quantity_accepted
    
    def inspect_items(self, accepted_qty, inspection_notes="", inspected_by_user=None):
        """Simple inspection method"""
        if accepted_qty > self.quantity_delivered:
            accepted_qty = self.quantity_delivered
        
        self.quantity_accepted = accepted_qty
        self.inspection_notes = inspection_notes
        self.save()
        
        # Update delivery inspected_by if provided
        if inspected_by_user:
            self.delivery.inspected_by = inspected_by_user
            self.delivery.save()
        
        # Create discrepancy for rejected items
        rejected_qty = self.quantity_rejected
        if rejected_qty > 0:
            Discrepancy.objects.create(
                purchase_order=self.delivery.purchase_order,
                po_item=self.purchase_order_item,
                product=self.product,
                disc_condition='damaged' if 'damaged' in inspection_notes.lower() else 'missing',
                disc_quantity=rejected_qty,
                notes=f"Rejected: {inspection_notes}",
                inspected_by=inspected_by_user
            )

class Receiving_Memo(models.Model):
    rm_id = models.AutoField(primary_key=True)
    rm_date = models.DateTimeField()
    rm_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Foreign Keys
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, null=True, blank=True)  # Made optional
    purchase_order = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE, null=True, blank=True)  # Added
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, null=True, blank=True)  # Added
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_receiving_memos')
    
    # PDF storage
    rm_pdf = models.FileField(upload_to='receiving_memos/', null=True, blank=True)

    class Meta:
        db_table = 'receiving_memo'
        ordering = ['-created_at']

    def __str__(self):
        return f"RM-{self.rm_id} - {self.rm_date.strftime('%Y-%m-%d')}"

class Acknowledgment_Receipt(models.Model):
    ar_id = models.AutoField(primary_key=True)
    ar_number = models.CharField(max_length=50, unique=True)
    ar_date = models.DateTimeField()
    ar_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Foreign Keys
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_acknowledgment_receipts')

    def __str__(self):
        return f"AR {self.ar_number}"

class Discrepancy_Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('quantity', 'Quantity Discrepancy'),
        ('quality', 'Quality Issue'),
        ('damage', 'Damaged Goods'),
        ('missing', 'Missing Items'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    report_id = models.AutoField(primary_key=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Foreign Keys
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE)
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_discrepancies')

    def __str__(self):
        return f"Report {self.report_id} - {self.report_type}"

class Return_Request(models.Model):
    RETURN_STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    return_id = models.AutoField(primary_key=True)
    return_reason = models.TextField()
    return_date = models.DateTimeField()
    return_status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='requested')
    quantity_to_return = models.IntegerField()
    return_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Foreign Keys
    delivery_product = models.ForeignKey(DeliveryItem, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requested_returns')

    def __str__(self):
        return f"Return {self.return_id} - {self.return_status}"