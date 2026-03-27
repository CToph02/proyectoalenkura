from django.urls import path
from .views import index, evaluar, ver_notas, instrumento_pdf
app_name = 'instrumentosApp'
urlpatterns = [
    path('<int:id>/<int:num>/', evaluar, name='evaluar_estudiante'),
    path('<int:id>/<int:num>/', index, name='instrumentos_list'),
    path('notas/<int:id>/', ver_notas, name='notas'),
    path('pdf/<int:id>/<int:num>/', instrumento_pdf, name='instrumento_pdf')
]
