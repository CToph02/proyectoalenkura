from django.db import models
from accounts.models import User
import re

class DateTime(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Asignatura(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
class Estrategias(models.Model):
    estrategia = models.CharField(max_length=100)

    def __str__(self):
        return self.estrategia

class Objetivos(models.Model):
    objetivo = models.TextField()

    def __str__(self):
        return self.objetivo

class Eje(models.Model):
    nombre = models.CharField(max_length=100)
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='ejes'
    )

    def __str__(self):
        return f"{self.nombre} ({self.asignatura.nombre})"


class Contenido(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    eje = models.ForeignKey(
        Eje,
        on_delete=models.CASCADE,
        related_name='contenidos'
    )

    def __str__(self):
        return f"{self.nombre} ({self.eje.nombre})"

class Nivel(models.TextChoices):
    BASIC = 'BASICO', 'Básico'
    LABORAL = 'LABORAL', 'Laboral'

class Sala(models.Model):
    nombre_sala = models.CharField(max_length=50, null=False)
    teachers = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profesor', blank=True, null=True)

    def __str__(self):
        return f'{self.nombre_sala}'

class Curso(DateTime):
    level = models.CharField(max_length=10, choices=Nivel.choices, default=Nivel.BASIC)
    name = models.CharField(max_length=25)
    sala_id = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name='sala', null=True)

    def __str__(self) -> str:
        return f'{self.name} - {self.created_at.year}'



#from core.models import DateTime, Course, Levels

# Create your models here.
class CollegeLevels(models.TextChoices):
    BASICO_COMPLETO = 'Básico Completo', 'Básico Completo'
    BASICO_INCOMPLETO = 'Básico Incompleto', 'Básico Incompleto'
    MEDIO_COMPLETO = 'Medio Completo', 'Medio Completo'
    MEDIO_INCOMPLETO = 'Medio Incompleto', 'Medio Incompleto'
    SUPERIOR = 'Superior', 'Superior'

class Apoderado(DateTime):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    rut = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    ocupation = models.CharField(max_length=20)
    collage_level = models.CharField(max_length=20, choices=CollegeLevels.choices, default=CollegeLevels.BASICO_COMPLETO)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'
    
class Estudiante(DateTime):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    rut = models.CharField(max_length=10, unique=True)
    birth_date = models.DateField()
    bapDiag = models.CharField(max_length=40)
    address = models.CharField(max_length=40)
    commune = models.CharField(max_length=40)
    etnia = models.CharField(max_length=40, null=True, blank=True)

    parents = models.ManyToManyField(Apoderado, related_name='students', blank=True)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='students', null=True, blank=True)
    nivel = models.CharField(max_length=10, choices=Nivel.choices, default=Nivel.BASIC)

    def __str__(self) -> str:
        return f'{self.first_name} {self.last_name}'
    
    def rut_regex(self):
        rut_reg = re.compile(r'^d\{1,2}.?d\{3}.?d\{3}-[\dkK]$')
        return rut_reg
    
    def get_age(self):
        from datetime import date
        today = date.today()
        age = today.year - self.birth_date.year
        month = today.month - self.birth_date.month
        if month < 0:
            age -= 1
            month += 12
        elif month == 0 and today.day < self.birth_date.day:
            age -= 1
            month = 11
        return f'{age} años y {month} meses'
    
    @property
    def edad(self):
        return self.get_age()