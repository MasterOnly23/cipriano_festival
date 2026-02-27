from django.urls import path

from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("kitchen/", views.kitchen_view, name="kitchen"),
    path("sales/", views.sales_view, name="sales"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("batches/", views.batches_view, name="batches"),
    path("admin-ops/", views.admin_ops_view, name="admin-ops"),
    path("api/scan", views.ScanAPIView.as_view(), name="api-scan"),
    path("api/dashboard", views.DashboardDataAPIView.as_view(), name="api-dashboard"),
    path("api/dashboard/sales-export.xls", views.SalesExportXLSAPIView.as_view(), name="api-dashboard-sales-export"),
    path("api/waiters", views.WaiterAPIView.as_view(), name="api-waiters"),
    path("api/waiters/labels.pdf", views.WaiterLabelsAPIView.as_view(), name="api-waiters-labels"),
    path("api/batches/generate", views.BatchGenerateAPIView.as_view(), name="api-batches-generate"),
    path("api/batches/<str:batch_code>/labels.pdf", views.BatchLabelsAPIView.as_view(), name="api-batches-labels"),
    path("api/admin/status", views.AdminStatusAPIView.as_view(), name="api-admin-status"),
    path("api/admin/undo", views.UndoAPIView.as_view(), name="api-admin-undo"),
    path("api/admin/verify-pin", views.AdminVerifyPinAPIView.as_view(), name="api-admin-verify-pin"),
]
