# Requisition/models.py

from django.db import models
from ERP.models import User, Product, Branch
from .constants import *


class Requisition(models.Model):
    req_id = models.AutoField(primary_key=True)

    requested_by = models.ForeignKey(User, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)

    req_type = models.CharField(max_length=100, choices=REQ_TYPE_CHOICES)

    # Main status + sub-status combo
    req_main_status = models.CharField(max_length=100, choices=REQ_MAIN_STATUS_CHOICES)
    req_substatus = models.CharField(max_length=100, choices=REQ_SUBSTATUS_CHOICES, default="NONE")

    req_requested_date = models.DateTimeField(auto_now_add=True)
    req_date_required = models.DateField(null=True, blank=True)

    req_notes = models.TextField(null=True, blank=True)
    req_rejection_reason = models.TextField(null=True, blank=True)
    req_approval_date = models.DateTimeField(null=True, blank=True)

    delivery_receipt_num = models.CharField(max_length=100, null=True, blank=True)
    rf_file = models.FileField(upload_to="rfs/", null=True, blank=True)

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requisition_approver"
    )

    def __str__(self):
        return f"REQ-{self.req_id} ({self.req_type})"

class RequisitionItem(models.Model):
    req_item_id = models.AutoField(primary_key=True)
    requisition = models.ForeignKey(Requisition, on_delete=models.CASCADE, related_name="items")

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    uom = models.CharField(max_length=20)

    def __str__(self):
        return f"Item {self.product.prod_name} x {self.quantity}"

class RequisitionStatusTimeline(models.Model):
    history_id = models.AutoField(primary_key=True)

    requisition = models.ForeignKey(
        Requisition,
        on_delete=models.CASCADE,
        related_name="timeline"
    )

    main_status = models.CharField(
        max_length=100,
        choices=REQ_MAIN_STATUS_CHOICES
    )

    sub_status = models.CharField(
        max_length=100,
        choices=REQ_SUBSTATUS_CHOICES,
        null=True,
        blank=True
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )

    changed_at = models.DateTimeField(auto_now_add=True)

    comment = models.CharField(
        max_length=100,
        # choices=TIMELINE_COMMENT_CHOICES,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.requisition.req_id} - {self.main_status}"
