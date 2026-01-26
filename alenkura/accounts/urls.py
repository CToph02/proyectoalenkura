from django.urls import path
from .views import login_view, logout_view, password_change

app_name = 'accounts'

urlpatterns = [
    path('', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('account/pwd_change', password_change, name="pwd_change")
]