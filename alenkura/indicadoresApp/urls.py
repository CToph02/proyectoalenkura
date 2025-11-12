from django.urls import path
from .views import indicadores_create, indicadores_delete, indicadores_edit, indicadores_list, index
urlpatterns = [
    path('', index, name='indicadores_list'),
    path('create/', indicadores_create.as_view(), name='indicadores_create'),
    path('edit/<int:pk>/', indicadores_edit.as_view(), name='indicadores_edit'),
    path('delete/<int:pk>/', indicadores_delete.as_view(), name='indicadores_delete'),
]