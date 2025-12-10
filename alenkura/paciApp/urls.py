from django.urls import path
from .views import index, create_paci, pdf_paci# paci_list, paci_create, paci_edit, paci_delete, 

app_name = 'paciApp'

urlpatterns = [
    path('<int:id>', index, name='paci_list'),
    path('create/<int:id>', create_paci, name='create_paci'),
    path('pdf/<int:id>', pdf_paci, name='pdf_paci')
    #path('edit/<int:pk>/', paci_edit.as_view(), name='paci_edit'),
]