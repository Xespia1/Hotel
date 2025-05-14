from django.shortcuts import render, redirect, get_object_or_404
from .models import Pasajero, Habitacion
from .forms import PasajeroForm, HabitacionForm
from django.http import HttpResponse
from django.contrib import messages
import openpyxl

def home(request):
    return HttpResponse("Bienvenido al Sistema de Gestión de Pasajeros del Hotel")
  
# Listar pasajeros
def lista_pasajeros(request):
    pasajeros = Pasajero.objects.all()
    return render(request, 'pasajeros/lista.html', {'pasajeros': pasajeros})

# Crear pasajero
def crear_pasajero(request):
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pasajero registrado correctamente.')
            return redirect('lista_pasajeros')
    else:
        form = PasajeroForm()
    return render(request, 'pasajeros/crear.html', {'form': form})

# Editar pasajero
def editar_pasajero(request, pasajero_id):
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)

    if request.method == 'POST':
        form = PasajeroForm(request.POST, instance=pasajero)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pasajero modificado correctamente.')
            return redirect('lista_pasajeros')
    else:
        form = PasajeroForm(instance=pasajero)

    return render(request, 'pasajeros/editar.html', {'form': form, 'pasajero': pasajero})
  
# Eliminar pasajero
def eliminar_pasajero(request, pasajero_id):
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)

    if request.method == 'POST':
        pasajero.delete()
        messages.success(request, 'Pasajero eliminado correctamente.')
        return redirect('lista_pasajeros')

def exportar_pasajeros_excel(request):
    # Crea el libro y hoja de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pasajeros'

    # Cabeceras
    headers = ['Nombre', 'Apellido', 'Email', 'Teléfono', 'RUT', 'Fecha Ingreso', 'Fecha Salida']
    ws.append(headers)

    # Datos
    for p in Pasajero.objects.all():
        ws.append([
            p.nombre,
            p.apellido,
            p.email,
            p.telefono,
            p.rut,
            p.fecha_ingreso.strftime('%d-%m-%Y') if p.fecha_ingreso else '',
            p.fecha_salida.strftime('%d-%m-%Y') if p.fecha_salida else ''
        ])

    # Configura la respuesta
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=pasajeros.xlsx'
    wb.save(response)
    return response

def crear_habitacion(request):
    if request.method == 'POST':
        form = HabitacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habitación registrada correctamente.')
            return redirect('lista_habitaciones')
    else:
        form = HabitacionForm()
    return render(request, 'habitaciones/crear.html', {'form': form})

def lista_habitaciones(request):
    habitaciones = Habitacion.objects.all()
    return render(request, 'habitaciones/lista.html', {'habitaciones': habitaciones})