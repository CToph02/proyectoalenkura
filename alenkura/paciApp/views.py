from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

# Create your views here.
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
