from django.contrib import admin
from .models import (
    RFQ,
    RFQ_Item,
    Supplier,
    Supplier_Product,
    RFQ_Supplier,
    Supplier_Category,
    Supplier_Quotation,
    Supplier_Quotation_Item,
    Purchase_Order,
    Purchase_Order_Item
)

# Register models
admin.site.register(RFQ)
admin.site.register(RFQ_Item)
admin.site.register(Supplier)
admin.site.register(Supplier_Product)
admin.site.register(RFQ_Supplier)
admin.site.register(Supplier_Category)
admin.site.register(Supplier_Quotation)
admin.site.register(Supplier_Quotation_Item)
admin.site.register(Purchase_Order)
admin.site.register(Purchase_Order_Item)
