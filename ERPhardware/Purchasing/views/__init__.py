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
from .purchasing_staff_inventory_views import *
from .purchasing_staff_reports_views import *
from . import supplier_management_views

__all__ = [
    'purchasing_staff_dashboard',
    'purchasing_staff_approved_req',
    'purchasing_staff_inventory',
    'purchasing_staff_reports',
    'supplier_management_views',
]