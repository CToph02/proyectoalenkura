from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import Sala

class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrador'
        DIRECTOR = 'DIRECTOR', 'Director'
        COORDINATOR = 'COORDINADOR', 'Coordinador'
        TEACHER = 'TEACHER', 'Docente'
        PROFESSIONAL = 'PROFESSIONAL', 'Profesional'

    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.TEACHER)
    profesion = models.CharField(max_length=150, blank=True)
    phone = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    nro_registro = models.CharField(max_length=20, null=True)
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self) -> str:
        full_name = self.get_full_name().strip()
        return full_name if full_name else self.username

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Roles.ADMIN
        super().save(*args, **kwargs)