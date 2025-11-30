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


class CursoForm(BaseStyledModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sala_id"].required = False
        self.fields["sala_id"].empty_label = "Sin sala asignada"

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
