from django.db import models
from django.utils import timezone
from ERP.models import *
from Requisition.models import *
from Requisition.constants import *
from decimal import *

# purchasing staff models.. (temporary)
class RFQ(models.Model):
    rfq_id = models.AutoField(primary_key=True)
    rfq_created_at = models.DateTimeField(auto_now_add=True)
    rfq_created_by = models.ForeignKey(Requisition, on_delete=models.CASCADE)
    def __str__(self):
        return self.rfq_id
    


class RFQ_Item(models.Model):
    rfq_item_id = models.AutoField(primary_key=True)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rfq_item_req_qty = models.IntegerField(default=0)
    rfq_item_req_uom = models.CharField(max_length=20)


class Supplier(models.Model):
    sup_id = models.AutoField(primary_key=True)
    sup_name = models.CharField(max_length=255)
    sup_phone = models.CharField(max_length=50)
    sup_email = models.CharField(max_length=255, null=True, blank=True)
    sup_address = models.TextField(null=True, blank=True)
    sup_contact_person = models.CharField(max_length=50, default="Unknown")

    sup_payment_terms = models.TextField(null=True, blank=True)
    sup_delivery_terms = models.TextField(null=True, blank=True)

    sup_is_active = models.BooleanField(default=True)

    sup_created_at = models.DateTimeField(auto_now_add=True)
    sup_updated_at = models.DateTimeField(auto_now=True)

    def  __str__(self):
        return self.sup_name
    
# associative entity of Supplier and Product
class Supplier_Product(models.Model):
    sup_prod_id = models.AutoField(primary_key=True)
    sup_prod_code = models.CharField(max_length=50)
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)  # Added reference to Product
    
    sup_prod_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    sup_prod_last_updated_price = models.DateTimeField(auto_now_add=True)
    sup_prod_is_active = models.BooleanField(default=True)

    def __str__(self):  # fixed method name
        return f"{self.supplier.sup_name} - {self.product.prod_name} ({self.sup_prod_code})"
    
#associative entity of Supplier and RFQ
class RFQ_Supplier(models.Model):
    rfq_sup_id = models.AutoField(primary_key=True)
    rfq = models.ForeignKey(Requisition, on_delete=models.CASCADE) 
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)  
    rfq_date_sent = models.DateTimeField(auto_now_add=True)  
    date_responded = models.DateTimeField(null=True, blank=True) 

    def __str__(self):
        return f"{self.rfq_sup_id} - {self.supplier}"


# associative entity of Supplier and Product_Category
class Supplier_Category(models.Model):
    sup_cat_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    prod_cat = models.ForeignKey(Product_Category, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.supplier.sup_name} - {self.prod_cat.prod_cat_name}"

class Supplier_Quotation(models.Model):
    sup_qtn_id = models.AutoField(primary_key=True)
    rfq_supplier = models.ForeignKey(RFQ_Supplier, on_delete=models.CASCADE)  # RFQ_SUP_ID
    sup_qtn_total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    sup_qtn_eta = models.DateField(null=True, blank=True)
    sup_qtn_valid_until = models.DateField(null=True, blank=True)
    sup_qtn_pdf = models.FileField(upload_to='supplier_quotations/', null=True, blank=True)
    sup_qtn_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quotation {self.sup_qtn_id} for {self.rfq_supplier.supplier}"



class Supplier_Quotation_Item(models.Model):
    sup_qtn_item_id = models.AutoField(primary_key=True)
    supplier_quotation = models.ForeignKey(Supplier_Quotation, on_delete=models.CASCADE)  # SUP_QTN_ID
    rfq_item = models.ForeignKey(RFQ_Item, on_delete=models.CASCADE)                      # RFQ_ITEM_ID
    product = models.ForeignKey(Product, on_delete=models.CASCADE)                       # PROD_ID
    sup_qtn_item_unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"QuotationItem {self.sup_qtn_item_id} - {self.product}"
    
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
    
class Purchase_Order(models.Model):
    po_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)             # SUP_ID
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE)       # REQ_ID
    user = models.ForeignKey(User, on_delete=models.CASCADE)                     # USER_ID
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)                 # BRANCH_ID
    
    po_main_status = models.CharField(max_length=50, choices=REQ_MAIN_STATUS_CHOICES, default="PO_APPROVAL")   
    po_substatus = models.CharField(max_length=100, choices=REQ_SUBSTATUS_CHOICES, default="NONE") 

                                
    po_date_sent_to_sup = models.DateField(null=True, blank=True)               
    po_eta = models.DateField(null=True, blank=True)                             
    
    po_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    po_total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    po_approval_date = models.DateField(null=True, blank=True)
    po_rejection_reason = models.TextField(null=True, blank=True)
    
    po_created_at = models.DateTimeField(auto_now_add=True)
    po_pdf = models.FileField(upload_to='po_pdfs/', null=True, blank=True)

    rfq_supplier = models.ForeignKey(RFQ_Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    supplier_quotation = models.ForeignKey(Supplier_Quotation, null=True, blank=True, on_delete=models.SET_NULL)


    def __str__(self):
        return f"PO-{self.po_id} | {self.supplier.sup_name}"

class Purchase_Order_Item(models.Model):
    po_item_id = models.AutoField(primary_key=True)
    purchase_order = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE)  # PO_ID
    product = models.ForeignKey(Product, on_delete=models.CASCADE)               # PROD_ID

    po_item_ordered_quantity = models.IntegerField()                             
    po_item_unit_price = models.DecimalField(max_digits=12, decimal_places=2)    
    po_item_line_total = models.DecimalField(max_digits=14, decimal_places=2)     

    # ADD THIS FIELD to link to requisition item mao ni gamit para 1 po multiple reqs
    requisition_item = models.ForeignKey(
        'Requisition.RequisitionItem', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='po_items'
    )
    
    def __str__(self):
        return f"{self.product.prod_name} - {self.po_item_ordered_quantity}"
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