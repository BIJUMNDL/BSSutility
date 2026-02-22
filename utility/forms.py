from django import forms
from .models import Inspection, DieselFilling

class InspectionForm(forms.ModelForm):
    class Meta:
        model = Inspection
        fields = "__all__"
        widgets = {"inspection_date": forms.DateInput(attrs={"type": "date"})}

class DieselFillingForm(forms.ModelForm):
    class Meta:
        model = DieselFilling
        fields = "__all__"
        widgets = {"date_of_filling": forms.DateInput(attrs={"type": "date"})}


class SiteUploadForm(forms.Form):
    file = forms.FileField()
    sheet = forms.CharField(required=False)
    header_row = forms.IntegerField(required=False, initial=1, min_value=1)