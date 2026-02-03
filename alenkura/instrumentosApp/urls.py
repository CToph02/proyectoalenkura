from django.urls import path
from .views import index, evaluar, ver_notas, instrumento_pdf
app_name = 'instrumentosApp'
urlpatterns = [
    path('evaluar/<int:id>', evaluar, name='evaluar_estudiante'),
    path('<int:id>', index, name='instrumentos_list'),
    path('notas/<int:id>', ver_notas, name='notas'),
    path('pdf/<int:id>', instrumento_pdf, name='instrumento_pdf')
]
