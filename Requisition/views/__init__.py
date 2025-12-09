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

from .internal_transfer_request import (
    internal_transfer_request,
    internal_transfer_request_detail,
    # accept_internal_transfer,
    # reject_internal_transfer,
    internal_transfer_request,
    custodian_approve_direct,
    custodian_send_to_management,
    custodian_reject,
    management_approve,
    management_reject,
    sender_accept,
    sender_reject,
    receive_items,

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
    'internal_transfer_request',
    'internal_transfer_request_detail',
    # 'accept_internal_transfer',
    # 'reject_internal_transfer',
    'custodian_approve_direct',
    'custodian_send_to_management',
    'custodian_reject',
    'management_approve',
    'management_reject',
    'sender_accept',
    'sender_reject',
    'receive_items',
]