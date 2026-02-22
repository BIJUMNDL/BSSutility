from django import forms

class SiteUploadForm(forms.Form):
    file = forms.FileField()
    sheet = forms.CharField(required=False)
    header_row = forms.IntegerField(required=False, initial=1, min_value=1)