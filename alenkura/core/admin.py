from django.contrib import admin
from .models import Asignatura, Eje, Contenido, Curso, Apoderado, Estudiante

admin.site.register(Asignatura)
admin.site.register(Eje)
admin.site.register(Contenido)
admin.site.register(Curso)
admin.site.register(Apoderado)
admin.site.register(Estudiante)