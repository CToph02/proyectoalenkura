from django.db import models


class Asignatura(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


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
