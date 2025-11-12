from django.db import models
from django.core.exceptions import ValidationError

from core.models import DateTime, Asignatura, Eje, Estudiante

class PaciAppModel(DateTime):
    student = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='paci_student')
    subject = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='paci_subject')
    axis = models.ForeignKey(Eje, on_delete=models.CASCADE, related_name='paci_axis')
    objetivo_general = models.TextField()
    adecuacion_curricular = models.TextField()

    estrategias = models.TextField(blank=True)

    puntaje_total = models.SmallIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.student} - {self.subject} - {self.axis}'
    
    class Meta:
        verbose_name = "Paci App Model"
        verbose_name_plural = "Paci App Models"