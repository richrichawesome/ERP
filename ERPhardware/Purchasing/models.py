from django.db import models
from ERP.models import User, Branch, Product, Product_Category
from Requisition.models import Requisition  # import from ERP app


# ------------------------------
# Supplier
# ------------------------------
class Supplier(models.Model):
    sup_id = models.AutoField(primary_key=True)
    sup_name = models.CharField(max_length=255)
    sup_contact_person = models.CharField(max_length=255)
    sup_phone = models.CharField(max_length=50)
    sup_email = models.EmailField(unique=True)
    sup_address = models.TextField()
    sup_payment_terms = models.CharField(max_length=100)
    sup_delivery_terms = models.CharField(max_length=100)
    sup_is_active = models.BooleanField(default=True)
    sup_created_at = models.DateTimeField(auto_now_add=True)
    sup_updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sup_name


# ------------------------------
# Supplier Category
# ------------------------------
class SupplierCategory(models.Model):
    sup_cat_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    category = models.ForeignKey(Product_Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category.prod_cat_name} - {self.supplier.sup_name}"


# ------------------------------
# Supplier Product
# ------------------------------
class SupplierProduct(models.Model):
    sup_prod_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sup_prod_code = models.CharField(max_length=100)
    sup_prod_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    sup_prod_last_updated_price = models.DateField()
    sup_is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sup_prod_code} - {self.supplier.sup_name}"


# ------------------------------
# Purchase Order
# ------------------------------
class PurchaseOrder(models.Model):
    po_id = models.AutoField(primary_key=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # purchasing staff
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    po_status = models.CharField(max_length=50)
    po_order_date = models.DateField()
    po_eta = models.DateField()
    po_total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    po_approval_date = models.DateField(blank=True, null=True)
    po_rejection_reason = models.TextField(blank=True, null=True)
    po_created_at = models.DateTimeField(auto_now_add=True)
    po_pdf = models.FileField(upload_to='purchase_orders/', blank=True, null=True)

    def __str__(self):
        return f"PO {self.po_id} - {self.po_status}"


# ------------------------------
# Purchase Order Item
# ------------------------------
class PurchaseOrderItem(models.Model):
    po_item_id = models.AutoField(primary_key=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    po_item_ordered_quantity = models.IntegerField()
    po_item_unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    po_item_line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"PO Item {self.po_item_id} for PO {self.purchase_order.po_id}"
