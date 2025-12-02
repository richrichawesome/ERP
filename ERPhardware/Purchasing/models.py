# Purchasing/models.py
from django.db import models # type: ignore
from Requisition.models import Requisition
from ERP.models import *

class RFQ(models.Model):
    rfq_id = models.AutoField(primary_key=True)
    rfq_created_at = models.DateTimeField(auto_now_add=True)
    rfq_created_by = models.ForeignKey(Requisition, on_delete=models.CASCADE)
    
    def __str__(self):
        return str(self.rfq_id)  # Fixed: convert to string


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
    sup_contact_person = models.CharField(max_length=50, default="Unknown")  # Added default
    
    sup_payment_terms = models.TextField(null=True, blank=True)
    sup_delivery_terms = models.TextField(null=True, blank=True)
    sup_is_active = models.BooleanField(default=True)
    sup_created_at = models.DateTimeField(auto_now_add=True)
    sup_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sup_name


class Supplier_Product(models.Model):
    sup_prod_id = models.AutoField(primary_key=True)
    sup_prod_code = models.CharField(max_length=50)
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, default=1)  # Added default
    
    sup_prod_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    sup_prod_last_updated_price = models.DateTimeField(auto_now_add=True)
    sup_prod_is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.supplier.sup_name} - {self.product.prod_name} ({self.sup_prod_code})"

class Supplier_Product_PriceHistory(models.Model):
    price_history_id = models.AutoField(primary_key=True)

    supplier_product = models.ForeignKey(
        Supplier_Product,
        on_delete=models.CASCADE,
        related_name="price_history"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.supplier_product.product.prod_name} - ₱{self.price} ({self.changed_at})"


class RFQ_Supplier(models.Model):
    rfq_sup_id = models.AutoField(primary_key=True)
    rfq = models.ForeignKey(Requisition, on_delete=models.CASCADE) 
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)  
    rfq_date_sent = models.DateTimeField(auto_now_add=True)  
    date_responded = models.DateTimeField(null=True, blank=True) 

    def __str__(self):
        return f"{self.rfq_sup_id} - {self.supplier}"


class Supplier_Category(models.Model):
    sup_cat_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    prod_cat = models.ForeignKey(Product_Category, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.supplier.sup_name} - {self.prod_cat.prod_cat_name}"


class Supplier_Quotation(models.Model):
    sup_qtn_id = models.AutoField(primary_key=True)
    rfq_supplier = models.ForeignKey(RFQ_Supplier, on_delete=models.CASCADE)
    sup_qtn_total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    sup_qtn_eta = models.DateField(null=True, blank=True)
    sup_qtn_valid_until = models.DateField(null=True, blank=True)
    sup_qtn_pdf = models.FileField(upload_to='supplier_quotations/', null=True, blank=True)
    sup_qtn_created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quotation {self.sup_qtn_id} for {self.rfq_supplier.supplier}"


class Supplier_Quotation_Item(models.Model):
    sup_qtn_item_id = models.AutoField(primary_key=True)
    supplier_quotation = models.ForeignKey(Supplier_Quotation, on_delete=models.CASCADE)
    rfq_item = models.ForeignKey(RFQ_Item, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sup_qtn_item_unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"QuotationItem {self.sup_qtn_item_id} - {self.product}"


class Purchase_Order(models.Model):
    po_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    
    po_status = models.CharField(max_length=50)
    po_date_sent_to_sup = models.DateField(null=True, blank=True)
    po_eta = models.DateField(null=True, blank=True)
    
    po_total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    po_approval_date = models.DateField(null=True, blank=True)
    po_rejection_reason = models.TextField(null=True, blank=True)
    
    po_created_at = models.DateTimeField(auto_now_add=True)
    po_pdf = models.FileField(upload_to='po_pdfs/', null=True, blank=True)

    def __str__(self):
        return f"PO-{self.po_id} | {self.supplier.sup_name}"


class Purchase_Order_Item(models.Model):
    po_item_id = models.AutoField(primary_key=True)
    purchase_order = models.ForeignKey(Purchase_Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    po_item_ordered_quantity = models.IntegerField()
    po_item_unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    po_item_line_total = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"PO {self.purchase_order.po_id} - {self.product.prod_name}"

    




