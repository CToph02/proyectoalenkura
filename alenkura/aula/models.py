from django.db import models

from core.models import Asignatura, Eje, Sala


class ProyectoAula(models.Model):
    sala = models.ForeignKey(
        Sala,
        on_delete=models.PROTECT,
        related_name="proyectos_aula",
    )
    asignaturas = models.ManyToManyField(
        Asignatura,
        related_name="proyectos_aula",
    )
    docente = models.CharField(max_length=150, blank=True)
    profesional = models.CharField(max_length=150, blank=True)
    objetivos_curriculares = models.TextField(blank=True)
    objetivo_general = models.TextField(blank=True)
    conocimientos = models.TextField(blank=True)
    habilidades = models.TextField(blank=True)
    actitudes = models.TextField(blank=True)
    descripcion = models.TextField(blank=True)
    procedimiento = models.CharField(max_length=120, default="Observador")
    instrumento = models.CharField(max_length=150, default="Escala de apreciacion")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Proyecto aula {self.sala} #{self.pk}"


class ProyectoSubsector(models.Model):
    proyecto = models.ForeignKey(
        ProyectoAula,
        on_delete=models.CASCADE,
        related_name="subsectores",
    )
    eje = models.ForeignKey(
        Eje,
        on_delete=models.CASCADE,
        related_name="proyectos_aula",
    )
    detalle_gantt = models.TextField(blank=True)
    acciones = models.TextField(blank=True)
    fechas = models.TextField(blank=True)

    class Meta:
        unique_together = ("proyecto", "eje")

    def __str__(self) -> str:
        return f"{self.eje.nombre} ({self.proyecto_id})"
