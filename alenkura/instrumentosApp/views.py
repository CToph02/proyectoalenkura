from django.shortcuts import render, get_object_or_404, HttpResponse
from paciApp.models import PaciAppModel
from .models import Indicadores
# Create your views here.

def index(request, id):
    paci = get_object_or_404(PaciAppModel, student_id=id)
    indicador = Indicadores.objects.filter(paci=paci)
    context = {
        'paci': paci,
        'indicadores': indicador
    }
    return render(request, 'indicadores.html', context)

def ind(request):
    return HttpResponse('hola')