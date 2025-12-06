from django.urls import path
from . import views

urlpatterns = [
    path('delivery_management/', views.delivery_management, name="delivery_management"),
    path('inspection/<int:req_id>/', views.inspection_page, name='inspection_page'),
    path('inspection/<int:req_id>/save/', views.save_inspection_discrepancies, name='save_inspection'),
    path('manage-delivery/<int:po_id>/', views.manage_delivery, name='manage_delivery'),
    path('create-delivery/<int:po_id>/', views.create_delivery, name='create_delivery'),
]