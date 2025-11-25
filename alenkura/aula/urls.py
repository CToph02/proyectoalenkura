from django.urls import path

from .views import proyecto_view

app_name = "aula"

urlpatterns = [
    path("proyecto/", proyecto_view, name="proyecto_form"),
]
