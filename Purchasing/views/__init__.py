# # Purchasing/init.py

# from .purchasing_staff_dashboard_views import *
# from .purchasing_staff_approved_req_views import *
# from .purchasing_staff_sup_manage_views import*
# from .purchasing_staff_inventory_views import*
# from .purchasing_staff_reports_views import*
# from .supplier_management_views import *

# Purchasing/views/__init__.py

from .purchasing_staff_dashboard_views import *
from .purchasing_staff_approved_req_views import *
from .purchasing_staff_sup_manage_views import*
from .purchasing_staff_inventory_views import*
from .purchasing_staff_reports_views import*
from .create_rfq_views import*
from .input_quotation_views import*
from .create_po_views import*
from .rf_selection_views import*
from .rfq_creation_views import*
from .quote_creation_views import*
from .purchasing_staff_inventory_views import *
from .purchasing_staff_reports_views import *
from .po_creation_views import*
from . import supplier_management_views

__all__ = [
    'purchasing_staff_dashboard',
    'purchasing_staff_approved_req',
    'purchasing_staff_inventory',
    'purchasing_staff_reports',
    'supplier_management_views',
]
