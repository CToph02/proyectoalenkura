from django.urls import path
from .views import estudiantes_view, gestion_view, index

app_name = 'coreApp'

urlpatterns = [
    path('', index, name='index'),
    path('estudiantes', estudiantes_view, name='estudiantes'),
    path('gestion', gestion_view, name='gestion'),
]
