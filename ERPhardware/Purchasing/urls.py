from django.urls import path
from . import views

urlpatterns = [
    path("purchasing_staff_dashboard/", views.purchasing_staff_dashboard, name="purchasing_staff_dashboard"),
    path("purchasing_staff_approved_req/", views.purchasing_staff_approved_req, name="purchasing_staff_approved_req"),
    path("purchasing_staff_sup_manage/", views.purchasing_staff_sup_manage, name="purchasing_staff_sup_manage"),
    path("purchasing_staff_inventory/", views.purchasing_staff_inventory, name="purchasing_staff_inventory"),
    path("purchasing_staff_track_progress/", views.purchasing_staff_track_progress, name="purchasing_staff_track_progress"),
    path("purchasing_staff_reports/", views.purchasing_staff_reports, name="purchasing_staff_reports"),
    path("purchasing_staff_view_reqitems/<int:req_id>/", views.purchasing_staff_view_reqitems, name="purchasing_staff_view_reqitems"),
    path("purchasing_staff_view_reqitems/<int:req_id>/",views.purchasing_staff_view_reqitems,name="purchasing_staff_view_reqitems"),




]  