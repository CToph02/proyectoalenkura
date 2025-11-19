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

    puntaje_total = models.SmallIntegerField(null=True)

    def __str__(self) -> str:
        return f'{self.student} - {self.subject} - {self.axis}'
    
    class Meta:
        verbose_name = "Paci App Model"
        verbose_name_plural = "Paci App Models"
