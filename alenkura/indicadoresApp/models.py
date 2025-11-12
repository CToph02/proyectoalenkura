from django.db import models
from paciApp.models import PaciAppModel

from core.models import Estudiante, Asignatura
from accounts.models import User

# Create your models here.
class Indicadores(models.Model):
    profesor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profesor')
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='estudiante')
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE, related_name='asignatura')

    indicador = models.CharField(max_length=150)
    puntaje = models.SmallIntegerField(null=True, blank=True)
    puntaje_obtenido = models.SmallIntegerField(null=True, blank=True)
    
    paci = models.ForeignKey(PaciAppModel, on_delete=models.CASCADE, related_name='paci', null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.indicador}'