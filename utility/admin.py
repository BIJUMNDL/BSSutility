from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Site, Inspection, DieselFilling

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("site_name", "site_code", "bss_incharge_name", "technician_name")
    search_fields = ("site_name", "site_code")

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ("inspection_date", "site", "dg_status", "overall_site_cleanliness", "created_at")
    search_fields = ("site__site_name", "site__site_code")
    list_filter = ("inspection_date", "dg_status", "overall_site_cleanliness")

@admin.register(DieselFilling)
class DieselFillingAdmin(admin.ModelAdmin):
    list_display = ("date_of_filling", "site", "diesel_filled", "balance_after_filling", "created_at")
    search_fields = ("site__site_name", "site__site_code")
    list_filter = ("date_of_filling",)