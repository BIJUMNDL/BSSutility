from django.urls import path
from . import views
from . import views_export

urlpatterns = [
    path("", views.inspection_create, name="home"),
    path("new/", views.inspection_create, name="inspection_create"),
    path("inspections/", views.inspection_list, name="inspection_list"),
    path("diesel/new/", views.diesel_filling_create, name="diesel_filling_create"),
    path("diesel/", views.diesel_records_list, name="diesel_records_list"),
    path("diesel/statement/", views.diesel_statement_list, name="diesel_statement_list"),
    path("api/sites/", views.site_search_api, name="site_search_api"),
    path("sites/upload/", views.upload_sites, name="upload_sites"),
     path("export/sites.xlsx", views_export.export_sites_xlsx, name="export_sites_xlsx"),
    path("export/inspections.xlsx", views_export.export_inspections_xlsx, name="export_inspections_xlsx"),
    path("export/diesel.xlsx", views_export.export_diesel_xlsx, name="export_diesel_xlsx"),
    path("export/diesel-statement.xlsx", views_export.export_diesel_statement_xlsx, name="export_diesel_statement_xlsx"),
    path("export/all.xlsx", views_export.export_all_xlsx, name="export_all_xlsx"),
]
