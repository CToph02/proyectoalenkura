from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

class BaseStyledModelForm(forms.ModelForm):
    """Applies a consistent Tailwind-ish style to all fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "w-full rounded-md border border-gray-600 bg-gray-800 px-3 py-2 text-gray-100 "
                    "focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-400",
                }
            )

class DocenteForm(BaseStyledModelForm):
    og_pwd = forms.CharField(
        widget=forms.PasswordInput,
        label="Ingrese su contraseña actual."
    )

    pwd_1 = forms.CharField(
        widget=forms.PasswordInput,
        label="Ingrese su nueva contraseña."
    )
    
    pwd_2 = forms.CharField(
        widget=forms.PasswordInput,
        label="Confirme su nueva contraseña."
    )

    class Meta:
        model = get_user_model()
        fields = [
            'og_pwd',
            'pwd_1',
            'pwd_2'
        ]
        label = {
            'og_pwd': 'Contraseña actual',
            'pwd_1': 'Nueva contraseña',
            'pwd_2': 'Confirme contraseña'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            css_classes = 'bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white'
            
            # Agregamos las clases al widget existente
            field.widget.attrs.update({'class': css_classes})
    
    def clean_og_pwd(self):
        og_pwd = self.cleaned_data.get('og_pwd')
        if not self.instance.check_password(og_pwd):
            raise ValidationError("La contraseña no coincide")
        return og_pwd

    def clean(self):
        cleaned_data = super().clean()
        pwd_1 = cleaned_data.get("pwd_1")
        pwd_2 = cleaned_data.get("pwd_2")
        if pwd_1 and pwd_2 and pwd_1 != pwd_2:
            self.add_error("pwd_2", "Las contraseñas no coinciden.")
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        user.set_password(self.cleaned_data['pwd_1'])

        if commit:
            user.save()
        return user