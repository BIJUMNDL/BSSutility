from django.contrib import admin
from .models import MediaInventory, MediaChangeLog


@admin.register(MediaInventory)
class MediaInventoryAdmin(admin.ModelAdmin):
    list_display = (
        "site_name", "transmission_media", "terminal_equipment_type",
        "terminalequipment_id", "b_end", "make", "cluster", "updated_at"
    )
    search_fields = ("site_name", "terminalequipment_id", "a_end", "b_end", "cluster")
    list_filter = ("transmission_media", "terminal_equipment_type", "cluster")


@admin.register(MediaChangeLog)
class MediaChangeLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "site_name", "action", "changed_by")
    search_fields = ("site_name", "action", "remarks")
    list_filter = ("action", "created_at")

# Register your models here.
