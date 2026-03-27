
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
from core.models import Asignatura, Estudiante

try:  # pragma: no cover - import guard for optional dependency
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image
    
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
    Image = None

from io import BytesIO
from xml.sax.saxutils import escape


def get_student(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)
    return estudiante


def index(request, id, num=1):
    print("XD")
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
        "num_evaluacion": num,
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


def evaluar(request, id, num=1):
    estudiante = get_student(request, id)
    asignatura_qs = Asignatura.objects.all()
    mapa_asignaturas = {a.nombre: a for a in asignatura_qs}
    print(f"MAPA ASIGNATURA {mapa_asignaturas}")

    adecuaciones_list = []
    puntajes = []

    for key, value in request.POST.items():
        if key.startswith("csrfmiddlewaretoken"):
            continue
        print(key)
        if key.startswith("adecuaciones_"):
            adecuaciones_list.append(value)
        if key.startswith("puntaje_"):
            name_puntaje = key.split("_")
            asignatura = name_puntaje[1]
            indicador = "_".join(name_puntaje[2:])
            puntajes.append({"asignatura": asignatura, "indicador": indicador, "puntaje": value})
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
                numero_evaluacion=num,
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
            instrumento_evaluacion.indicadores.all().delete()
            for item in puntajes:
                asig_model = mapa_asignaturas.get(item["asignatura"])
                if asig_model:
                    Indicadores_instrumento.objects.create(
                        instrumento=instrumento_evaluacion,
                        indicador=item["indicador"],
                        asignatura=asig_model,
                        puntaje_obtenido=item["puntaje"],
                    )

    except Exception as e:
        print(f"Error en la transacción: {e}")

    return redirect("coreApp:estudiantes")

def ver_notas(request, id, num=1):
    estudiante = get_student(request, id)

    instrumentos = Instrumento_evaluacion.objects.filter(
        estudiante=estudiante,
        numero_evaluacion=num
    ).prefetch_related(
        'notas',
        'notas__asignatura',
        'indicadores',
        'indicadores__asignatura',
        'adecuaciones'
    )
    print(instrumentos)
    instrumento = instrumentos.first()

    asignaturas = Asignatura.objects.filter(
        paci_subject__student_id=estudiante.id
    ).distinct()

    notas_dict = {}
    for asig in asignaturas:
        notas_dict[asig.id] = {
            'asignatura': asig,
            'n1': None,
            'n2': None,
            'n3': None,
            'promedio': None,
            'suma': 0,
            'cantidad': 0
        }
        
    for inst in instrumentos:
        num = inst.numero_evaluacion
        if num not in [1, 2, 3]:
            continue
        for nota in inst.notas.all():
            asig_id = nota.asignatura_id
            if asig_id not in notas_dict:
                notas_dict[asig_id] = {
                    'asignatura': nota.asignatura,
                    'n1': None,
                    'n2': None,
                    'n3': None,
                    'promedio': None,
                    'suma': 0,
                    'cantidad': 0
                }
            val = float(nota.nota) if nota.nota else None
            notas_dict[asig_id][f'n{num}'] = val
            if val is not None:
                notas_dict[asig_id]['suma'] += val
                notas_dict[asig_id]['cantidad'] += 1

    promedio_general_suma = 0
    promedio_general_cantidad = 0

    for asig_id, data in notas_dict.items():
        if data['cantidad'] > 0:
            data['promedio'] = round(data['suma'] / data['cantidad'], 1)
            promedio_general_suma += data['promedio']
            promedio_general_cantidad += 1

    promedio_final = round(promedio_general_suma / promedio_general_cantidad, 1) if promedio_general_cantidad > 0 else 0

    a = notas_dict
    print(a)

    context = {
        "estudiante": estudiante,
        "instrumento": instrumento,
        "notas_asignaturas": notas_dict,
        "promedio_final": promedio_final,
    }

    return render(request, "notas.html", context)

