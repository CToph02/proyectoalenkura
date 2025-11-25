from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render

from core.models import Asignatura, Eje, Sala

from .models import ProyectoAula, ProyectoSubsector


def proyecto_view(request):
    """Formulario para crear un Proyecto de Aula con selección de aula, ejes y objetivos."""
    salas = Sala.objects.all().order_by("nombre_sala")
    ejes = Eje.objects.select_related("asignatura").all().order_by("asignatura__nombre", "nombre")
    selected_sala = None
    errors = []
    selected_ejes_ids = set()
    docente_por_defecto = (
        request.user.get_full_name()
        if request.user.is_authenticated and request.user.get_full_name()
        else (request.user.username if request.user.is_authenticated else "")
    )

    if request.method == "POST":
        sala_val = request.POST.get("sala")
        ejes_val = request.POST.getlist("ejes")

        docente = request.POST.get("docente", "").strip() or docente_por_defecto
        objetivos_inputs = [
            request.POST.get(f"obj_curricular_{i}", "").strip() for i in range(1, 5)
        ]
        objetivos_curriculares = "\n".join(
            f"{idx}. {texto}" for idx, texto in enumerate(objetivos_inputs, start=1) if texto
        )
        objetivo_general = request.POST.get("objetivo_general", "").strip()

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
                    profesional="",
                    conocimientos="",
                    habilidades="",
                    actitudes="",
                    descripcion="",
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

    context = {
        "page_title": "Proyecto de Aula",
        "salas": salas,
        "ejes": ejes,
        "selected_sala": selected_sala,
        "docente_por_defecto": docente_por_defecto,
        "errors": errors,
        "form_values": form_values,
        "proyectos": proyectos,
        "form_expanded": request.method == "POST" or bool(errors),
        "selected_ejes_ids": list(selected_ejes_ids) if request.method == "POST" else [],
    }
    return render(request, "aula/proyecto.html", context)
