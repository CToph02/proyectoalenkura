from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout

# Create your views here.
def login_view(request):
    username = request.POST.get('user')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        print('a')
        login(request, user)
        return redirect('core:index')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('accounts:login')
