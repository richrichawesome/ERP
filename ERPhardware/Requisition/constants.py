# Requisition/constants.py

REQ_TYPE_CHOICES = [
    ("INV_REPLENISHMENT", "Inventory Replenishment"),
    ("INTERNAL_TRANSFER", "Internal Transfer"),
]

REQ_MAIN_STATUS_CHOICES = [
    ("PENDING_CUSTODIAN", "Pending Custodian Approval"),
    ("PENDING_TOP_MGMT", "Pending Top Management Approval"),
    ("APPROVED_REQUISITION", "Approved Requisition"),
    ("PO_APPROVAL", "PO Approval"),
    ("TO_BE_DELIVERED", "To be Delivered"),
    ("INSPECTION", "Inspection"),
    ("FULFILLED", "Request Fulfilled"),
]

REQ_SUBSTATUS_CHOICES = [
    # Approved Requisition sub-status
    ("RFQ_CREATED", "RFQ Created"),
    ("PENDING_PO", "Pending Purchase Order"),

    # # PO Approval sub-status
    # ("PO_PENDING_CUSTODIAN", "PO Pending Custodian Approval"),
    # ("PO_PENDING_TOP_MGMT", "PO Pending Top Management Approval"),
    # ("PO_APPROVED", "PO Approved"),
    # PO Approval sub-status (updated)
    ("PO_CUSTODIAN_APPROVAL", "Custodian reviewed and approved"),
    ("PO_TOP_MANAGEMENT_APPROVAL", "Approved by Top Management"),
    ("PO_APPROVED", "PO Approved"),  # keep if needed as final confirmation    

    # To be Delivered
    ("PO_SENT_TO_SUPPLIER", "PO Sent to Supplier"),

    # Inspection
    ("PRODUCTS_RECEIVED", "Products Received"),
    ("INSPECTING", "Inspecting"),
    ("IN_TRANSIT", "In Transit"),

    ("NONE", "None"),
]
