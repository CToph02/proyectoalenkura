from django.urls import path, include
from .views import paci_list, paci_create, paci_edit, paci_delete, index
urlpatterns = [
    path('', index, name='paci_list'),
    path('indicadores/', include('indicadoresApp.urls')),
    path('create/', paci_create.as_view(), name='paci_create'),
    path('edit/<int:pk>/', paci_edit.as_view(), name='paci_edit'),
    path('delete/<int:pk>/', paci_delete.as_view(), name='paci_delete'),
]