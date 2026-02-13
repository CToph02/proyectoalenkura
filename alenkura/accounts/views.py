from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .forms import DocenteForm

# Create your views here.
def login_view(request):
    username = request.POST.get('user')
    password = request.POST.get('password')
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('coreApp:index')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def password_change(request):
    if request.method == "POST":
        form = DocenteForm(request.POST, instance=request.user)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect('accounts:login')
        
    else:
        form = DocenteForm(instance=request.user)

    context = {
        'form': form
    }
    return render(request, 'pwd_change.html', context)