# Requisition/views/__init__.py
from .redirections import track_requisition_page, redirect_internal_transfer_form

from .inventory_replenishment import (
    inventory_replenishment_form,
    create_inventory_replenishment
)

from .internal_transfer import (
    internal_transfer_form,
    create_internal_transfer
)

from .requisition_management import (
    requisition_list,
    requisition_detail
)


__all__ = [
    "track_requisition_page",
    "redirect_internal_transfer_form",
    'inventory_replenishment_form',
    'create_inventory_replenishment',
    'internal_transfer_form',
    'create_internal_transfer',
    'requisition_list',
    'requisition_detail',
]