from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Exists, OuterRef

from .models import Estudiante
from paciApp.models import PaciAppModel
from instrumentosApp.models import Indicadores

# Create your views here.
def estudiantes_view(request):
    estudiantes = Estudiante.objects.all().annotate(
        tiene_paci=Exists(
            PaciAppModel.objects.filter(student=OuterRef('pk'))
        ),
        # tiene_indicadores=Exists(
        #     Indicadores.objects.filter(paci__student=OuterRef('pk'))
        # )
    )
    #estudiante_id = request.GET.get('estudiante_id')

    #paci = PaciAppModel.objects.filter(student__in=estudiantes)
    #indicadores = Indicadores.objects.filter(paci__in=paci)
    context = {
        'estudiantes': estudiantes,
        #'paci': paci,
        #'indicadores': indicadores
    }
    return render(request, 'estudiantes.html', context)

# def paci_get(request, id):
#     paci = PaciAppModel.objects.get(student_id=id)
#     return HttpResponse(paci)