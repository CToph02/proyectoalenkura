from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Prefetch
from django.db import transaction
from paciApp.models import PaciAppModel, Indicador
from .models import Indicadores, Nota
from core.models import Estudiante, Asignatura
# Create your views here.
def get_student(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)
    return estudiante

def index(request, id):
    estudiante = get_student(request, id)

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

def puntaje_total_asignatura(asignatura, indicadores):
    puntaje_total_asignatura = {asig.nombre: 0 for asig in asignatura}

    for indi in indicadores:
        indicadores_x_asignatura = indi.paci.subject.nombre
        if indicadores_x_asignatura in puntaje_total_asignatura:
            puntaje_total_asignatura[indicadores_x_asignatura] += 4

    puntaje_corte = {asignatura: puntaje * 0.6 for asignatura, puntaje in puntaje_total_asignatura.items()}

    return [puntaje_total_asignatura, puntaje_corte]

def calcular_nota(pjes:dict, pje_alumno:dict) -> dict:
    notas_finales = {}

    dict_pjes_max = pjes[0]
    dict_pjes_corte = pjes[1]

    for asig, pje_obtenido in pje_alumno.items():
        pje_corte = dict_pjes_corte[asig]
        pje_max = dict_pjes_max[asig]

        if pje_max == 0:
            notas_finales[asig] = 1.0
            continue

        if pje_obtenido < pje_corte:
            nota = 1 + 3 * (pje_obtenido / pje_corte)

        else:
            remanente_alumno = pje_obtenido - pje_corte
            remanente_total =  pje_max - pje_corte
            nota = 4 + 3 * ( remanente_alumno / remanente_total)
        notas_finales[asig] = round(nota, 1)
    return notas_finales

def evaluar(request, id):
    estudiante = get_student(request, id)
    asignatura_qs = Asignatura.objects.all()
    indicadores_estudiante = Indicador.objects.filter(paci__student=estudiante)
    
    mapa_asignaturas = {a.nombre: a for a in asignatura_qs}
    
    # Usamos floats para permitir decimales en la suma
    pje_asignatura = {asig.nombre: 0.0 for asig in asignatura_qs} 
    pjes = puntaje_total_asignatura(asignatura_qs, indicadores_estudiante)

    if request.method == "POST":
        for key, value in request.POST.items():
            if key.startswith("csrfmiddlewaretoken"):
                continue

            if "puntaje" in key:
                parts = key.split('_')
                asignatura_nombre = parts[0]
                indicador_nombre = parts[2]
                
                # Verificación rápida
                if indicadores_estudiante.filter(indicador=indicador_nombre).exists():
                     pje_asignatura[asignatura_nombre] += float(value)

        notas = calcular_nota(pjes, pje_asignatura)
        print(notas)
        
        try:
            with transaction.atomic():
                # ELIMINAMOS EL BUCLE "for indi in indicadores..." 
                # No es necesario crear indicadores nuevos para guardar la nota final.

                for asig_nombre, valor_nota in notas.items():
                    asig_obj = mapa_asignaturas.get(asig_nombre)
                    
                    if asig_obj:
                        # AQUÍ ESTÁ LA CORRECCIÓN CLAVE:
                        obj, created = Nota.objects.update_or_create(
                            # 1. CRITERIOS DE BÚSQUEDA (¿Quién es?)
                            estudiante=estudiante,
                            asignatura=asig_obj,
                            
                            # 2. VALORES A ACTUALIZAR (¿Qué dato cambia?)
                            defaults={
                                'nota': float(valor_nota),
                                # Recomendación: Dejar indicador en None para nota final de asignatura
                                'indicador': None 
                            }
                        )
                        print(f"Asignatura: {asig_nombre} | Nota: {valor_nota} | {'Creada' if created else 'Actualizada'}")
                    else:
                        print(f"No se encontró objeto asignatura para: {asig_nombre}")

        except Exception as e:
            print(f"Error al guardar: {e}")
    
    return redirect('coreApp:estudiantes')

def ver_notas(request, id):
    estudiante = get_student(request, id)
    notas = Nota.objects.filter(estudiante=estudiante.id)
    asignaturas = (
        Asignatura.objects
            .filter(
                paci_subject__student_id=estudiante.id
            )
        ).distinct()
    context = {
        'estudiante': estudiante,
        'notas': notas,
        'asignaturas': asignaturas
    }
    return render(request, "notas.html", context)