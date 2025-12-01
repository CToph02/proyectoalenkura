from django.shortcuts import render, get_object_or_404, HttpResponse
from django.db.models import Prefetch
from paciApp.models import PaciAppModel
from .models import Indicadores
from core.models import Estudiante, Asignatura
# Create your views here.


def index(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)

    pacis_estudiante = (
        PaciAppModel.objects
        .filter(student_id=estudiante.id)
        .select_related(
            "subject", "axis"
        ).prefetch_related('indicadores_paci')
    )
    asignaturas = (
        Asignatura.objects
            .filter(
                paci_subject__student_id=estudiante.id
            )
            .prefetch_related(
                Prefetch(
                    'paci_subject',
                    queryset=pacis_estudiante,
                    to_attr='pacis_estudiante'
                )
                
            )
        ).distinct()
    context = {
        "estudiante": estudiante, 
        "asignaturas": asignaturas
    }
    return render(request, "indicadores.html", context)


def ind(request):
    return HttpResponse("hola")
