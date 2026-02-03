from core.models import Asignatura, Estudiante
from django.db import models
from paciApp.models import PaciAppModel

class Instrumento_evaluacion(models.Model):
    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.CASCADE,
        related_name="instrumento",
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.estudiante}"


class Nota(models.Model):
    instrumento = models.ForeignKey(
        Instrumento_evaluacion,
        on_delete=models.CASCADE,
        related_name="notas",
        null=True,
        blank=True
    )
    nota = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    asignatura = models.ForeignKey(
        Asignatura, on_delete=models.CASCADE, related_name="nota", null=True, blank=True
    )

    def __str__(self) -> str:
        return f"{self.nota}"


class Adecuacion_curricular(models.Model):
    instrumento = models.ForeignKey(
        Instrumento_evaluacion,
        on_delete=models.CASCADE,
        related_name="adecuaciones",
        null=True,
        blank=True
    )
    adecuacion = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.adecuacion}"


class Indicadores_instrumento(models.Model):
    instrumento = models.ForeignKey(
        Instrumento_evaluacion,
        on_delete=models.CASCADE,
        related_name="indicadores",
        null=True,
        blank=True,
    )
    indicador = models.CharField(max_length=150, null=True)
    puntaje_obtenido = models.SmallIntegerField(null=True, blank=True)
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name="indicadores",
        null=True,
        blank=True,
    )
    #logro = models.CharField(max_length=15, null=True)

    def __str__(self) -> str:
        return f"{self.indicador}"
