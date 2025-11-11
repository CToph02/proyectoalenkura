from django.db import models
from django.core.exceptions import ValidationError

from core.models import DateTime, Student, Subject, Axis

# Create your models here.
def validate_list_of_strings(value):
    if not isinstance(value, list):
        raise ValidationError("Estrategias debe ser una lista.")
    for i, v in enumerate(value):
        if not isinstance(v, str) or not v.strip():
            raise ValidationError(f"Estrategia #{i+1} debe ser un string no vacío.")

class PaciAppModel(DateTime):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='paci_student')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='paci_subject')
    axis = models.ForeignKey(Axis, on_delete=models.CASCADE, related_name='paci_axis')
    objetivo_general = models.TextField()
    adecuacion_curricular = models.TextField()

    estrategias = models.JSONField(default=list, blank=True, validators=[validate_list_of_strings])

    puntaje_total = models.SmallIntegerField()

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = "Paci App Model"
        verbose_name_plural = "Paci App Models"