from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from core.models import Estudiante, Asignatura, Eje, Contenido
from indicadoresApp.models import Indicadores
from accounts.models import User
from .models import PaciAppModel

# Create your views here.
def index(request, id):
    if request.method == 'POST':
        asignatura_id = request.POST.get('asignatura')
        indicadores_lista = request.POST.getlist('indicadores_lista')

        with transaction.atomic():
            paci = PaciAppModel.objects.create(
                profesor = request.user,
                student=Estudiante.objects.get(pk=id),
                subject=Asignatura.objects.get(pk=asignatura_id),
                axis=request.POST.getlist('eje'),
                objetivo_general=request.POST.get('objetivo'),
                adecuacion_curricular=request.POST.get('adecuacion'),
                estrategias=request.POST.get('estrategias')
            )
            for indicador in indicadores_lista:
                Indicadores.objects.create(
                    indicador=indicador,
                    paci=paci
                )
    context = {
        'estudiante': Estudiante.objects.get(id=id),
        'asignaturas': Asignatura.objects.all(),
        'ejes': Eje.objects.all(),
        'contenidos': Contenido.objects.all(),
    }
    return render(request, 'paci.html', context)

class paci_list(LoginRequiredMixin, ListView):
    pass

class paci_create(LoginRequiredMixin, CreateView):

    fields = [
    'nombre', 
    'descripcion', 
    'fecha_inicio', 
    'fecha_fin', 
    'estado']

    success_url = reverse_lazy("paci:list")
class paci_edit(LoginRequiredMixin, UpdateView):
    success_url = reverse_lazy("paci:list")

class paci_delete(LoginRequiredMixin, DeleteView):
    success_url = reverse_lazy("paci:list")
