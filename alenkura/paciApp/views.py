from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.models import Estudiante, Asignatura, Eje, Objetivos, Estrategias
from accounts.models import User
from .models import PaciAppModel, Indicador
import json

@login_required
def index(request, id):
    estudiante = get_object_or_404(Estudiante, pk=id)
    
    asignaturas = Asignatura.objects.prefetch_related('ejes').all()

    asignaturas_data = []
    for asignatura in asignaturas:
        
        ejes_list = list(asignatura.ejes.all().values('id', 'nombre'))
        asignaturas_data.append({
            'id': asignatura.id,
            'nombre': asignatura.nombre,
            'ejes': ejes_list
        })
    
    context = {
        'estudiante': estudiante,
        'asignaturas_json': json.dumps(asignaturas_data),
        'asignaturas': asignaturas,
        'objetivos': Objetivos.objects.all(),
        'estrategias': Estrategias.objects.all()
    }
    return render(request, 'paci.html', context)

@login_required
def create_paci(request, id):
    if request.method == 'POST':
        estudiante = get_object_or_404(Estudiante, pk=id)
        asignaturas = Asignatura.objects.all()
        
        try:
            with transaction.atomic():
                for asig in asignaturas:
                    # IMPORTANTE: Esto busca el input con el name modificado en el HTML
                    # name="ejes_seleccionados_{{asignatura.id}}"
                    ejes_ids = request.POST.getlist(f'ejes_seleccionados_{asig.id}')
                    
                    if not ejes_ids:
                        continue # Si no eligió ejes para esta asignatura, pasamos a la siguiente

                    # Iteramos por cada ID de Eje seleccionado
                    for eje_id in ejes_ids:
                        
                        # Definimos las claves para buscar en el POST según el formato de tu JS
                        # Formato: nombre_campo + "_" + ID_Asignatura + "_" + ID_Eje
                        key_adecuacion = f'adecuacion_{asig.id}_{eje_id}'
                        key_objetivo = f'objetivos_{asig.id}_{eje_id}'
                        key_estrategias = f'estrategias_{asig.id}_{eje_id}'
                        key_indicadores_json = f'indicadores_json_{asig.id}_{eje_id}'

                        # Obtenemos valores
                        adecuacion = request.POST.get(key_adecuacion)
                        objetivo = request.POST.get(key_objetivo)
                        
                        # Validamos que al menos haya algo que guardar
                        if not adecuacion and not objetivo:
                            continue

                        # Procesar estrategias (lista a string)
                        estrategias_lista = request.POST.getlist(key_estrategias)
                        estrategias_str = ", ".join(estrategias_lista)

                        # Buscamos la instancia del Eje para la Foreign Key
                        eje_instancia = get_object_or_404(Eje, pk=eje_id)

                        # Creamos el PACI usando tu modelo PaciAppModel
                        paci = PaciAppModel.objects.create(
                            profesor=request.user,
                            student=estudiante,
                            subject=asig,
                            axis=eje_instancia,  # Aquí asignamos el eje
                            objetivo_general=objetivo,
                            adecuacion_curricular=adecuacion,
                            estrategias=estrategias_str
                        )

                        # Procesar Indicadores (vienen como JSON string desde el JS)
                        indicadores_json_str = request.POST.get(key_indicadores_json)
                        
                        if indicadores_json_str:
                            try:
                                # Convertimos string JSON a lista Python
                                indicadores_lista = json.loads(indicadores_json_str)
                                
                                for texto_indicador in indicadores_lista:
                                    if texto_indicador.strip():
                                        # Usamos el modelo Indicador (singular)
                                        Indicador.objects.create(
                                            indicador=texto_indicador,
                                            paci=paci
                                        )
                            except json.JSONDecodeError:
                                print(f"Error decodificando JSON para Asig {asig.id} Eje {eje_id}")

                return redirect('coreApp:estudiantes')

        except Exception as e:
            print(f"Error CRÍTICO al guardar PACI: {e}")
            return HttpResponse(f"Error al guardar: {e}", status=500)

    return redirect('coreApp:estudiantes')