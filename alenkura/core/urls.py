from django.urls import path
from .views import estudiantes_view, gestion_view, index, send_email

app_name = 'coreApp'

urlpatterns = [
    path('', index, name='index'),
    path('estudiantes', estudiantes_view, name='estudiantes'),
    path('gestion', gestion_view, name='gestion'),
    path('correo/<int:id>', send_email, name='send_mail')
]
