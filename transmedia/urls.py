from django.urls import path
from . import views

app_name = "transmedia"

urlpatterns = [
    path("", views.inventory_list, name="inventory_list"),
    path("migrations/", views.migrations_index, name="migrations_index"),
    path("migrations/diversion/", views.migration_diversion, name="migration_diversion"),
    path("migrations/shift-to-store/", views.migration_shift_to_store, name="migration_shift_to_store"),
    path("migrations/reparenting/", views.migration_reparenting, name="migration_reparenting"),
    path("migrations/dmw-to-of/", views.migration_dmw_to_of, name="migration_dmw_to_of"),
    path("migrations/cpan-to-maan/", views.migration_cpan_to_maan, name="migration_cpan_to_maan"),
    path("migrations/dmw-make-change/", views.migration_dmw_make_change, name="migration_dmw_make_change"),
    path("upload/", views.excel_upload, name="excel_upload"),
    path("edit/<int:pk>/", views.inventory_edit, name="inventory_edit"),
    path("action/<int:pk>/", views.action_update, name="action_update"),
    path("logs/", views.log_list, name="log_list"),
    path("spares/", views.spare_list, name="spare_list"),
]
