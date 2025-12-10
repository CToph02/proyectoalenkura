from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Prefetch
from paciApp.models import PaciAppModel, Indicador
from .models import Indicadores, Nota
from core.models import Estudiante, Asignatura
# Create your views here.


def index(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)

    paci_estudiante = (
        PaciAppModel.objects
        .filter(student_id=estudiante.id)
        .select_related("subject", "axis")
        .prefetch_related(
            Prefetch(
                'indicadores_paci',                       # relación existente en tu modelo
                queryset=Indicador.objects.all(),         # opcional: añadir filtros si los necesitas
                to_attr='indicadores'                     # cada PaciAppModel tendrá .indicadores
            )
        )
    )
    asignaturas = (
        Asignatura.objects
            .filter(
                paci_subject__student_id=estudiante.id
            )
            .prefetch_related(
                Prefetch(
                    'paci_subject',
                    queryset=paci_estudiante,
                    to_attr='paci_estudiante'
                )
            )
        ).distinct()
    
    context = {
        "estudiante": estudiante,
        "asignatura": asignaturas
    }
    return render(request, "indicadores.html", context)


def evaluar(request, id):
    indicadores = request.POST.get('')
    estudiante = Estudiante.objects.get(id=id)

    return redirect('coreApp:estudiantes')
