from django.urls import path, include
from .views import index, create_paci# paci_list, paci_create, paci_edit, paci_delete, 

app_name = 'paciApp'

urlpatterns = [
    path('<int:id>', index, name='paci_list'),
    path('create/<int:id>', create_paci, name='create_paci'),
    #path('edit/<int:pk>/', paci_edit.as_view(), name='paci_edit'),
]