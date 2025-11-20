# Requisition/views/__init__.py
from .redirections import track_requisition_page, redirect_inventory_replenishment_form, redirect_internal_transfer_form
# Requisition/views/__init__.py

from .inventory_replenishment import (
    inventory_replenishment_form,
    create_inventory_replenishment
)

from .requisition_management import (
    requisition_list,
    requisition_detail
)


__all__ = [
    "track_requisition_page",
    "redirect_inventory_replenishment_form",
    "redirect_internal_transfer_form",
    'inventory_replenishment_form',
    'create_inventory_replenishment',
    'requisition_list',
    'requisition_detail',
    'inventory_items_view',
]
