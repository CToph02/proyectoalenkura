from django.urls import path

from .views import proyecto_delete, proyecto_download, proyecto_pdf, proyecto_view

app_name = "aula"

urlpatterns = [
    path("proyecto/", proyecto_view, name="proyecto_form"),
    path("proyecto/<int:pk>/descargar/", proyecto_download, name="proyecto_download"),
    path("proyecto/<int:pk>/pdf/", proyecto_pdf, name="proyecto_pdf"),
    path("proyecto/<int:pk>/eliminar/", proyecto_delete, name="proyecto_delete"),
]
