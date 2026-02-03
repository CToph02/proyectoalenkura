from core.models import Asignatura, Estudiante
from django.db import transaction
from django.db.models import Avg, Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from paciApp.models import Indicador_paci, PaciAppModel
import json
from .models import (
    Adecuacion_curricular,
    Indicadores_instrumento,
    Instrumento_evaluacion,
    Nota,
)

try:  # pragma: no cover - import guard for optional dependency
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError:  # pragma: no cover - only triggered when lib missing
    colors = None
    letter = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None

from io import BytesIO
from xml.sax.saxutils import escape


def get_student(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)
    return estudiante


def index(request, id):
    estudiante = get_student(request, id)

    indicadores_paci = Indicador_paci.objects.filter(paci__student=estudiante)

    paci_estudiante = (
        PaciAppModel.objects.filter(student_id=estudiante.id)
        .select_related("axis", "subject")
        .prefetch_related(
            Prefetch(
                "indicadores_paci",  # relación existente en tu modelo
                queryset=Indicador_paci.objects.all(),  # opcional: añadir filtros si los necesitas
                to_attr="indicadores",  # cada PaciAppModel tendrá .indicadores
            )
        )
    )
    asignaturas = (
        Asignatura.objects.filter(
            paci_subject__student_id=estudiante.id
        ).prefetch_related(
            Prefetch(
                "paci_subject", queryset=paci_estudiante, to_attr="paci_estudiante"
            )
        )
    ).distinct()

    asignaturas_data = []

    for asig in asignaturas:
        asignaturas_data.append({"id": asig.id, "nombre": asig.nombre})
    context = {
        "indicadores_paci": indicadores_paci,
        "estudiante": estudiante,
        "asignatura": asignaturas,
        "asignaturas": json.dumps(asignaturas_data),
    }
    return render(request, "indicadores.html", context)

def calcular_nota(pjes: dict, pje_alumno: dict) -> dict:
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
            remanente_total = pje_max - pje_corte
            nota = 4 + 3 * (remanente_alumno / remanente_total)
        notas_finales[asig] = round(nota, 1)
    return notas_finales


