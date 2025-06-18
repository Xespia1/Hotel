from django.shortcuts import render, redirect, get_object_or_404
from .models import Pasajero, Habitacion
from .forms import *
from django.http import HttpResponse
from django.contrib import messages
import openpyxl
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.utils import timezone
from django.db.models import Q

def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'

@user_passes_test(es_administrador)
def crear_encargado(request):
    # Lógica para crear encargado
    pass

def home(request):
    return HttpResponse("Bienvenido al Sistema de Gestión de Pasajeros del Hotel")

@login_required
# Listar pasajeros
def lista_pasajeros(request):
    consulta = request.GET.get('buscar', '').strip()
    pasajeros = Pasajero.objects.all()
    
    if consulta:
        pasajeros = pasajeros.filter(
            Q(nombre__icontains=consulta) |
            Q(apellido__icontains=consulta) |
            Q(rut__icontains=consulta) |
            Q(email__icontains=consulta) |
            Q(telefono__icontains=consulta)
        )

    huespedes = []
    for pasajero in pasajeros:
        reserva = Reserva.objects.filter(pasajero=pasajero).first()
        asignador = reserva.usuario if reserva and hasattr(reserva, 'usuario') and reserva.usuario else None
        huespedes.append({
            'pasajero': pasajero,
            'reserva': reserva,
            'asignador': asignador,
        })
    return render(request, 'pasajeros/lista.html', {'huespedes': huespedes, 'buscar': consulta})

@login_required
# Crear pasajero
def crear_pasajero(request):
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            pasajero = form.save()
            habitacion = form.cleaned_data['habitacion']
            # Crear la reserva automáticamente
            Reserva.objects.create(
                pasajero=pasajero,
                habitacion=habitacion,
                fecha_entrada=pasajero.fecha_ingreso,
                fecha_salida=pasajero.fecha_salida,
                total=20000  # Puedes ajustar el cálculo del total
            )
            messages.success(request, 'Pasajero y reserva registrados correctamente.')
            return redirect('lista_pasajeros')
        else:
            messages.error(request, 'Error al registrar pasajero.')
    else:
        form = PasajeroForm()
    return render(request, 'pasajeros/crear.html', {'form': form})

@login_required
# Editar pasajero
def editar_pasajero(request, pasajero_id):
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)
    reserva = Reserva.objects.filter(pasajero=pasajero).first()

    if request.method == 'POST':
        form = PasajeroForm(request.POST, instance=pasajero)
        if form.is_valid():
            habitacion = form.cleaned_data['habitacion']
            fecha_ingreso = form.cleaned_data['fecha_ingreso']
            fecha_salida = form.cleaned_data['fecha_salida']

            # Excluye la reserva actual del pasajero al buscar conflictos
            conflicto = Reserva.objects.filter(
                habitacion=habitacion,
                fecha_entrada__lte=fecha_salida,
                fecha_salida__gte=fecha_ingreso
            )
            if reserva:
                conflicto = conflicto.exclude(id=reserva.id)
            
            if conflicto.exists():
                messages.error(request, 'Esa habitación ya tiene un pasajero asignado en ese periodo.')
            else:
                pasajero = form.save()
                if reserva:
                    reserva.habitacion = habitacion
                    reserva.fecha_entrada = fecha_ingreso
                    reserva.fecha_salida = fecha_salida
                    reserva.save()
                else:
                    Reserva.objects.create(
                        pasajero=pasajero,
                        habitacion=habitacion,
                        fecha_entrada=fecha_ingreso,
                        fecha_salida=fecha_salida,
                        total=20000
                    )
                messages.success(request, 'Pasajero y reserva modificados correctamente.')
                return redirect('lista_pasajeros')
        else:
            messages.error(request, 'Error al editar pasajero.')
    else:
        initial = {'habitacion': reserva.habitacion if reserva else None}
        form = PasajeroForm(instance=pasajero, initial=initial)
    return render(request, 'pasajeros/editar.html', {'form': form, 'pasajero': pasajero})

@login_required
# Eliminar pasajero
def eliminar_pasajero(request, pasajero_id):
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)

    if request.method == 'POST':
        pasajero.delete()
        messages.success(request, 'Pasajero eliminado correctamente.')
        return redirect('lista_pasajeros')

@login_required
def exportar_pasajeros_excel(request):
    # Crea el libro y hoja de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pasajeros'

    # Cabeceras
    headers = ['RUT','Nombre', 'Apellido', 'Email', 'Teléfono',  'Fecha Ingreso', 'Fecha Salida']
    ws.append(headers)

    # Datos
    for p in Pasajero.objects.all():
        ws.append([
            p.rut,
            p.nombre,
            p.apellido,
            p.email,
            p.telefono,
            p.fecha_ingreso.strftime('%d-%m-%Y') if p.fecha_ingreso else '',
            p.fecha_salida.strftime('%d-%m-%Y') if p.fecha_salida else ''
        ])

    # Configura la respuesta
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=pasajeros.xlsx'
    wb.save(response)
    return response

