from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name="login"),
    path('top_management_dashboard/', views.top_management_dashboard, name="top_management_dashboard"),
    path('add_users/', views.add_users, name="add_users"),
    path("branch_manager_dashboard/", views.branch_manager_dashboard, name="branch_manager_dashboard"),
    # path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
    path("property_custodian_dashboard/", views.property_custodian_dashboard, name="property_custodian_dashboard"),
    path("inventory/", views.inventory, name="inventory"),
    path('inventory/stock_action/', views.stock_action, name='stock_action'), #Note: this url is for the stock in and stock out for the inventory itself [STOCK IN, STOCK OUT]
    path('inventory/edit_product/', views.edit_product, name='edit_product'), #Note: this url is for the EDIT for the inventory itself [EDIT]
]   