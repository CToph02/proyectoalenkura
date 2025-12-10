from django.db import models
from paciApp.models import PaciAppModel

from core.models import Estudiante, Asignatura

# Create your models here.
class Indicadores(models.Model):
    indicador = models.CharField(max_length=150, null=True)
    puntaje = models.SmallIntegerField(null=True, blank=True)
    puntaje_obtenido = models.SmallIntegerField(null=True, blank=True)
    
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='asignatura', null=True, blank=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='estudiante', null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.indicador}'
    
class Nota(models.Model):
    nota = models.SmallIntegerField(null=True, blank=True)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='asignatura_nota', null=True, blank=True)
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='estudiante_nota', null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.nota}'