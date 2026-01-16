from django import forms
from django.contrib.auth import get_user_model

from .models import Curso, Estudiante


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


class EstudianteForm(BaseStyledModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Fecha de nacimiento",
    )

    class Meta:
        model = Estudiante
        fields = [
            "first_name",
            "last_name",
            "rut",
            "birth_date",
            "bapDiag",
            "address",
            "commune",
            "etnia",
            "nivel",
            "curso",
        ]
        labels = {
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "rut": "RUT",
            "bapDiag": "Diagnóstico BAP",
            "address": "Dirección",
            "commune": "Comuna",
            "etnia": "Pueblo originario",
            "nivel": "Nivel",
            "curso": "Curso",
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Iteramos sobre todos los campos del formulario
        for field_name, field in self.fields.items():
            # Definimos las clases de Tailwind comunes para todos los inputs
            # bg-white: fondo blanco
            # text-gray-900: texto oscuro
            # border-gray-300: borde gris suave
            # rounded-lg: bordes redondeados
            # w-full: ancho completo
            # p-2.5: padding interno
            css_classes = 'bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white'
            
            # Agregamos las clases al widget existente
            field.widget.attrs.update({'class': css_classes})


class ProfesorForm(BaseStyledModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(),
        label="Contraseña",
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(),
        label="Confirmar contraseña",
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "profesion",
        ]
        labels = {
            "username": "Usuario",
            "first_name": "Nombres",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
            "profesion": "Profesión",
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = user.Roles.TEACHER
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            css_classes = 'bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white'
            
            # Agregamos las clases al widget existente
            field.widget.attrs.update({'class': css_classes})


class CursoForm(BaseStyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sala_id"].required = False
        self.fields["sala_id"].empty_label = "Sin sala asignada"

        for field_name, field in self.fields.items():
            css_classes = 'bg-white border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white'
            
            # Agregamos las clases al widget existente
            field.widget.attrs.update({'class': css_classes})

    class Meta:
        model = Curso
        fields = [
            "name",
            "level",
            "sala_id",
        ]
        labels = {
            "name": "Nombre del curso",
            "level": "Nivel",
            "sala_id": "Sala",
        }

    
