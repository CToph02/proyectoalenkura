from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.models import Estudiante, Asignatura, Eje, Objetivos, Estrategias
from accounts.models import User
from .models import PaciAppModel, Indicador
import json


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

@login_required
def index(request, id):
    estudiante = get_object_or_404(Estudiante, pk=id)
    
    asignaturas = Asignatura.objects.prefetch_related('ejes').all()

    asignaturas_data = []
    for asignatura in asignaturas:
        
        ejes_list = list(asignatura.ejes.all().values('id', 'nombre'))
        asignaturas_data.append({
            'id': asignatura.id,
            'nombre': asignatura.nombre,
            'ejes': ejes_list
        })
    
    context = {
        'estudiante': estudiante,
        'asignaturas_json': json.dumps(asignaturas_data),
        'asignaturas': asignaturas,
        'objetivos': Objetivos.objects.all(),
        'estrategias': Estrategias.objects.all()
    }
    return render(request, 'paci.html', context)

@login_required
def create_paci(request, id):
    if request.method == 'POST':
        estudiante = get_object_or_404(Estudiante, pk=id)
        asignaturas = Asignatura.objects.all()
        
        try:
            with transaction.atomic():
                for asig in asignaturas:
                    # IMPORTANTE: Esto busca el input con el name modificado en el HTML
                    # name="ejes_seleccionados_{{asignatura.id}}"
                    ejes_ids = request.POST.getlist(f'ejes_seleccionados_{asig.id}')
                    
                    if not ejes_ids:
                        continue # Si no eligió ejes para esta asignatura, pasamos a la siguiente

                    # Iteramos por cada ID de Eje seleccionado
                    for eje_id in ejes_ids:
                        
                        # Definimos las claves para buscar en el POST según el formato de tu JS
                        # Formato: nombre_campo + "_" + ID_Asignatura + "_" + ID_Eje
                        key_adecuacion = f'adecuacion_{asig.id}_{eje_id}'
                        key_objetivo = f'objetivos_{asig.id}_{eje_id}'
                        key_estrategias = f'estrategias_{asig.id}_{eje_id}'
                        key_indicadores_json = f'indicadores_json_{asig.id}_{eje_id}'

                        # Obtenemos valores
                        adecuacion = request.POST.get(key_adecuacion)
                        objetivo = request.POST.get(key_objetivo)
                        
                        # Validamos que al menos haya algo que guardar
                        if not adecuacion and not objetivo:
                            continue

                        # Procesar estrategias (lista a string)
                        estrategias_lista = request.POST.getlist(key_estrategias)
                        estrategias_str = ", ".join(estrategias_lista)

                        # Buscamos la instancia del Eje para la Foreign Key
                        eje_instancia = get_object_or_404(Eje, pk=eje_id)

                        # Creamos el PACI usando tu modelo PaciAppModel
                        paci = PaciAppModel.objects.create(
                            profesor=request.user,
                            student=estudiante,
                            subject=asig,
                            axis=eje_instancia,  # Aquí asignamos el eje
                            objetivo_general=objetivo,
                            adecuacion_curricular=adecuacion,
                            estrategias=estrategias_str
                        )

                        # Procesar Indicadores (vienen como JSON string desde el JS)
                        indicadores_json_str = request.POST.get(key_indicadores_json)
                        
                        if indicadores_json_str:
                            try:
                                # Convertimos string JSON a lista Python
                                indicadores_lista = json.loads(indicadores_json_str)
                                
                                for texto_indicador in indicadores_lista:
                                    if texto_indicador.strip():
                                        # Usamos el modelo Indicador (singular)
                                        Indicador.objects.create(
                                            indicador=texto_indicador,
                                            paci=paci
                                        )
                            except json.JSONDecodeError:
                                print(f"Error decodificando JSON para Asig {asig.id} Eje {eje_id}")

                return redirect('coreApp:estudiantes')

        except Exception as e:
            print(f"Error CRÍTICO al guardar PACI: {e}")
            return HttpResponse(f"Error al guardar: {e}", status=500)

    return redirect('coreApp:estudiantes')

