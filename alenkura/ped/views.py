from io import BytesIO
from xml.sax.saxutils import escape

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import Asignatura, Curso

from .models import (
    Decreto,
    ObjetivoGeneral,
    PlanAsignatura,
    PlanEje,
    PlanEvaluacion,
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


def formulario_view(request):
    """Renderiza y procesa el formulario PED para planificar evaluaciones."""
    decretos = Decreto.objects.all()
    asignaturas = Asignatura.objects.prefetch_related('ejes').all()
    cursos = Curso.objects.all().order_by('name')
    selected_asignaturas = []
    selected_decreto = None
    selected_curso = None
    errors = []

    if request.method == "POST":
        decreto_value = request.POST.get("decreto")
        asignaturas_values = request.POST.getlist("asignaturas")
        curso_value = request.POST.get("curso")

        if decreto_value:
            try:
                selected_decreto = int(decreto_value)
            except (TypeError, ValueError):
                errors.append("El valor del decreto es inválido.")
        else:
            errors.append("Debes seleccionar un decreto.")

        if curso_value:
            try:
                selected_curso = int(curso_value)
            except (TypeError, ValueError):
                errors.append("El valor del curso es inválido.")
        else:
            errors.append("Debes seleccionar un curso.")

        try:
            selected_asignaturas = [int(value) for value in asignaturas_values]
            # Elimina duplicados manteniendo el orden original
            selected_asignaturas = list(dict.fromkeys(selected_asignaturas))
        except ValueError:
            selected_asignaturas = []
            errors.append("Los valores de asignaturas son inválidos.")

        if not selected_asignaturas:
            errors.append("Selecciona al menos una asignatura.")

        decreto_obj = None
        curso_obj = None
        asignaturas_qs = Asignatura.objects.filter(id__in=selected_asignaturas).prefetch_related('ejes')
        if selected_decreto:
            try:
                decreto_obj = decretos.get(pk=int(selected_decreto))
            except Decreto.DoesNotExist:
                errors.append("El decreto seleccionado no existe.")
        if selected_curso:
            try:
                curso_obj = cursos.get(pk=int(selected_curso))
            except Curso.DoesNotExist:
                errors.append("El curso seleccionado no existe.")

        if asignaturas_qs.count() != len(selected_asignaturas):
            errors.append("Alguna asignatura seleccionada no existe.")

        if not errors and decreto_obj and curso_obj:
            with transaction.atomic():
                plan = PlanEvaluacion.objects.create(
                    decreto=decreto_obj,
                    curso=curso_obj,
                    objetivo_general="",
                )

                for asignatura in asignaturas_qs:
                    selected_ejes = set(request.POST.getlist(f"ejes_{asignatura.id}"))
                    procedimiento = request.POST.get(f"procedimiento_{asignatura.id}", "").strip()
                    instrumento = request.POST.get(f"instrumento_{asignatura.id}", "").strip()
                    objetivo_asignatura = request.POST.get(f"objetivo_{asignatura.id}", "").strip()
                    plan_asignatura = PlanAsignatura.objects.create(
                        plan=plan,
                        asignatura=asignatura,
                        procedimiento=procedimiento,
                        instrumento=instrumento,
                    )
                    if objetivo_asignatura:
                        ObjetivoGeneral.objects.create(
                            descripcion=objetivo_asignatura,
                            plan=plan,
                            objAsignatura=asignatura,
                        )
                    for eje in asignatura.ejes.all():
                        contenido = request.POST.get(f"eje_{eje.id}", "").strip()
                        if str(eje.id) in selected_ejes and contenido:
                            PlanEje.objects.create(
                                plan_asignatura=plan_asignatura,
                                eje=eje,
                                contenido=contenido,
                            )

            messages.success(request, "Se guardó el formulario PED correctamente.")
            return redirect("ped:formulario")

    form_values = request.POST if request.method == "POST" else {}

    planes = PlanEvaluacion.objects.select_related('decreto', 'curso').prefetch_related(
        'plan_asignaturas__asignatura',
        'plan_asignaturas__plan_ejes__eje',
        'objetivos_generales',
    ).order_by('-creado_en')

    context = {
        "page_title": "Formulario PED",
        "decretos": decretos,
        "asignaturas": asignaturas,
        "cursos": cursos,
        "selected_asignaturas": selected_asignaturas,
        "selected_decreto": selected_decreto,
        "selected_curso": selected_curso,
        "errors": errors,
        "form_values": form_values,
        "planes": planes,
        "form_expanded": request.method == "POST" or bool(selected_asignaturas) or bool(errors),
    }
    return render(request, "ped/formulario.html", context)


def plan_pdf_view(request, plan_id):
    """Genera un PDF con el detalle del plan de evaluación seleccionado."""
    plan = get_object_or_404(
        PlanEvaluacion.objects.select_related('decreto', 'curso').prefetch_related(
            'plan_asignaturas__asignatura',
            'plan_asignaturas__plan_ejes__eje',
            'objetivos_generales',
        ),
        pk=plan_id,
    )

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
        title=f"PED_{plan.id}",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PEDTitle",
        parent=styles["Heading2"],
        alignment=1,
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=16,
        spaceAfter=10,
        textColor="#000000",
    )
    body_style = ParagraphStyle(
        "PEDBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        spaceAfter=0,
    )
    small_style = ParagraphStyle(
        "PEDSmall",
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

    objetivos_por_asignatura = {}
    for objetivo in plan.objetivos_generales.all():
        if objetivo.objAsignatura_id:
            objetivos_por_asignatura.setdefault(objetivo.objAsignatura_id, []).append(objetivo.descripcion)

    curso_text = plan.curso.name if plan.curso else "No asignado"
    nivel_text = plan.curso.get_level_display() if plan.curso else "No asignado"

    story = [
        Paragraph("PLAN DE EVALUACIÓN DIAGNÓSTICA", title_style),
    ]

    header_table = Table(
        [
            ["Curso:", curso_text, "Nivel:", nivel_text],
            ["Fecha:", plan.creado_en.strftime("%d/%m/%Y"), "", ""],
        ],
        colWidths=[90, 150, 80, 150],
    )
    header_table.setStyle(
        TableStyle(
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
    )
    story.append(header_table)
    story.append(Spacer(1, 12))

    table_data = [
        [
            Paragraph("Decreto", body_style),
            Paragraph("Asignatura", body_style),
            Paragraph("¿Qué evaluar?", body_style),
            Paragraph("¿Cómo evaluar?", body_style),
            Paragraph("¿Para qué evaluar?", body_style),
        ]
    ]

    for plan_asignatura in plan.plan_asignaturas.all():
        ejes = plan_asignatura.plan_ejes.all()
        if ejes:
            que_lines = []
            for plan_eje in ejes:
                que_lines.append(f"- {plan_eje.eje.nombre}:")
                if plan_eje.contenido:
                    que_lines.append(plan_eje.contenido)
                que_lines.append("")
            que_text = "\n".join(que_lines).strip()
        else:
            que_text = "Sin ejes definidos."

        como_lines = [
            "Procedimiento:",
            plan_asignatura.procedimiento or "-",
            "",
            "Instrumento:",
            plan_asignatura.instrumento or "-",
        ]
        como_text = "\n".join(como_lines).strip()

        objetivos = objetivos_por_asignatura.get(plan_asignatura.asignatura_id, [])
        if objetivos:
            para_text = "\n\n".join(objetivos)
        else:
            para_text = "Sin objetivos declarados."

        table_data.append(
            [
                build_paragraph(plan.decreto.nombre, small_style),
                build_paragraph(plan_asignatura.asignatura.nombre, small_style),
                build_paragraph(que_text, small_style),
                build_paragraph(como_text, small_style),
                build_paragraph(para_text, small_style),
            ]
        )

    if len(table_data) == 1:
        table_data.append(
            [
                build_paragraph(plan.decreto.nombre, small_style),
                build_paragraph("Sin asignaturas registradas", small_style),
                build_paragraph("-", small_style),
                build_paragraph("-", small_style),
                build_paragraph("-", small_style),
            ]
        )

    main_table = Table(
        table_data,
        colWidths=[90, 100, 150, 110, 100],
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
    response['Content-Disposition'] = f'attachment; filename="PED_{plan.id}.pdf"'
    return response


@require_POST
def plan_delete_view(request, plan_id):
    """Elimina un plan PED después de confirmar en la interfaz."""
    plan = get_object_or_404(PlanEvaluacion, pk=plan_id)
    plan.delete()
    messages.success(request, f"El plan #{plan_id} fue eliminado correctamente.")
    return redirect("ped:formulario")
