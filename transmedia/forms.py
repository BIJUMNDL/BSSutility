import datetime

from django import forms
from django.utils import timezone

from .models import MediaInventory, SpareDMW


def _add_future_date_errors(form, date_fields):
    today = timezone.localdate()
    for field_name in date_fields:
        value = form.cleaned_data.get(field_name)
        if isinstance(value, datetime.date) and value > today:
            form.add_error(field_name, f"Date cannot be after today ({today.isoformat()}).")


class MediaInventoryForm(forms.ModelForm):
    class Meta:
        model = MediaInventory
        fields = [
            "sl_no", "site_name", "transmission_media", "a_end", "b_end",
            "terminal_equipment_type", "make", "terminalequipment_id",
            "cluster", "port_2g", "port_3g", "port_4g"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Auto-generated always (SITE+Terminal Equipment+first 3 of Make)
        self.fields["terminalequipment_id"].disabled = True
        self.fields["terminalequipment_id"].required = False


class ExcelUploadForm(forms.Form):
    file = forms.FileField()


class _BaseMigrationForm(forms.Form):
    record = forms.ModelChoiceField(
        queryset=MediaInventory.objects.none(),
        label="Record",
        widget=forms.Select(
            attrs={
                "class": "form-select js-search-select",
                "data-placeholder": "Type site name or TE ID to search...",
            }
        ),
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Remarks (optional)"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["record"].queryset = MediaInventory.objects.all().order_by("site_name")


class ReparentingForm(_BaseMigrationForm):
    b_end = forms.CharField(
        required=True,
        label="B END (TE B1 NODE)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "B END (TE B1 NODE)"}),
    )
    terminal_equipment_type = forms.CharField(
        required=True,
        label="Terminal Equipment (MAAN/DMW/CPAN)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "MAAN/DMW/CPAN"}),
    )
    make = forms.CharField(
        required=True,
        label="Make",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Make"}),
    )
    cluster = forms.CharField(
        required=True,
        label="Cluster",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Cluster"}),
    )
    port_2g = forms.CharField(
        required=True,
        label="2G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "2G PORT"}),
    )
    port_3g = forms.CharField(
        required=True,
        label="3G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "3G PORT"}),
    )
    port_4g = forms.CharField(
        required=True,
        label="4G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "4G PORT"}),
    )


class DmwToOfForm(_BaseMigrationForm):
    DISPOSITION_CHOICES = [
        ("DECOMMISSION", "Decommission"),
        ("DIVERSION", "Diversion"),
    ]

    terminal_equipment_type = forms.CharField(
        required=True,
        label="Terminal Equipment (MAAN/DMW/CPAN)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "MAAN/DMW/CPAN"}),
    )
    b_end = forms.CharField(
        required=True,
        label="B END (TE B1 NODE)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "B END (TE B1 NODE)"}),
    )
    make = forms.CharField(
        required=True,
        label="Make",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Make"}),
    )
    cluster = forms.CharField(
        required=True,
        label="Cluster",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Cluster"}),
    )
    port_2g = forms.CharField(
        required=True,
        label="2G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "2G PORT"}),
    )
    port_3g = forms.CharField(
        required=True,
        label="3G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "3G PORT"}),
    )
    port_4g = forms.CharField(
        required=True,
        label="4G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "4G PORT"}),
    )
    disposition = forms.ChoiceField(
        required=True,
        choices=DISPOSITION_CHOICES,
        label="Disposition",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    diverted_site_name = forms.CharField(
        required=False,
        label="Diverted Site Name",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Diverted Site Name"}),
    )
    diversion_order = forms.CharField(
        required=False,
        label="Diversion Order",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Diversion Order"}),
    )
    date_of_decommissioning = forms.DateField(
        required=False,
        label="Date of Decommissioning",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    date_of_commissioning = forms.DateField(
        required=False,
        label="Date of Commissioning",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    stored = forms.ChoiceField(
        required=False,
        choices=[("", "Select Storage"), ("BSS_STORE", "BSS Store"), ("IN_SITE", "In site")],
        label="Stored",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned = super().clean()
        disposition = cleaned.get("disposition") or ""
        _add_future_date_errors(self, ("date_of_decommissioning", "date_of_commissioning"))
        if disposition == "DECOMMISSION":
            if not cleaned.get("date_of_decommissioning"):
                self.add_error("date_of_decommissioning", "Date of decommissioning is required for Decommission.")
            if not cleaned.get("stored"):
                self.add_error("stored", "Stored is required for Decommission.")
        if disposition == "DIVERSION":
            if not cleaned.get("diverted_site_name"):
                self.add_error("diverted_site_name", "Diverted site name is required for Diversion.")
            if not cleaned.get("diversion_order"):
                self.add_error("diversion_order", "Diversion order is required for Diversion.")
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today_iso = timezone.localdate().isoformat()
        self.fields["date_of_decommissioning"].widget.attrs["max"] = today_iso
        self.fields["date_of_commissioning"].widget.attrs["max"] = today_iso
        self.fields["record"].queryset = MediaInventory.objects.filter(
            transmission_media="DMW"
        ).order_by("site_name")


class CpanToMaanForm(_BaseMigrationForm):
    b_end = forms.CharField(
        label="B END",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "B END"}),
    )
    make = forms.CharField(
        label="Make",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Make"}),
    )
    cluster = forms.CharField(
        label="Cluster",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Cluster"}),
    )
    port_2g = forms.CharField(
        label="2G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "2G PORT"}),
    )
    port_3g = forms.CharField(
        label="3G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "3G PORT"}),
    )
    port_4g = forms.CharField(
        label="4G PORT",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "4G PORT"}),
    )


class DmwMakeChangeForm(_BaseMigrationForm):
    DISPOSITION_CHOICES = [
        ("DECOMMISSION", "Decommission"),
        ("DIVERSION", "Diversion"),
    ]
    MAKE_CHOICES = [
        ("CCERAGON", "CCeragon"),
        ("ECERAGON", "ECeragon"),
        ("NOKIA", "Nokia"),
        ("UBR", "UBR"),
    ]

    b_end = forms.CharField(
        required=True,
        label="New B END",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "New B END"}),
    )
    make = forms.ChoiceField(
        required=True,
        label="New Make",
        choices=MAKE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    disposition = forms.ChoiceField(
        required=True,
        choices=DISPOSITION_CHOICES,
        label="Disposition",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    diverted_site_name = forms.CharField(
        required=False,
        label="Diverted Site Name",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Diverted Site Name"}),
    )
    diversion_order = forms.CharField(
        required=False,
        label="Diversion Order",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Diversion Order"}),
    )
    date_of_decommissioning = forms.DateField(
        required=False,
        label="Date of Decommissioning",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    date_of_commissioning = forms.DateField(
        required=False,
        label="Date of Commissioning",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    stored = forms.ChoiceField(
        required=False,
        choices=[("", "Select Storage"), ("BSS_STORE", "BSS Store"), ("IN_SITE", "In site")],
        label="Stored",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean(self):
        cleaned = super().clean()
        disposition = cleaned.get("disposition") or ""
        _add_future_date_errors(self, ("date_of_decommissioning", "date_of_commissioning"))
        if disposition == "DECOMMISSION":
            if not cleaned.get("date_of_decommissioning"):
                self.add_error("date_of_decommissioning", "Date of decommissioning is required for Decommission.")
            if not cleaned.get("stored"):
                self.add_error("stored", "Stored is required for Decommission.")
        if disposition == "DIVERSION":
            if not cleaned.get("diverted_site_name"):
                self.add_error("diverted_site_name", "Diverted site name is required for Diversion.")
            if not cleaned.get("diversion_order"):
                self.add_error("diversion_order", "Diversion order is required for Diversion.")
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today_iso = timezone.localdate().isoformat()
        self.fields["date_of_decommissioning"].widget.attrs["max"] = today_iso
        self.fields["date_of_commissioning"].widget.attrs["max"] = today_iso
        self.fields["record"].queryset = MediaInventory.objects.filter(
            transmission_media="DMW"
        ).order_by("site_name")


class DiversionActionForm(forms.Form):
    spare = forms.ModelChoiceField(
        queryset=SpareDMW.objects.none(),
        label="Spare DMW TE ID",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    site_name = forms.CharField(
        label="Diverted Site Name",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Diverted Site Name"}),
    )
    diversion_letter_no = forms.CharField(
        label="Diversion Letter No",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Diversion Letter No"}),
    )
    remarks = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Remarks (optional)"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["spare"].queryset = SpareDMW.objects.all().order_by("-created_at")


class ShiftToStoreForm(_BaseMigrationForm):
    spare = forms.ModelChoiceField(
        queryset=SpareDMW.objects.none(),
        label="Spare DMW TE ID",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("record", None)
        self.fields["spare"].queryset = SpareDMW.objects.all().order_by("-created_at")
