from django.contrib import admin

from .models import (
    Adecuacion_curricular,
    Indicadores_instrumento,
    Instrumento_evaluacion,
    Nota,
)

# Register your models here.

admin.site.register(Indicadores_instrumento)
admin.site.register(Adecuacion_curricular)
admin.site.register(Instrumento_evaluacion)
admin.site.register(Nota)
