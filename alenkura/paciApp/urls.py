from django.urls import path
from .views import paci_list, paci_create, paci_edit, paci_delete
urlpatterns = [
    path('', paci_list.as_view(), name='paci_list'),
    path('create/', paci_create.as_view(), name='paci_create'),
    path('edit/<int:pk>/', paci_edit.as_view(), name='paci_edit'),
    path('delete/<int:pk>/', paci_delete.as_view(), name='paci_delete'),
]