@login_required
def crear_pasajero(request):
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            pasajero = form.save(commit=False)
            habitacion = form.cleaned_data['habitacion']
            fecha_ingreso = form.cleaned_data['fecha_ingreso']
            fecha_salida = form.cleaned_data['fecha_salida']

            # Validar que la habitación esté disponible en ese periodo
            existe_reserva = Reserva.objects.filter(
                habitacion=habitacion,
                fecha_entrada__lte=fecha_salida,
                fecha_salida__gte=fecha_ingreso
            ).exists()
            if existe_reserva:
                messages.error(request, 'Esa habitación ya tiene un pasajero asignado en ese periodo.')
            else:
                pasajero.save()
                Reserva.objects.create(
                    pasajero=pasajero,
                    habitacion=habitacion,
                    fecha_entrada=fecha_ingreso,
                    fecha_salida=fecha_salida,
                    total=20000  # o tu lógica de costo
                )
                messages.success(request, 'Pasajero y reserva registrados correctamente.')
                return redirect('lista_pasajeros')
        else:
            messages.error(request, 'Error al registrar pasajero.')
    else:
        form = PasajeroForm()
    return render(request, 'pasajeros/crear.html', {'form': form})

@login_required
def crear_habitacion(request):
    if request.method == 'POST':
        form = HabitacionForm(request.POST)
        if form.is_valid():
            numero = form.cleaned_data['numero']
            # Validar que no exista una habitación activa con ese número
            if Habitacion.objects.filter(numero=numero, esta_activa=True).exists():
                messages.error(request, 'Ya existe una habitación activa con ese número.')
            else:
                form.save()
                messages.success(request, 'Habitación registrada correctamente.')
                return redirect('lista_habitaciones')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = HabitacionForm()
    return render(request, 'habitaciones/crear.html', {'form': form})

@login_required
def eliminar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)

    # Valida si hay reservas activas (sin fecha de salida)
    reservas_activas = Reserva.objects.filter(habitacion=habitacion, fecha_salida__isnull=True)
    if reservas_activas.exists():
        messages.error(request, 'No se puede eliminar una habitación con pasajeros activos.')
        return redirect('lista_habitaciones')

    # Si no hay reservas activas, hacemos borrado lógico
    habitacion.esta_activa = False
    habitacion.save()
    messages.success(request, 'Habitación desactivada correctamente (historial preservado).')
    return redirect('lista_habitaciones')

@login_required
def editar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)

    if request.method == 'POST':
        form = HabitacionForm(request.POST, instance=habitacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Habitación editada correctamente.')
            return redirect('lista_habitaciones')
        else:
            messages.error(request, 'Error al editar la habitación. Verifica los datos ingresados.')
    else:
        form = HabitacionForm(instance=habitacion)

    return render(request, 'habitaciones/editar.html', {
        'form': form,
        'habitacion': habitacion
    })

@login_required
def lista_habitaciones(request):
    filtro = request.GET.get('filtro', 'todas')
    habitaciones = Habitacion.objects.all()

    habitaciones_estado = []
    for habitacion in habitaciones:
        ocupada = Reserva.objects.filter(
            habitacion=habitacion,
            fecha_entrada__lte=timezone.now().date(),
            fecha_salida__gte=timezone.now().date(),
        ).exists()
        habitaciones_estado.append({
            'habitacion': habitacion,
            'ocupada': ocupada,
        })

    # Filtro:
    if filtro == 'vacantes':
        habitaciones_estado = [h for h in habitaciones_estado if not h['ocupada'] and h['habitacion'].esta_activa]
    elif filtro == 'ocupadas':
        habitaciones_estado = [h for h in habitaciones_estado if h['ocupada'] and h['habitacion'].esta_activa]
    elif filtro == 'deshabilitadas':
        habitaciones_estado = [h for h in habitaciones_estado if not h['habitacion'].esta_activa]
    # Filtro == 'todas', no filtra

    return render(request, 'habitaciones/lista.html', {
        'habitaciones_estado': habitaciones_estado,
        'filtro': filtro,
    })
    
@login_required
def habilitar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    habitacion.esta_activa = True
    habitacion.save()
    messages.success(request, 'Habitación reactivada correctamente.')
    return redirect('lista_habitaciones')

@login_required
def deshabilitar_habitacion(request, habitacion_id):
    habitacion = get_object_or_404(Habitacion, id=habitacion_id)
    habitacion.esta_activa = False
    habitacion.save()
    messages.success(request, 'Habitación deshabilitada correctamente.')
    return redirect('lista_habitaciones')



@login_required
def home_view(request):
    return render(request, 'home.html')

class CustomLoginView(LoginView):
    template_name = 'login.html'

class CustomLogoutView(LogoutView):
    next_page = 'login'
    
def es_administrador(user):
    return user.is_authenticated and (user.rol == 'administrador' or user.is_superuser)

@user_passes_test(es_administrador)
def crear_encargado(request):
    if request.method == "POST":
        form = EncargadoCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Encargado creado correctamente.")
            return redirect('home')
    else:
        form = EncargadoCreationForm()
    return render(request, "crear_encargado.html", {"form": form})

@login_required
def crear_reserva(request):
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            # Calcula días de estadía
            dias = (reserva.fecha_salida - reserva.fecha_entrada).days if reserva.fecha_salida and reserva.fecha_entrada else 1
            # Asume 1 pasajero por reserva, ajusta si quieres sumar varios pasajeros
            reserva.total = 20000 * dias
            reserva.save()
            messages.success(request, 'Reserva creada correctamente.')
            return redirect('lista_habitaciones')
        else:
            messages.error(request, 'Error al crear reserva. Revisa los campos.')
    else:
        form = ReservaForm()
    return render(request, 'reservas/crear.html', {'form': form})