def evaluar(request, id):
    estudiante = get_student(request, id)
    asignatura_qs = Asignatura.objects.all()
    mapa_asignaturas = {a.nombre: a for a in asignatura_qs}
    print(f"MAPA ASIGNATURA {mapa_asignaturas}")

    adecuaciones_list = []
    puntajes = {}

    for key, value in request.POST.items():
        if key.startswith("csrfmiddlewaretoken"):
            continue
        print(key)
        if key.startswith("adecuaciones_"):
            adecuaciones_list.append(value)
        if key.startswith("puntaje_"):
            name_puntaje = key.split("_")
            asignatura = name_puntaje[1]
            indicador = name_puntaje[2]
            if indicador not in puntajes:
                puntajes[asignatura] = {}
            puntajes[asignatura]["indicador"] = indicador
            puntajes[asignatura]["puntaje"] = value
            print(
                f"INDICADOR: {indicador} - ASIGNATURA: {asignatura} - PUNTAJE: {value}"
            )
    print(adecuaciones_list)
    print(puntajes)

    pje_alumno = {}
    dict_pjes_max = {}

    for asig in asignatura_qs:
        json_data = request.POST.get(f"json_asig_{asig.id}")
        if json_data:
            try:
                indicadores_seleccionados = json.loads(json_data)

                dict_pjes_max[asig.nombre] = len(indicadores_seleccionados) * 4

                suma_puntos = sum(
                    int(item.get("puntaje", 0)) for item in indicadores_seleccionados
                )
                pje_alumno[asig.nombre] = suma_puntos
            except json.JSONDecodeError:
                dict_pjes_max[asig.nombre] = 0
                pje_alumno[asig.nombre] = 0
        else:
            dict_pjes_max[asig.nombre] = 0
            pje_alumno[asig.nombre] = 0

    dict_pjes_corte = {nombre: p_max * 0.6 for nombre, p_max in dict_pjes_max.items()}

    pjes_para_calcular = [dict_pjes_max, dict_pjes_corte]

    notas = calcular_nota(pjes_para_calcular, pje_alumno)
    print(notas)
    try:
        with transaction.atomic():
            # ---------------------------------------------------------
            # PASO 1: Gestionar Instrumento (El Contenedor Principal)
            # ---------------------------------------------------------
            # Ya no pasamos 'nota=' porque el campo fue eliminado del modelo Instrumento.
            instrumento_evaluacion, created = Instrumento_evaluacion.objects.get_or_create(
                estudiante=estudiante,
                defaults={} # Puedes agregar otros campos default aquí si tienes (ej. fecha)
            )

            # ---------------------------------------------------------
            # PASO 2: Gestionar Notas (AHORA SON MÚLTIPLES)
            # ---------------------------------------------------------
            # Iteramos por TODAS las asignaturas que vienen del formulario
            for asignatura_nombre, valor_nota in notas.items():
                asig_obj = mapa_asignaturas.get(asignatura_nombre)

                if asig_obj:
                    # Buscamos si ya existe nota para ESTA asignatura en ESTE instrumento
                    Nota.objects.update_or_create(
                        instrumento=instrumento_evaluacion, # Vínculo al padre
                        asignatura=asig_obj,
                        defaults={'nota': valor_nota} # Actualizamos el valor
                    )

            # ---------------------------------------------------------
            # PASO 3: Gestionar Adecuaciones (Igual que definimos antes)
            # ---------------------------------------------------------
            # 1. Borramos las existentes para este instrumento (evita duplicados/basura)
            instrumento_evaluacion.adecuaciones.all().delete()

            # 2. Creamos las nuevas
            for texto_adecuacion in adecuaciones_list:
                if texto_adecuacion:
                    Adecuacion_curricular.objects.create(
                        instrumento=instrumento_evaluacion,
                        adecuacion=texto_adecuacion
                    )

            # ---------------------------------------------------------
            # PASO 4: Guardar Indicadores (Se mantiene igual)
            # ---------------------------------------------------------
            for asig_nombre, info in puntajes.items():
                asig_model = mapa_asignaturas.get(asig_nombre)
                if asig_model:
                    Indicadores_instrumento.objects.update_or_create(
                        instrumento=instrumento_evaluacion,
                        indicador=info.get("indicador"),
                        asignatura=asig_model,
                        defaults={"puntaje_obtenido": info.get("puntaje")},
                    )

    except Exception as e:
        print(f"Error en la transacción: {e}")

    return redirect("coreApp:estudiantes")

def ver_notas(request, id):
    estudiante = get_student(request, id)

    instrumentos = Instrumento_evaluacion.objects.filter(
        estudiante=estudiante
    ).prefetch_related(
        'notas',
        'notas__asignatura',
        'indicadores',
        'indicadores__asignatura',
        'adecuaciones'
    )

    notas_queryset = Nota.objects.filter(
        instrumento__estudiante=estudiante
    ).select_related('asignatura')

    promedio_final = notas_queryset.aggregate(promedio=Avg("nota"))
    valor_promedio = promedio_final["promedio"] if promedio_final["promedio"] else 0

    asignaturas = Asignatura.objects.filter(
        paci_subject__student_id=estudiante.id
    ).distinct()

    context = {
        "estudiante": estudiante,
        "instrumentos": instrumentos,
        "notas": notas_queryset,
        "promedio": round(valor_promedio, 1),
        "asignaturas": asignaturas,
    }

    return render(request, "notas.html", context)


def instrumento_pdf(request, id):
    estudiante = get_student(request, id)
    instrumento = Instrumento_evaluacion.objects.filter(
        estudiante_id=estudiante
    ).prefetch_related(
        'notas',
        'indicadores',
        'indicadores__asignatura',
        'adecuaciones'
    )

    paci = PaciAppModel.objects.filter(student_id=estudiante)

    for p in paci.all():
        print(f"Objetivo general: {p.objetivo_general} - Adecuación curricular: {p.adecuacion_curricular}")

    for items in instrumento:
        for i in items.indicadores.all():
            print(f"Indicador: {i} - Puntaje: {i.puntaje_obtenido}")
        for n in items.notas.all():
            print(f"Nota: {n} - Asignatura: {n.asignatura}")
    return HttpResponse(instrumento)
