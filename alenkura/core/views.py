from django.shortcuts import render
from .models import Estudiante

# Create your views here.
def estudiantes_view(request):
    
    context = {
        'estudiantes': Estudiante.objects.all(),
    }
    return render(request, 'estudiantes.html', context)