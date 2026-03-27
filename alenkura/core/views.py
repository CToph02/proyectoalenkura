from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Avg, Exists, OuterRef, Prefetch, Count, Q, Case, When, Value, BooleanField
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models.functions import Lower, Upper
from instrumentosApp.models import Instrumento_evaluacion, Nota
from paciApp.models import PaciAppModel
from ped.models import PlanAsignatura
from utils import enviar_correo_gmail
from .forms import CursoForm, EstudianteForm, ProfesorForm
from .models import Curso, Estudiante, Sala
from accounts.models import User

def index(request):
    return render(request, "index.html")

def estudiantes_view(request):
    user = request.user
    estudiantes = Estudiante.objects.none()
    
    if hasattr(user, 'sala') and user.sala:
        estudiantes = Estudiante.objects.filter(
            curso__sala_id=user.sala.id
        ).annotate(
            tiene_paci=Exists(PaciAppModel.objects.filter(student=OuterRef("pk"))),
            cantidad_evaluaciones=Count(
                'instrumento',
                filter=Q(instrumento__notas__isnull=False),
                distinct=True
            ),
            tiene_nota=Case(
                When(cantidad_evaluaciones=3, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).order_by(Lower('last_name'))
        
    else:
        estudiantes = Estudiante.objects.none()

    context = {
        "estudiantes": estudiantes,
        'sala': user.sala if hasattr(user, 'sala') else None,
    }

    return render(request, "estudiantes.html", context)

@staff_member_required
def gestion_view(request):
    active_tab = request.GET.get("tab", "estudiantes")
    User = get_user_model()

    if request.method == "POST":
        active_tab = request.POST.get("active_tab", "estudiantes")

        if active_tab == "estudiantes":
            estudiante_form = EstudianteForm(request.POST)
            profesor_form = ProfesorForm()
            curso_form = CursoForm()
            if estudiante_form.is_valid():
                estudiante_form.save()
                messages.success(request, "Estudiante creado correctamente.")
                return redirect(f"{request.path}?tab=estudiantes")
        elif active_tab == "profesores":
            profesor_form = ProfesorForm(request.POST)
            estudiante_form = EstudianteForm()
            curso_form = CursoForm()
            if profesor_form.is_valid():
                profesor_form.save()
                messages.success(request, "Profesor creado correctamente.")
                return redirect(f"{request.path}?tab=profesores")
        elif active_tab == "cursos":
            curso_form = CursoForm(request.POST)
            estudiante_form = EstudianteForm()
            profesor_form = ProfesorForm()
            if curso_form.is_valid():
                curso_form.save()
                messages.success(request, "Curso creado correctamente.")
                return redirect(f"{request.path}?tab=cursos")
        else:
            estudiante_form = EstudianteForm()
            profesor_form = ProfesorForm()
            curso_form = CursoForm()
    else:
        estudiante_form = EstudianteForm()
        profesor_form = ProfesorForm()
        curso_form = CursoForm()

    estudiantes = Estudiante.objects.select_related("curso", "curso__sala_id").all()
    profesores = User.objects.filter(role=User.Roles.TEACHER).select_related("sala")
    cursos = Curso.objects.select_related("sala_id").all()

    context = {
        "active_tab": active_tab,
        "estudiante_form": estudiante_form,
        "profesor_form": profesor_form,
        "curso_form": curso_form,
        "estudiantes": estudiantes,
        "profesores": profesores,
        "cursos": cursos,
    }
    return render(request, "gestion.html", context)

def send_email(request, id):
    estudiante = get_object_or_404(Estudiante, pk=id)

    instrumento = Instrumento_evaluacion.objects.filter(
        estudiante_id=estudiante
    ).prefetch_related(
        'notas',
        'indicadores',
        'indicadores__asignatura',
        'adecuaciones'
    )

    nombre_estudiante = estudiante.first_name + " " + estudiante.last_name
    #notas = Nota.objects.filter(estudiante=estudiante.id)
    notas = []
    # PaciAppModel.objects.filter(student=estudiante)
    txt_notas = f"""

Notas del estudiante: {nombre_estudiante}\n
"""
    
    for item in instrumento:
        for nota in item.notas.all():
            txt_notas += f"- {nota.asignatura}: {nota}\n"

            promedio_final = item.notas.all().aggregate(promedio=Avg("nota"))

    txt_notas += f"\nPromedio: {round(promedio_final['promedio'], 1)}"

    para = request.POST.get("para")
    cuerpo_mensaje = request.POST.get("cuerpo_mensaje", "")
    asunto = request.POST.get("asunto")
    mensaje = cuerpo_mensaje + txt_notas
    enviar_correo_gmail(para, asunto, mensaje)

    context = {"estudiante": estudiante}
    return render(request, "correo.html", context)
