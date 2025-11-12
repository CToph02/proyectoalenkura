from django.db import models

from core.models import Asignatura, Eje


class Decreto(models.Model):
    nombre = models.CharField(max_length=150)

    def __str__(self):
        return self.nombre

class PlanEvaluacion(models.Model):
    decreto = models.ForeignKey(
        Decreto,
        on_delete=models.PROTECT,
        related_name='planes'
    )
    objetivo_general = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Plan {self.decreto.nombre} (#{self.pk})"


class PlanAsignatura(models.Model):
    plan = models.ForeignKey(
        PlanEvaluacion,
        on_delete=models.CASCADE,
        related_name='plan_asignaturas'
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='planes_evaluacion'
    )
    procedimiento = models.TextField(blank=True)
    instrumento = models.TextField(blank=True)

    class Meta:
        unique_together = ('plan', 'asignatura')

    def __str__(self):
        return f"{self.asignatura.nombre} - Plan {self.plan_id}"


class PlanEje(models.Model):
    plan_asignatura = models.ForeignKey(
        PlanAsignatura,
        on_delete=models.CASCADE,
        related_name='plan_ejes'
    )
    eje = models.ForeignKey(
        Eje,
        on_delete=models.CASCADE,
        related_name='planificaciones'
    )
    contenido = models.TextField()

    class Meta:
        unique_together = ('plan_asignatura', 'eje')

    def __str__(self):
        return f"{self.eje.nombre} - {self.plan_asignatura}"


class ObjetivoGeneral(models.Model):
    descripcion = models.TextField()
    objAsignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='objetivos_generales',
        null=True,
        blank=True
    )
    plan = models.ForeignKey(
        PlanEvaluacion,
        on_delete=models.CASCADE,
        related_name='objetivos_generales',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Objetivo General: {self.descripcion[:50]}..."
