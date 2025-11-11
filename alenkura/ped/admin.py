from django.contrib import admin

from .models import (
    Decreto,
    ObjetivoGeneral,
    PlanAsignatura,
    PlanEje,
    PlanEvaluacion,
)


@admin.register(Decreto)
class DecretoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


class PlanAsignaturaInline(admin.TabularInline):
    model = PlanAsignatura
    extra = 0


@admin.register(PlanEvaluacion)
class PlanEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'decreto', 'creado_en', 'actualizado_en')
    list_filter = ('decreto', 'creado_en')
    inlines = (PlanAsignaturaInline,)


@admin.register(PlanAsignatura)
class PlanAsignaturaAdmin(admin.ModelAdmin):
    list_display = ('plan', 'asignatura')
    list_filter = ('asignatura',)
    search_fields = ('plan__decreto__nombre', 'asignatura__nombre')


@admin.register(PlanEje)
class PlanEjeAdmin(admin.ModelAdmin):
    list_display = ('plan_asignatura', 'eje')
    list_filter = ('eje__asignatura',)


@admin.register(ObjetivoGeneral)
class ObjetivoGeneralAdmin(admin.ModelAdmin):
    list_display = ('descripcion_resumida', 'plan', 'objAsignatura')
    search_fields = ('descripcion',)

    def descripcion_resumida(self, obj):
        return obj.descripcion[:50] + ('...' if len(obj.descripcion) > 50 else '')
    descripcion_resumida.short_description = 'Descripción'
