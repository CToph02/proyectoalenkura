from io import BytesIO

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Asignatura

from .models import (
    Decreto,
    ObjetivoGeneral,
    PlanAsignatura,
    PlanEje,
    PlanEvaluacion,
)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover - only triggered when lib missing
    canvas = None
    letter = None


def formulario_view(request):
    """Renderiza y procesa el formulario PED para planificar evaluaciones."""
    decretos = Decreto.objects.all()
    asignaturas = Asignatura.objects.prefetch_related('ejes').all()
    selected_asignaturas = []
    selected_decreto = None
    errors = []

    if request.method == "POST":
        decreto_value = request.POST.get("decreto")
        asignaturas_values = request.POST.getlist("asignaturas")

        if decreto_value:
            try:
                selected_decreto = int(decreto_value)
            except (TypeError, ValueError):
                errors.append("El valor del decreto es inválido.")
        else:
            errors.append("Debes seleccionar un decreto.")

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
        asignaturas_qs = Asignatura.objects.filter(id__in=selected_asignaturas).prefetch_related('ejes')
        if selected_decreto:
            try:
                decreto_obj = decretos.get(pk=int(selected_decreto))
            except Decreto.DoesNotExist:
                errors.append("El decreto seleccionado no existe.")

        if asignaturas_qs.count() != len(selected_asignaturas):
            errors.append("Alguna asignatura seleccionada no existe.")

        if not errors and decreto_obj:
            with transaction.atomic():
                plan = PlanEvaluacion.objects.create(
                    decreto=decreto_obj,
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

    planes = PlanEvaluacion.objects.select_related('decreto').prefetch_related(
        'plan_asignaturas__asignatura',
        'plan_asignaturas__plan_ejes__eje',
        'objetivos_generales',
    ).order_by('-creado_en')

    context = {
        "page_title": "Formulario PED",
        "decretos": decretos,
        "asignaturas": asignaturas,
        "selected_asignaturas": selected_asignaturas,
        "selected_decreto": selected_decreto,
        "errors": errors,
        "form_values": form_values,
        "planes": planes,
    }
    return render(request, "ped/formulario.html", context)


def plan_pdf_view(request, plan_id):
    """Genera un PDF con el detalle del plan de evaluación seleccionado."""
    plan = get_object_or_404(
        PlanEvaluacion.objects.select_related('decreto').prefetch_related(
            'plan_asignaturas__asignatura',
            'plan_asignaturas__plan_ejes__eje',
            'objetivos_generales',
        ),
        pk=plan_id,
    )

    if canvas is None or letter is None:
        return HttpResponse(
            "La librería reportlab no está instalada. Instálala con 'pip install reportlab' para generar el PDF.",
            status=500,
        )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    left_margin = 40
    right_margin = width - 40
    y_position = height - 50

    def draw_text(text, bold=False, leading=14):
        nonlocal y_position
        if y_position <= 60:
            pdf.showPage()
            pdf.setFont("Helvetica-Bold", 12)
            y_position = height - 50
        font = "Helvetica-Bold" if bold else "Helvetica"
        pdf.setFont(font, 11)
        wrapped = []
        max_chars = int((right_margin - left_margin) / 6)
        for paragraph in text.splitlines() or [""]:
            while len(paragraph) > max_chars:
                wrapped.append(paragraph[:max_chars])
                paragraph = paragraph[max_chars:]
            wrapped.append(paragraph)
        for line in wrapped:
            pdf.drawString(left_margin, y_position, line)
            y_position -= leading

    pdf.setTitle(f"PED_{plan.id}")
    draw_text(f"Plan de Evaluación #{plan.id}", bold=True, leading=18)
    draw_text(f"Decreto: {plan.decreto.nombre}")
    draw_text(f"Creado: {plan.creado_en.strftime('%d/%m/%Y %H:%M')}")
    draw_text("")

    objetivos_por_asignatura = {}
    for objetivo in plan.objetivos_generales.all():
        if objetivo.objAsignatura_id:
            objetivos_por_asignatura.setdefault(objetivo.objAsignatura_id, []).append(objetivo.descripcion)

    for plan_asignatura in plan.plan_asignaturas.all():
        draw_text(f"Asignatura: {plan_asignatura.asignatura.nombre}", bold=True, leading=16)
        if plan_asignatura.procedimiento:
            draw_text("Procedimiento:", bold=True)
            draw_text(plan_asignatura.procedimiento)
        if plan_asignatura.instrumento:
            draw_text("Instrumento:", bold=True)
            draw_text(plan_asignatura.instrumento)

        ejes = plan_asignatura.plan_ejes.all()
        if ejes:
            draw_text("¿Qué evaluar?", bold=True)
            for plan_eje in ejes:
                draw_text(f"- {plan_eje.eje.nombre}")
                draw_text(plan_eje.contenido)

        objetivos = objetivos_por_asignatura.get(plan_asignatura.asignatura_id, [])
        if objetivos:
            draw_text("¿Para qué evaluar?", bold=True)
            for objetivo in objetivos:
                draw_text(objetivo)

        draw_text("")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PED_{plan.id}.pdf"'
    return response
