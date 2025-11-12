from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Indicadores

# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the indicadoresApp index.")

class indicadores_list(LoginRequiredMixin, ListView):
    pass
    #model = Indicadores
    #context_object_name = 'indicadores_list'

class indicadores_create(LoginRequiredMixin, CreateView):
    pass
    # model = Indicadores
    # fields = [
    # 'profesor', 
    # 'estudiante', 
    # 'asignatura', 
    # 'indicador', 
    # 'puntaje', 
    # 'puntaje_obtenido', 
    # 'paci'
    # ]
    # success_url = reverse_lazy("indicadores:list")

class indicadores_edit(LoginRequiredMixin, UpdateView):
    pass
    #model = Indicadores
    # success_url = reverse_lazy("indicadores:list")

class indicadores_delete(LoginRequiredMixin, DeleteView):
    pass
    #model = Indicadores
    # success_url = reverse_lazy("indicadores:list")