def pdf_paci(request, id):
    estudiante = get_object_or_404(Estudiante, id=id)
    paci = PaciAppModel.objects.filter(
            student=estudiante.id
        ).select_related(
            'profesor', 'student', 'subject', 'axis'
        ).prefetch_related(
            'indicadores_paci'
        )
    # asignaturas = [
    #     p.subject.nombre 
    #     for p in PaciAppModel.objects.filter(
    #         student=estudiante.id
    #         )
    # ]

    fecha_creacion = paci.first().created_at.strftime("%d/%m/%Y")

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
        title=f"PACI_{estudiante.first_name}",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PACITitle",
        parent=styles["Heading2"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        spaceAfter=10,
        textColor="#000000",
    )
    body_style = ParagraphStyle(
        "PACIBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        spaceAfter=0,
    )
    small_style = ParagraphStyle(
        "PACISmall",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
    )

    def build_paragraph(text, style=body_style, default="-"):
        """Devuelve un Paragraph escapando HTML y conservando saltos de línea."""
        value = (text or "").strip()
        if not value:
            value = default
        sanitized = escape(value)
        lines = sanitized.splitlines() or ["-"]
        html = "<br/>".join(line if line else "&nbsp;" for line in lines)
        return Paragraph(html, style)

    story = [Paragraph("PLAN DE ADECUACIÓN CURRICULAR INDIVIDUAL (P.A.C.I.)", title_style)]
    nombre_estudiante = estudiante.first_name + " " + estudiante.last_name
    story.append(build_paragraph("I. Identificador del estudiante:"))
    story.append(Spacer(1, 6))
    
    estilos=TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#c6c6c6")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    t1 = Table([["Nombre:", nombre_estudiante]], colWidths=[120,310])
    t1.setStyle(estilos)

    t2 = Table([["Fecha de nacimiento:",estudiante.birth_date, "Edad:", estudiante.edad]], colWidths=[120,115,60,135])
    t2.setStyle(estilos)

    t3 = Table([["Diagnóstico B.A.P:", estudiante.bapDiag]], colWidths=[120,310])
    t3.setStyle(estilos)

    t4 = Table([["Curso:", estudiante.curso.name, "Nivel:", estudiante.nivel]], colWidths=[120,115,60,135])
    t4.setStyle(estilos)

    t5 = Table([["Fecha de elaboración:", fecha_creacion]], colWidths=[120,310])
    t5.setStyle(estilos)
    
    story.append(t1)
    story.append(t2)
    story.append(t3)
    story.append(t4)
    story.append(t5)
    story.append(Spacer(1, 12))

    story.append(build_paragraph("II. Propuesta curricular:"))
    story.append(Spacer(1, 6))
    # 1. Definimos el encabezado de la tabla (6 Columnas)
    table_data = [
        [
            Paragraph("Asignatura", body_style),
            Paragraph("Eje", body_style),
            Paragraph("Objetivo", body_style),
            Paragraph("Adecuación", body_style),
            Paragraph("Indicadores", body_style), # <--- Columna 5
            Paragraph("Estrategias", body_style), # <--- Columna 6
        ]
    ]

    # 2. Iteramos SOLO sobre los objetos PACI (Ya tienen todo vinculado)
    for item_paci in paci:
        
        # A. Procesamos los indicadores para ponerlos en una sola celda
        # Obtenemos los indicadores relacionados a este item específico
        lista_indicadores = []
        for ind in item_paci.indicadores_paci.all():
            lista_indicadores.append(f"• {ind.indicador}")
        
        # Los unimos con saltos de línea HTML (<br/>) para el Paragraph
        texto_indicadores = "\n".join(lista_indicadores) if lista_indicadores else "Sin indicadores"

        # B. Construimos la fila (Debe tener 6 elementos, igual que el encabezado)
        row = [
            build_paragraph(item_paci.subject.nombre if item_paci.subject else "Sin Asignatura"),
            build_paragraph(item_paci.axis.nombre if item_paci.axis else "Sin Eje"),
            build_paragraph(item_paci.objetivo_general),
            build_paragraph(item_paci.adecuacion_curricular),
            build_paragraph(texto_indicadores),     # <--- Aquí van los indicadores procesados
            build_paragraph(item_paci.estrategias),
        ]
        table_data.append(row)

    # 3. Configuración de la Tabla
    # IMPORTANTE: colWidths debe tener 6 valores y sumar aprox 540 (ancho carta - márgenes)
    main_table = Table(
        table_data,
        colWidths=[70, 70, 100, 100, 100, 100], # Ajustado para 6 columnas
        repeatRows=1,
    )

    main_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2d4c4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#000000")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#c6c6c6")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfbfb")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    
    story.append(main_table)
    
    doc.build(story)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PACI_{estudiante.first_name}.pdf"'
    return response