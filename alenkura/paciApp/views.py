from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from core.models import Estudiante, Asignatura, Eje, Contenido

# Create your views here.
def index(request):
    context = {
        'estudiantes': Estudiante.objects.all(),
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
