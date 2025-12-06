from django.urls import path
from . import views
from Requisition.views import track_requisition_page  # <- correct import


urlpatterns = [
    path('', views.login, name="login"),
    path('top_management_dashboard/', views.top_management_dashboard, name="top_management_dashboard"),
    path('add_users/', views.add_users, name="add_users"),
    # path("branch_manager_dashboard/", views.branch_manager_dashboard, name="branch_manager_dashboard"),
    path('track_requisition/', track_requisition_page, name="track_requisition"),
    # path('add_users/', views.add_users, name="add_users"), #urls from top_management_dashboard == make views -> add_users_views.py
    # path("branch_manager_dashboard/", views.branch_manager_dashboard, name="branch_manager_dashboard"),
    path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
    path("property_custodian_dashboard/", views.property_custodian_dashboard, name="property_custodian_dashboard"),
    path("inventory/", views.inventory, name="inventory"),
    path('inventory/stock_action/', views.stock_action, name='stock_action'), #Note: this url is for the stock in and stock out for the inventory itself [STOCK IN, STOCK OUT]
    path('inventory/edit_product/', views.edit_product, name='edit_product'), #Note: this url is for the EDIT for the inventory itself [EDIT]
    path('inventory/add_product/', views.add_product, name='add_product'), #Note: this url is for the ADD product for the inventory itself [ADD PRODUCT]
    path('inventory/remove_product/', views.remove_product, name='remove_product'), #Note: this url is for the REMOVE product for the inventory itself [REMOVE PRODUCT]
    path('inventory/get_inactive_products/', views.get_inactive_products, name='get_inactive_products'),
    path('inventory/reactivate_product/', views.reactivate_product, name='reactivate_product'),
    path('property-custodian/', views.property_custodian_dashboard, name='property_custodian_dashboard'), #property custodian
    path('requisition/', views.property_custodian_dashboard, name='requisition'), #Note: requisition html pero sa property_custodian_dashboard na views
    path('requisition_detail/<int:req_id>/', views.requisition_detail, name='requisition_detail'),
    path('requisition/<int:req_id>/received/', views.approve_to_be_delivered, name='approve_to_be_delivered'),
    path('requisition/<int:req_id>/approve-management/', views.approve_to_management, name='approve_to_management'),
    path('requisition/<int:req_id>/approve/', views.approve_requisition, name='approve_requisition'),
    path('requisition/<int:req_id>/start-inspection/', views.start_inspection, name='start_inspection'),
    path('requisition/<int:req_id>/confirm-delivery-received/', views.confirm_delivery_received, name='confirm_delivery_received'),
    path('requisition/<int:req_id>/complete/', views.complete_requisition, name='complete_requisition'),
]
