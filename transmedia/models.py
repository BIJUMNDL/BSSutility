

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


def _clean(val: str) -> str:
    """Remove spaces and uppercase."""
    if val is None:
        return ""
    return "".join(str(val).split()).upper()


def _first3(val: str) -> str:
    """Remove spaces, uppercase, take first 3 chars."""
    return _clean(val)[:3]


class MediaInventory(models.Model):
    sl_no = models.IntegerField(null=True, blank=True)

    site_name = models.CharField(max_length=150)

    transmission_media = models.CharField(max_length=10, null=True, blank=True)  # OF/DMW
    a_end = models.CharField(max_length=150, null=True, blank=True)
    b_end = models.CharField(max_length=150, null=True, blank=True)

    # Column G: Terminal Equipment (MAAN/DMW/CPAN)
    terminal_equipment_type = models.CharField(max_length=10, null=True, blank=True)

    make = models.CharField(max_length=80, null=True, blank=True)

    # Excel column header MUST be: TERMINALEQUIPMENT ID (blank allowed)
    terminalequipment_id = models.CharField(max_length=30, null=True, blank=True)

    cluster = models.CharField(max_length=80, null=True, blank=True)
    port_2g = models.CharField(max_length=30, null=True, blank=True)
    port_3g = models.CharField(max_length=30, null=True, blank=True)
    port_4g = models.CharField(max_length=30, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_te_id(self) -> str:
        # Full SITE NAME (no spaces) + full Terminal Equipment type (col G) + first 3 of Make
        return f"{_clean(self.site_name)}{_clean(self.terminal_equipment_type)}{_first3(self.make)}"

    def save(self, *args, **kwargs):
        # Always keep TE ID consistent for upload + edits + conversions
        self.terminalequipment_id = self.generate_te_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.site_name} ({self.terminalequipment_id})"


class MediaChangeLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)  # date/time auto
    record = models.ForeignKey(MediaInventory, on_delete=models.CASCADE, related_name="logs")
    site_name = models.CharField(max_length=150)

    # REPAR / DMW_TO_OF / CPAN_TO_MAAN / DMW_MAKE_CHANGE / EDIT / EXCEL_UPLOAD / EXCEL_UPDATE
    action = models.CharField(max_length=40)

    old_data = models.JSONField()
    new_data = models.JSONField()

    remarks = models.CharField(max_length=250, null=True, blank=True)
    changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.created_at} - {self.site_name} - {self.action}"


class SpareDMW(models.Model):
    STORED_CHOICES = [
        ("BSS_STORE", "BSS Store"),
        ("IN_SITE", "In site"),
        ("DIVERTED", "Diverted"),
    ]

    record = models.ForeignKey(MediaInventory, on_delete=models.SET_NULL, null=True, blank=True)
    terminal_equipment = models.CharField(max_length=10, null=True, blank=True)
    date_of_decommissioning = models.DateField(null=True, blank=True)
    terminalequipment_id = models.CharField(max_length=30, null=True, blank=True)
    date_of_commissioning = models.DateField(null=True, blank=True)
    stored = models.CharField(max_length=20, choices=STORED_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.terminalequipment_id or '-'} ({self.terminal_equipment or '-'})"


class DiversionDMW(models.Model):
    record = models.ForeignKey(MediaInventory, on_delete=models.SET_NULL, null=True, blank=True)
    site_name = models.CharField(max_length=150)
    diversion_letter_no = models.CharField(max_length=80)
    remarks = models.CharField(max_length=250, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.site_name} - {self.diversion_letter_no}"
