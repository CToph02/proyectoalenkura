from django.urls import path
from .views import estudiantes_view

app_name = 'core'

urlpatterns = [
    path('estudiantes/', estudiantes_view, name='estudiantes'),
]