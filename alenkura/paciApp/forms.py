from django import forms
from .models import PaciAppModel

class PaciAppForm(forms.ModelForm):
    class Meta:
        model = PaciAppModel
        fields = [
            'name',
            'description',
            'created_at',
            'updated_at',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'created_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'updated_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("El nombre es obligatorio.")
        return name
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("La descripción es obligatoria.")
        return description
    def clean(self):
        cleaned_data = super().clean()
        # Aquí puedes agregar validaciones adicionales si es necesario
        return cleaned_data