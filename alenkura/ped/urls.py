from django.urls import path

from . import views

app_name = "ped"

urlpatterns = [
    path("formulario/", views.formulario_view, name="formulario"),
    path("plan/<int:plan_id>/pdf/", views.plan_pdf_view, name="plan_pdf"),
]
