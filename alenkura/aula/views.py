import json
from io import BytesIO

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import Asignatura, Eje, Sala

from .models import ProyectoAula, ProyectoSubsector

try:  # pragma: no cover - optional dependency
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
        ListFlowable,
        ListItem,
    )
except ImportError:  # pragma: no cover
    colors = None
    letter = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None


def proyecto_view(request):
    """Formulario para crear un Proyecto de Aula con selección de aula, ejes y objetivos."""
    salas = Sala.objects.all().order_by("nombre_sala")
    ejes = Eje.objects.select_related("asignatura").all().order_by("asignatura__nombre", "nombre")
    selected_sala = None
    errors = []
    selected_ejes_ids = set()
    User = get_user_model()
    docentes = User.objects.filter(role=User.Roles.TEACHER).order_by("first_name", "last_name", "username")
    default_docente_id = (
        request.user.id
        if request.user.is_authenticated and getattr(request.user, "role", None) == User.Roles.TEACHER
        else None
    )
    selected_docente_id = None
    docente_por_defecto = (
        request.user.get_full_name()
        if request.user.is_authenticated and request.user.get_full_name()
        else (request.user.username if request.user.is_authenticated else "")
    )

    if request.method == "POST":
        sala_val = request.POST.get("sala")
        ejes_val = request.POST.getlist("ejes")

        docente_id_val = request.POST.get("docente_id")
        docente_obj = None
        if docente_id_val:
            try:
                selected_docente_id = int(docente_id_val)
                docente_obj = docentes.get(pk=selected_docente_id)
            except (ValueError, User.DoesNotExist):
                errors.append("El docente seleccionado no existe.")
        else:
            errors.append("Debes seleccionar un docente.")

        docente = (
            docente_obj.get_full_name() or docente_obj.username if docente_obj else docente_por_defecto
        )
        objetivos_inputs = [
            request.POST.get(f"obj_curricular_{i}", "").strip() for i in range(1, 5)
        ]
        objetivos_curriculares = "\n".join(
            f"{idx}. {texto}" for idx, texto in enumerate(objetivos_inputs, start=1) if texto
        )
        objetivo_general = request.POST.get("objetivo_general", "").strip()
        conocimientos = request.POST.get("conocimientos", "").strip()
        habilidades = request.POST.get("habilidades", "").strip()
        actitudes = request.POST.get("actitudes", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        procedimiento = request.POST.get("procedimiento", "").strip() or "Observación"
        instrumento = request.POST.get("instrumento", "").strip() or "Escala de apreciación"
        gantt_data_raw = request.POST.get("gantt_data", "").strip()
        try:
            json.loads(gantt_data_raw or "[]")
        except json.JSONDecodeError:
            gantt_data_raw = "[]"

        sala_obj = None
        if sala_val:
            try:
                selected_sala = int(sala_val)
                sala_obj = salas.get(pk=selected_sala)
            except (TypeError, ValueError, Sala.DoesNotExist):
                errors.append("El aula seleccionada no existe.")
        else:
            errors.append("Debes seleccionar un aula.")

        try:
            selected_ejes_ids = {int(value) for value in ejes_val}
        except ValueError:
            selected_ejes_ids = set()
            errors.append("Los ejes seleccionados no son válidos.")

        if not selected_ejes_ids:
            errors.append("Selecciona al menos un eje.")

        ejes_qs = (
            Eje.objects.select_related("asignatura")
            .filter(id__in=selected_ejes_ids)
            .order_by("asignatura__nombre", "nombre")
        )
        if ejes_qs.count() != len(selected_ejes_ids):
            errors.append("Alguno de los ejes seleccionados no existe.")

        if not errors and sala_obj:
            with transaction.atomic():
                proyecto = ProyectoAula.objects.create(
                    sala=sala_obj,
                    docente=docente,
                    objetivos_curriculares=objetivos_curriculares,
                    objetivo_general=objetivo_general,
                    conocimientos=conocimientos,
                    habilidades=habilidades,
                    actitudes=actitudes,
                    descripcion=descripcion,
                    procedimiento=procedimiento,
                    instrumento=instrumento,
                    gantt_data=gantt_data_raw,
                    profesional="",
                )
                # Deriva asignaturas desde los ejes seleccionados
                asignatura_ids = {eje.asignatura_id for eje in ejes_qs}
                proyecto.asignaturas.set(
                    Asignatura.objects.filter(id__in=asignatura_ids)
                )

                for eje in ejes_qs:
                    ProyectoSubsector.objects.create(
                        proyecto=proyecto,
                        eje=eje,
                        detalle_gantt="",
                        acciones="",
                        fechas="",
                    )

            messages.success(request, "Proyecto de aula creado correctamente.")
            return redirect("aula:proyecto_form")

    form_values = request.POST if request.method == "POST" else {}
    proyectos = (
        ProyectoAula.objects.select_related("sala")
        .prefetch_related("asignaturas", "subsectores__eje__asignatura")
        .order_by("-creado_en")
    )
    active_panel = request.GET.get("panel") or ""
    if request.method == "POST" or errors:
        active_panel = "crear"

    context = {
        "page_title": "Proyecto de Aula",
        "salas": salas,
        "ejes": ejes,
        "selected_sala": selected_sala,
        "docente_por_defecto": docente_por_defecto,
        "errors": errors,
        "form_values": form_values,
        "proyectos": proyectos,
        "selected_ejes_ids": list(selected_ejes_ids) if request.method == "POST" else [],
        "docentes": docentes,
        "selected_docente_id": selected_docente_id or default_docente_id,
        "active_panel": active_panel,
    }
    return render(request, "aula/proyecto.html", context)


def proyecto_download(request, pk: int) -> HttpResponse:
    proyecto = get_object_or_404(
        ProyectoAula.objects.select_related("sala").prefetch_related(
            "subsectores__eje__asignatura",
            "asignaturas",
        ),
        pk=pk,
    )
    lines = [
        f"Proyecto de Aula #{proyecto.pk}",
        f"Aula: {proyecto.sala}",
        f"Docente: {proyecto.docente or '-'}",
        "",
        "Objetivos curriculares:",
        proyecto.objetivos_curriculares or "-",
        "",
        f"Objetivo general: {proyecto.objetivo_general or '-'}",
        "",
        f"Conocimientos: {proyecto.conocimientos or '-'}",
        f"Habilidades: {proyecto.habilidades or '-'}",
        f"Actitudes: {proyecto.actitudes or '-'}",
        "",
        f"Descripción: {proyecto.descripcion or '-'}",
        "",
        f"Evaluación - Procedimiento: {proyecto.procedimiento or '-'}",
        f"Evaluación - Instrumento: {proyecto.instrumento or '-'}",
        "",
        "Subsectores seleccionados:",
    ]

    for subsector in proyecto.subsectores.all():
        eje = subsector.eje
        asignatura = eje.asignatura.nombre if eje.asignatura else "-"
        lines.append(f"- {asignatura} — {eje.nombre}")

    content = "\n".join(lines)
    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="proyecto_aula_{proyecto.pk}.txt"'
    return response


def proyecto_pdf(request, pk: int) -> HttpResponse:
    proyecto = get_object_or_404(
        ProyectoAula.objects.select_related("sala").prefetch_related(
            "subsectores__eje__asignatura",
            "asignaturas",
        ),
        pk=pk,
    )

    if SimpleDocTemplate is None or letter is None:
        return HttpResponse(
            "La librería reportlab no está instalada. Instálala con 'pip install reportlab' para generar el PDF.",
            status=500,
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=42,
        bottomMargin=36,
        title=f"Proyecto_Aula_{proyecto.pk}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "AulaTitle",
        parent=styles["Heading1"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "AulaHeading",
        parent=styles["Heading3"],
        fontSize=11,
        leading=13,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "AulaBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        spaceAfter=4,
    )

    def p(text: str) -> Paragraph:
        """Render paragraph preserving saltos de línea."""
        return Paragraph((text or "-").replace("\n", "<br/>"), body_style)

    months = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]

    def format_date(dt) -> str:
        if not dt:
            return "-"
        return f"{dt.day} de {months[dt.month - 1]} de {dt.year}"

    # Parse gantt early to derive fecha
    gantt_rows = []
    weeks_meta = []
    try:
        gantt_json = json.loads(proyecto.gantt_data or "[]")
    except json.JSONDecodeError:
        gantt_json = {}
    if isinstance(gantt_json, dict):
        weeks_meta = gantt_json.get("weeks", [])
        gantt_rows = gantt_json.get("rows", [])

    week_ranges_texts = [w.get("range", "") for w in weeks_meta if w.get("range")]
    if week_ranges_texts:
        fecha_text = f"{week_ranges_texts[0]} — {week_ranges_texts[-1]}" if len(week_ranges_texts) > 1 else week_ranges_texts[0]
    else:
        fecha_text = format_date(getattr(proyecto, "creado_en", None).date() if getattr(proyecto, "creado_en", None) else None)

    title_block = Table(
        [["PROYECTO DE AULA"]],
        colWidths=[470],
        style=TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        ),
    )
    story = [title_block, Spacer(1, 6)]

    subsectores_items = [
        ListItem(Paragraph(f"{sub.eje.asignatura.nombre if sub.eje.asignatura else '-'} — {sub.eje.nombre}", body_style), leftIndent=0)
        for sub in proyecto.subsectores.all()
    ]
    subsectores_flow = ListFlowable(
        subsectores_items or [Paragraph("-", body_style)],
        bulletType="bullet",
        start="•",
        leftIndent=12,
        bulletFontName="Helvetica",
        bulletFontSize=9,
    )

    header_table = Table(
        [
            ["Fecha:", fecha_text, "", ""],
            ["Curso:", str(proyecto.sala), "Subsectores:", subsectores_flow],
            ["Docentes:", proyecto.docente or "-", "Profesional:", proyecto.profesional or "-"],
        ],
        colWidths=[60, 170, 90, 150],
        hAlign="CENTER",
    )
    header_table.setStyle(
        TableStyle(
            [
                ("SPAN", (1, 0), (3, 0)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 8))

    objetivos_lines = [line.strip() for line in (proyecto.objetivos_curriculares or "").split("\n") if line.strip()]
    while len(objetivos_lines) < 4:
        objetivos_lines.append("")
    objetivos_cells = [p(text) for text in objetivos_lines[:4]]

    info_table_data = [
        ["Objetivos curriculares fundamentales del proyecto de aula", "", "", ""],
        objetivos_cells,
        ["Objetivo general del proyecto de aula", "", "", ""],
        [p(proyecto.objetivo_general), "", "", ""],
        ["Conocimientos", p(proyecto.conocimientos), "", ""],
        ["Habilidades", p(proyecto.habilidades), "", ""],
        ["Actitudes", p(proyecto.actitudes), "", ""],
        ["Descripción del proyecto", "", "", ""],
        [p(proyecto.descripcion), "", "", ""],
        ["Procedimiento", p(proyecto.procedimiento), "", ""],
        ["Instrumento", p(proyecto.instrumento), "", ""],
    ]

    info_table = Table(
        info_table_data,
        colWidths=[120, 116, 116, 116],
        hAlign="CENTER",
    )
    info_table.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (3, 0)),
                ("SPAN", (0, 0), (3, 0)),
                ("SPAN", (0, 2), (3, 2)),
                ("SPAN", (0, 3), (3, 3)),
                ("SPAN", (1, 4), (3, 4)),
                ("SPAN", (1, 5), (3, 5)),
                ("SPAN", (1, 6), (3, 6)),
                ("SPAN", (0, 7), (3, 7)),
                ("SPAN", (0, 8), (3, 8)),
                ("SPAN", (1, 9), (3, 9)),
                ("SPAN", (1, 10), (3, 10)),
                ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 2), (0, 10), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (3, 1), "Helvetica"),
                ("BACKGROUND", (0, 2), (3, 2), colors.whitesmoke),
                ("BACKGROUND", (0, 7), (3, 7), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 10))

    story.append(PageBreak())
    story.append(Paragraph("Planificación de las actividades", heading_style))
    story.append(Paragraph("Carta Gantt", heading_style))

    week_titles = []
    if weeks_meta:
        for w in weeks_meta:
            label = w.get("label", "")
            rango = w.get("range", "")
            week_titles.append(Paragraph(f"<b>{label}:</b><br/>{rango}", body_style))
    else:
        week_titles = [Paragraph(f"<b>Semana {i}</b>", body_style) for i in range(1, 5)]

    headers = [Paragraph("<b>Subsectores</b>", body_style), Paragraph("<b>Acciones</b>", body_style), *week_titles]

    table_data = [headers]
    span_cmds = []
    for row in gantt_rows:
        acciones = row.get("acciones") or []
        if not acciones:
            acciones = [{"texto": "", "semanas": []}]
        subsector_para = Paragraph(row.get("subsector", "-") or "-", body_style)
        start_idx = len(table_data)
        for idx, accion in enumerate(acciones):
            acciones_text = Paragraph(accion.get("texto") or "-", body_style)
            week_marks = ["X" if checked else "" for checked in (accion.get("semanas") or [])]
            if len(week_marks) < len(headers) - 2:
                week_marks.extend([""] * (len(headers) - 2 - len(week_marks)))
            table_data.append([subsector_para if idx == 0 else "", acciones_text, *week_marks])
        end_idx = len(table_data) - 1
        if end_idx > start_idx:
            span_cmds.append(("SPAN", (0, start_idx), (0, end_idx)))

    weeks_count = max(len(headers) - 2, 1)
    total_width = 750  # approximate drawable width in landscape with margins
    subsector_w = 150
    acciones_w = 200
    remaining = max(total_width - subsector_w - acciones_w, 300)
    week_w = max(int(remaining / weeks_count), 55)

    gantt_table = Table(
        table_data,
        colWidths=[subsector_w, acciones_w] + [week_w] * weeks_count,
        hAlign="CENTER",
    )
    gantt_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (2, 1), (-1, -1), "CENTER"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
            + span_cmds
        )
    )
    story.append(gantt_table)

    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename=\"proyecto_aula_{proyecto.pk}.pdf\"'
    response.write(pdf_value)
    return response


@require_POST
def proyecto_delete(request, pk: int):
    proyecto = get_object_or_404(ProyectoAula, pk=pk)
    proyecto.delete()
    messages.success(request, f"Proyecto #{pk} eliminado.")
    return redirect("aula:proyecto_form")
