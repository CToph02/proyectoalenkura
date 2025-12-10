from django.urls import path
from .views import index, evaluar
app_name = 'instrumentosApp'
urlpatterns = [
    path('evaluar/<int:id>', evaluar, name='evaluar_estudiante'),
    path('<int:id>', index, name='instrumentos_list'),
]