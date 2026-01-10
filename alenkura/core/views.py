from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Exists, OuterRef

from .models import Curso, Estudiante
from paciApp.models import PaciAppModel
from instrumentosApp.models import Indicadores, Nota
from ped.models import PlanAsignatura
from .forms import CursoForm, EstudianteForm, ProfesorForm
from utils import enviar_correo_gmail

# Create your views here.

def index(request):
    return render(request, 'index.html')


def estudiantes_view(request):
    estudiantes = Estudiante.objects.all().annotate(
        tiene_paci=Exists(
            PaciAppModel.objects.filter(student=OuterRef('pk'))
        ),
        tiene_nota=Exists(
            Nota.objects.filter(estudiante=OuterRef('pk'))
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


def gestion_view(request):
    active_tab = request.GET.get('tab', 'estudiantes')
    User = get_user_model()

    if request.method == 'POST':
        active_tab = request.POST.get('active_tab', 'estudiantes')

        if active_tab == 'estudiantes':
            estudiante_form = EstudianteForm(request.POST)
            profesor_form = ProfesorForm()
            curso_form = CursoForm()
            if estudiante_form.is_valid():
                estudiante_form.save()
                messages.success(request, 'Estudiante creado correctamente.')
                return redirect(f'{request.path}?tab=estudiantes')
        elif active_tab == 'profesores':
            profesor_form = ProfesorForm(request.POST)
            estudiante_form = EstudianteForm()
            curso_form = CursoForm()
            if profesor_form.is_valid():
                profesor_form.save()
                messages.success(request, 'Profesor creado correctamente.')
                return redirect(f'{request.path}?tab=profesores')
        elif active_tab == 'cursos':
            curso_form = CursoForm(request.POST)
            estudiante_form = EstudianteForm()
            profesor_form = ProfesorForm()
            if curso_form.is_valid():
                curso_form.save()
                messages.success(request, 'Curso creado correctamente.')
                return redirect(f'{request.path}?tab=cursos')
        else:
            estudiante_form = EstudianteForm()
            profesor_form = ProfesorForm()
            curso_form = CursoForm()
    else:
        estudiante_form = EstudianteForm()
        profesor_form = ProfesorForm()
        curso_form = CursoForm()

    estudiantes = Estudiante.objects.select_related('curso', 'curso__sala_id').all()
    profesores = User.objects.filter(role=User.Roles.TEACHER)
    cursos = Curso.objects.select_related('sala_id').all()

    context = {
        'active_tab': active_tab,
        'estudiante_form': estudiante_form,
        'profesor_form': profesor_form,
        'curso_form': curso_form,
        'estudiantes': estudiantes,
        'profesores': profesores,
        'cursos': cursos,
    }
    return render(request, 'gestion.html', context)

def send_email(request, id):
    from django.core.mail import send_mail
    estudiante = get_object_or_404(Estudiante, pk=id)
    PaciAppModel.objects.filter(student=estudiante)

    para = request.POST.get('para')
    cuerpo_mensaje = request.POST.get('cuerpo_mensaje')
    asunto = request.POST.get('asunto')
    print(para)
    print(cuerpo_mensaje)
    enviar_correo_gmail(para, asunto, cuerpo_mensaje)

    # send_mail(
    #     "Asunto SMTP",
    #     "Texto plano",
    #     "cm38314@gmail.com",
    #     ["cm23456788@gmail.com"],
    #     html_message="<p>Hola</p>",
    #     fail_silently=False,
    # )

    context = {
        'estudiante':estudiante
    }
    return render(request, 'correo.html', context)
