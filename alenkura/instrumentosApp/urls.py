from django.urls import path
from .views import index, ind
app_name = 'instrumentosApp'
urlpatterns = [
    path('', ind),
    path('<int:id>', index, name='instrumentos_list'),
    #path('create/', indicadores_create.as_view(), name='indicadores_create'),
    #path('edit/<int:pk>/', indicadores_edit.as_view(), name='indicadores_edit'),
    #path('delete/<int:pk>/', indicadores_delete.as_view(), name='indicadores_delete'),
]