#ERP.models (Inventory, Roles, User, Branch)
from django.db import models

#DATABASE

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=20)
    role_description = models.CharField(max_length=150)

    def __str__(self):
        return self.role_name

class Branch(models.Model):
    branch_id = models.AutoField(primary_key=True)
    branch_name = models.CharField(unique=True)
    branch_address = models.CharField(max_length=150)
    branch_phone = models.CharField(max_length=20)
    branch_email = models.CharField(max_length=100, unique=True)
    branch_is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.branch_name


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=20, unique=True)
    user_password = models.CharField(max_length=20)
    user_email = models.CharField(max_length=30, unique=True)
    user_fname = models.CharField(max_length=16)
    user_lname = models.CharField(max_length=16)
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    #FK
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    def __str__(self):
        return self.username


class Product_Category(models.Model):
    prod_cat_id = models.AutoField(primary_key=True)
    prod_cat_name = models.CharField(max_length=50)
    prod_cat_desc = models.CharField(max_length=50)

    def __str__(self):
        return self.prod_cat_name
    
class Product(models.Model):
    prod_id = models.AutoField(primary_key=True)
    prod_name = models.CharField(max_length=50)
    prod_desc = models.CharField(max_length=50)
    prod_unit_of_measure = models.CharField(max_length=20)
    prod_current_cost = models.DecimalField(max_digits=10, decimal_places=2)
    prod_retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    prod_reorder_threshold = models.IntegerField()
    prod_is_active = models.BooleanField(default=True)
    prod_created_at = models.DateField(auto_now_add=True)
    prod_updated_at = models.DateTimeField(null=True, blank=True)
    prod_sku = models.CharField(max_length=50)
    #FK
    category = models.ForeignKey(Product_Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.prod_name

class Inventory(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    quantity_on_hand = models.IntegerField(default=0)
    last_updated_at = models.DateField(null=True, blank=True)
    #FK
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Inventory_Transaction(models.Model):
    TRANS_TYPE_CHOICES = [
        ('stockin', 'Stock In'),
        ('stockout', 'Stock Out'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
    ]
    trans_id = models.AutoField(primary_key=True)
    trans_type = models.CharField(max_length=20, choices=TRANS_TYPE_CHOICES)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    #FK
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    user = models.ForeignKey(User,  on_delete=models.CASCADE)

    def __str__(self):
        return self.trans_type

class Price_History(models.Model):
    price_id = models.AutoField(primary_key=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()
    #FK
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Product_Specification(models.Model):
    prod_spec_id = models.AutoField(primary_key=True)
    spec_name = models.CharField(max_length=50)
    spec_value = models.CharField(max_length=50)
    #FK
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    