def instrumento_pdf(request, id, num):
    estudiante = get_student(request, id)
    # Obtenemos el instrumento asociado al estudiante
    instrumento_qs = Instrumento_evaluacion.objects.filter(
        estudiante=estudiante,
        numero_evaluacion=num
    ).prefetch_related(
        'notas',
        'notas__asignatura',
        'indicadores',
        'indicadores__asignatura',
        'adecuaciones'
    )
    instrumento = instrumento_qs.first()

    if not instrumento:
        return HttpResponse("No se encontró un instrumento de evaluación para este estudiante.", status=404)

    if SimpleDocTemplate is None or letter is None:
        return HttpResponse(
            "La librería reportlab no está instalada. Instálala con 'pip install reportlab' para generar el PDF.",
            status=500,
        )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=40,
        bottomMargin=36,
        title=f"Evaluacion_{estudiante.first_name}",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "EvalTitle",
        parent=styles["Heading2"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        spaceAfter=10,
        textColor="#000000",
    )
    body_style = ParagraphStyle(
        "EvalBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        spaceAfter=0,
    )

    def build_paragraph(text, style=body_style, default="-"):
        """Devuelve un Paragraph escapando HTML y conservando saltos de línea."""
        value = (text or "").strip()
        if not value:
            value = default
        sanitized = escape(str(value))
        lines = sanitized.splitlines() or ["-"]
        html = "<br/>".join(line if line else "&nbsp;" for line in lines)
        return Paragraph(html, style)

    story = []
    
    logo_url = "https://images.builderservices.io/s/cdn/v1.0/i/m?url=https%3A%2F%2Fstorage.googleapis.com%2Fproduction-hostgator-chile-v1-0-3%2F573%2F1237573%2FEeoJHNah%2Fd473ee41415e43fc99acf1131253fde3&methods=resize%2C60%2C5000"
    try:
        logo = Image(logo_url, width=60, height=60)
        logo.hAlign = 'LEFT'
        story.append(logo)
        story.append(Spacer(1, 12))
    except Exception as e:
        print(f"Error al cargar logo: {e}")

    story.append(Paragraph(f"INFORME DE EVALUACIÓN {num}", title_style))
    
    # Datos de identificación
    nombre_estudiante = f"{estudiante.first_name} {estudiante.last_name}"
    curso_nombre = estudiante.curso.name if estudiante.curso else "Sin curso"
    
    from datetime import datetime
    fecha_emision = datetime.now().strftime("%d/%m/%Y")

    story.append(build_paragraph("I. Identificación del estudiante:"))
    story.append(Spacer(1, 6))

    estilos_tabla = TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#c6c6c6")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])

    t1 = Table([["Nombre:", nombre_estudiante]], colWidths=[120, 310])
    t1.setStyle(estilos_tabla)
    
    t2 = Table([["Curso:", curso_nombre, "Fecha emisión:", fecha_emision]], colWidths=[120, 115, 90, 105])
    t2.setStyle(estilos_tabla)

    story.append(t1)
    story.append(t2)
    story.append(Spacer(1, 12))

    # II. Resultados (Notas)
    story.append(build_paragraph("II. Resultados de Evaluación (Notas):"))
    story.append(Spacer(1, 6))

    notas_data = [[Paragraph("Asignatura", body_style), Paragraph("Nota", body_style)]]
    for nota in instrumento.notas.all():
        asig = nota.asignatura.nombre if nota.asignatura else "General"
        notas_data.append([build_paragraph(asig), build_paragraph(str(nota.nota))])

    if len(notas_data) > 1:
        t_notas = Table(notas_data, colWidths=[300, 100])
        t_notas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2d4c4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#000000")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#c6c6c6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfbfb")]),
        ]))
        story.append(t_notas)
    else:
        story.append(build_paragraph("No se registraron notas."))
    
    story.append(Spacer(1, 12))

    # III. Adecuaciones
    story.append(build_paragraph("III. Adecuaciones Curriculares:"))
    story.append(Spacer(1, 6))
    
    adecuaciones = instrumento.adecuaciones.all()
    if adecuaciones:
        for adec in adecuaciones:
            story.append(build_paragraph(f"• {adec.adecuacion}"))
    else:
        story.append(build_paragraph("No se registraron adecuaciones."))
    
    story.append(Spacer(1, 12))

    # IV. Indicadores
    story.append(build_paragraph("IV. Detalle de Indicadores:"))
    story.append(Spacer(1, 6))

    # Agrupamos indicadores por asignatura
    indicadores_list = sorted(instrumento.indicadores.all(), key=lambda x: x.asignatura.nombre if x.asignatura else "")
    grouped_indicadores = {}
    for ind in indicadores_list:
        asig = ind.asignatura.nombre if ind.asignatura else "General"
        if asig not in grouped_indicadores:
            grouped_indicadores[asig] = []
        grouped_indicadores[asig].append(ind)

    if not grouped_indicadores:
        story.append(build_paragraph("No se registraron indicadores."))
    else:
        ind_data = [[Paragraph("Asignatura", body_style), Paragraph("Indicador", body_style), Paragraph("Puntaje", body_style)]]
        spans = []
        row_idx = 1
        
        for asig, inds in grouped_indicadores.items():
            # Construimos tabla interna para los indicadores de esta asignatura
            inner_data = []
            for ind in inds:
                inner_data.append([
                    build_paragraph(ind.indicador),
                    build_paragraph(str(ind.puntaje_obtenido))
                ])
            
            t_inner = Table(inner_data, colWidths=[250, 60])
            t_inner.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#c6c6c6")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            
            # Agregamos la fila principal: Asignatura | Tabla Interna | (Espacio para SPAN)
            ind_data.append([
                build_paragraph(asig),
                t_inner,
                ""
            ])
            # Hacemos que la tabla interna ocupe las columnas 1 y 2 (Indicador y Puntaje)
            spans.append(('SPAN', (1, row_idx), (2, row_idx)))
            row_idx += 1

        t_ind = Table(ind_data, colWidths=[120, 250, 60], repeatRows=1)
        estilos = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2d4c4")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#000000")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#c6c6c6")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfbfb")]),
            ("LEFTPADDING", (0, 0), (0, -1), 6), # Padding solo para col Asignatura
            ("RIGHTPADDING", (0, 0), (0, -1), 6),
            ("TOPPADDING", (0, 0), (0, -1), 6),
            ("BOTTOMPADDING", (0, 0), (0, -1), 6),
            ("LEFTPADDING", (1, 1), (-1, -1), 0), # Sin padding para la tabla anidada
            ("RIGHTPADDING", (1, 1), (-1, -1), 0),
            ("TOPPADDING", (1, 1), (-1, -1), 0),
            ("BOTTOMPADDING", (1, 1), (-1, -1), 0),
        ]
        estilos.extend(spans)
        t_ind.setStyle(TableStyle(estilos))
        story.append(t_ind)

    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Evaluacion_{estudiante.first_name}.pdf"'
    return response
