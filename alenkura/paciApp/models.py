from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import User
from core.models import DateTime, Asignatura, Eje, Estudiante

class PaciAppModel(DateTime):
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    student = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='paci_student', null=True)
    subject = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='paci_subject', null=True)
    axis = models.ForeignKey(Eje, on_delete=models.CASCADE, related_name='paci_axis', null=True)
    objetivo_general = models.TextField(null=True)
    adecuacion_curricular = models.TextField(null=True)
    estrategias = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'{self.student} - {self.subject} - {self.axis}'

    class Meta:
        verbose_name = "Paci App Model"
        verbose_name_plural = "Paci App Models"

class Indicador(models.Model):
    indicador = models.CharField(max_length=150, null=True)
    paci = models.ForeignKey(PaciAppModel, on_delete=models.CASCADE, related_name='indicadores_paci', null=True)

    # class Meta:
    #     unique_together = ('paci', 'indicador')
    def __str__(self) -> str:
        return self.indicador or ""