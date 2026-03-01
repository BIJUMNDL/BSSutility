import datetime

from django import forms
from django.utils import timezone

from .models import Inspection, DieselFilling


def _add_future_date_errors(form, date_fields=None):
    today = timezone.localdate()
    for name, value in list(form.cleaned_data.items()):
        if date_fields and name not in date_fields:
            continue
        if isinstance(value, datetime.date) and value > today:
            form.add_error(name, f"Date cannot be after today ({today.isoformat()}).")

class InspectionForm(forms.ModelForm):
    OPTIONAL_INSPECTION_FIELDS = {
        "power_factor",
        "contract_demand",
        "dg_kwh_reading",
        "dg_remarks",
        "spare_unused_items_available",
    }

    class Meta:
        model = Inspection
        fields = "__all__"
        widgets = {"inspection_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today_iso = timezone.localdate().isoformat()
        self.fields["inspection_date"].widget.attrs["max"] = today_iso
        for name, field in self.fields.items():
            if name not in self.OPTIONAL_INSPECTION_FIELDS:
                field.required = True

    def clean(self):
        cleaned = super().clean()
        _add_future_date_errors(self, {"inspection_date"})
        return cleaned

class DieselFillingForm(forms.ModelForm):
    REQUIRED_DIESEL_FIELDS = ("balance_on_tank", "diesel_filled", "hour_meter_reading")

    class Meta:
        model = DieselFilling
        fields = "__all__"
        widgets = {"date_of_filling": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today_iso = timezone.localdate().isoformat()
        self.fields["date_of_filling"].widget.attrs["max"] = today_iso
        for name in self.REQUIRED_DIESEL_FIELDS:
            self.fields[name].required = True
        self.fields["balance_after_filling"].required = False

    def clean(self):
        cleaned = super().clean()
        _add_future_date_errors(self, {"date_of_filling"})
        balance_on_tank = cleaned.get("balance_on_tank")
        diesel_filled = cleaned.get("diesel_filled")

        # Always derive balance_after_filling from inputs.
        if balance_on_tank is None and diesel_filled is None:
            cleaned["balance_after_filling"] = None
        else:
            cleaned["balance_after_filling"] = (balance_on_tank or 0) + (diesel_filled or 0)

        return cleaned


class SiteUploadForm(forms.Form):
    file = forms.FileField()
    sheet = forms.CharField(required=False)
    header_row = forms.IntegerField(required=False, initial=1, min_value=1)
