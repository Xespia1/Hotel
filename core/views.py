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
from django.db import transaction
from django.forms import formset_factory
from datetime import date

def es_administrador(user):
    return user.is_authenticated and user.rol == 'administrador'

@user_passes_test(es_administrador)
def crear_encargado(request):
    pass

def home(request):
    return HttpResponse("Bienvenido al Sistema de Gestión de Pasajeros del Hotel")

@login_required
# Listar pasajeros
def lista_pasajeros(request):
    consulta = request.GET.get('buscar', '').strip()
    pasajeros = Pasajero.objects.all()
    hoy = timezone.now().date()
    
    if consulta:
        pasajeros = pasajeros.filter(
            Q(nombre__iexact=consulta) |
            Q(apellido__iexact=consulta) |
            Q(rut__iexact=consulta) |
            Q(email__iexact=consulta) |
            Q(telefono__iexact=consulta)
        )

    huespedes = []
    for pasajero in pasajeros:
        reservas_pasajero = Reserva.objects.filter(pasajero=pasajero).order_by(
            '-fecha_entrada'
        )

        total_pagado = sum(r.total for r in reservas_pasajero)
        
        reserva_actual = reservas_pasajero.filter(
            fecha_entrada__lte=hoy,
            fecha_salida__gte=hoy
        ).first()
        reserva = reserva_actual or reservas_pasajero.first()
        asignador = reserva.usuario if reserva and hasattr(reserva, 'usuario') and reserva.usuario else None
        
        huespedes.append({
        'pasajero': pasajero,
        'reserva': reserva,
        'asignador': asignador,
        'total_pagado': total_pagado,
        })
    return render(request, 'pasajeros/lista.html', {'huespedes': huespedes, 'buscar': consulta})

def reporte_ocupacion(request):
    habitaciones = Habitacion.objects.filter(esta_activa=True)
    hoy = date.today()

    total_habitaciones = habitaciones.count()
    ocupadas = 0

    for habitacion in habitaciones:
        habitaciones = Habitacion.objects.filter(esta_activa=True)
    reservas = Reserva.objects.all()
    fecha = request.GET.get('fecha', timezone.now().date())

    # Habitaciones ocupadas en esa fecha (solo contar cada habitación una vez)
    ocupadas_ids = Reserva.objects.filter(
        fecha_entrada__lte=fecha,
        fecha_salida__gte=fecha
    ).values_list('habitacion_id', flat=True).distinct()
    ocupadas = len(set(ocupadas_ids))

    vacantes = habitaciones.count() - ocupadas

    context = {
        'total': habitaciones.count(),
        'ocupadas': ocupadas,
        'vacantes': vacantes,
    }
    return render(request, 'reporte_ocupacion.html', context)

@login_required
def crear_pasajero(request):
    if request.method == 'POST':
        form = PasajeroForm(request.POST)
        if form.is_valid():
            habitacion = form.cleaned_data['habitacion']
            fecha_ingreso = form.cleaned_data['fecha_ingreso']
            fecha_salida = form.cleaned_data['fecha_salida']

            # 1. Contar reservas solapadas en esa habitación
            reservas_solapadas = Reserva.objects.filter(
                habitacion=habitacion,
                fecha_entrada__lte=fecha_salida,
                fecha_salida__gte=fecha_ingreso
            ).count()

            if reservas_solapadas >= habitacion.capacidad:
                messages.error(request, f'La habitación {habitacion.numero} ya alcanzó su capacidad máxima para esas fechas.')
            else:
                pasajero = form.save()
                Reserva.objects.create(
                    pasajero=pasajero,
                    habitacion=habitacion,
                    fecha_entrada=fecha_ingreso,
                    fecha_salida=fecha_salida,
                    total=20000
                )
                messages.success(request, 'Pasajero y reserva registrados correctamente.')
                return redirect('lista_pasajeros')
        else:
            messages.error(request, 'Error al registrar pasajero.')
    else:
        form = PasajeroForm()
    return render(request, 'pasajeros/crear.html', {'form': form})

@login_required
def editar_pasajero(request, pasajero_id):
    pasajero = get_object_or_404(Pasajero, id=pasajero_id)
    reserva = Reserva.objects.filter(pasajero=pasajero).first()

    if request.method == 'POST':
        form = PasajeroForm(request.POST, instance=pasajero)
        if form.is_valid():
            pasajero = form.save()

            habitacion = form.cleaned_data.get('habitacion')
            fecha_ingreso = form.cleaned_data.get('fecha_ingreso')
            fecha_salida = form.cleaned_data.get('fecha_salida')

            if habitacion and fecha_ingreso and fecha_salida:
                reservas_solapadas = Reserva.objects.filter(
                    habitacion=habitacion,
                    fecha_entrada__lte=fecha_salida,
                    fecha_salida__gte=fecha_ingreso
                )
                if reserva:
                    reservas_solapadas = reservas_solapadas.exclude(id=reserva.id)
                if reservas_solapadas.exists():
                    messages.error(request, 'Esa habitación ya tiene un pasajero asignado en ese periodo.')
                else:
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
                messages.error(request, 'Debes completar los campos de habitación, fecha de ingreso y fecha de salida.')
        else:
            messages.error(request, 'Error al editar pasajero. Revisa los campos ingresados.')
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
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Pasajeros'

    headers = [
        'RUT', 'Nombre', 'Apellido', 'Email', 'Teléfono',
        'Fecha Ingreso', 'Fecha Salida',
        'N° Habitación', 'Total a Pagar', 'Asignador'
    ]
    ws.append(headers)

    for p in Pasajero.objects.all():
        reserva = p.reserva_set.order_by('-fecha_entrada').first()
        if reserva:
            ws.append([
                p.rut,
                p.nombre,
                p.apellido,
                p.email,
                p.telefono,
                reserva.fecha_entrada.strftime('%d-%m-%Y') if reserva.fecha_entrada else '',
                reserva.fecha_salida.strftime('%d-%m-%Y') if reserva.fecha_salida else '',
                reserva.habitacion.numero if reserva.habitacion else '',
                f"${reserva.total:,}" if reserva.total else '',
                reserva.usuario.get_full_name() if reserva.usuario else ''
            ])
        else:
            ws.append([
                p.rut, p.nombre, p.apellido, p.email, p.telefono, '', '', '', '', ''
            ])

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
    hoy = timezone.now().date()

    habitaciones_estado = []
    for habitacion in habitaciones:
        # Reservas actuales: hoy está entre fecha_entrada y fecha_salida
        reservas_actuales = Reserva.objects.filter(
            habitacion=habitacion,
            fecha_entrada__lte=hoy,
            fecha_salida__gte=hoy
        )
        # Reservas futuras: empiezan después de hoy
        reservas_futuras = Reserva.objects.filter(
            habitacion=habitacion,
            fecha_entrada__gt=hoy
        )

        # Ocupada sólo si tiene al menos una reserva ACTUAL
        ocupada = reservas_actuales.exists()

        # Ocupantes actuales y futuros (listas de nombres)
        ocupantes_actuales = [
            f"{r.pasajero.nombre} {r.pasajero.apellido}" for r in reservas_actuales
        ]
        ocupantes_futuros = [
            f"{r.pasajero.nombre} {r.pasajero.apellido}" for r in reservas_futuras
        ]

        habitaciones_estado.append({
            'habitacion': habitacion,
            'ocupada': ocupada,
            'ocupantes_actuales': ocupantes_actuales,
            'ocupantes_futuros': ocupantes_futuros,
        })

    # Filtrado
    if filtro == 'vacantes':
        habitaciones_estado = [h for h in habitaciones_estado if not h['ocupada'] and h['habitacion'].esta_activa]
    elif filtro == 'ocupadas':
        habitaciones_estado = [h for h in habitaciones_estado if h['ocupada'] and h['habitacion'].esta_activa]
    elif filtro == 'deshabilitadas':
        habitaciones_estado = [h for h in habitaciones_estado if not h['habitacion'].esta_activa]
    # Si es "todas", no filtra

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
            messages.success(request, 'Reserva creada correctamente. Total a pagar: ${reserva.total:,}')
            return redirect('lista_habitaciones')
        else:
            messages.error(request, 'Error al crear reserva. Revisa los campos.')
    else:
        form = ReservaForm()
    return render(request, 'reservas.html', {'form': form})

@login_required
def crear_grupo_reserva(request):
    pasajeros = Pasajero.objects.all()
    habitaciones = Habitacion.objects.filter(esta_activa=True)

    if request.method == 'POST':
        form = GrupoReservaForm(request.POST)
        ids_seleccionados = request.POST.getlist('pasajero_ids')
        pasajeros_seleccionados = Pasajero.objects.filter(id__in=ids_seleccionados)

        # Valida que al menos un pasajero esté seleccionado
        if not pasajeros_seleccionados:
            messages.error(request, "Debes seleccionar al menos un pasajero.")
            return render(request, 'grupo_reserva.html', {
                'form': form,
                'pasajeros': pasajeros,
                'habitaciones': habitaciones,
            })

        if form.is_valid():
            responsable = form.cleaned_data['responsable']
            observaciones = form.cleaned_data['observaciones']
            fecha_entrada = form.cleaned_data['fecha_entrada']
            fecha_salida = form.cleaned_data['fecha_salida']

            # 1. Recolectar asignaciones pasajero-habitación
            asignaciones = []
            errores = []
            conteo = {}

            for pasajero in pasajeros_seleccionados:
                habitacion_id = request.POST.get(f"habitacion_id_{pasajero.id}")
                if habitacion_id:
                    try:
                        habitacion = habitaciones.get(id=habitacion_id)
                        asignaciones.append((pasajero, habitacion))
                        conteo[habitacion.id] = conteo.get(habitacion.id, 0) + 1
                    except Habitacion.DoesNotExist:
                        errores.append(f"Habitación inválida para pasajero {pasajero}")
                else:
                    errores.append(f"Debes asignar una habitación para {pasajero}")

            # Validar habitaciones seleccionadas y capacidades
            for habitacion in habitaciones:
                if conteo.get(habitacion.id, 0) > habitacion.capacidad:
                    errores.append(f"La habitación {habitacion.numero} está sobrepasando su capacidad.")

            if errores:
                messages.error(request, "Corrige los siguientes errores: " + ", ".join(errores))
                return render(request, 'grupo_reserva.html', {
                    'form': form,
                    'pasajeros': pasajeros,
                    'habitaciones': habitaciones,
                })

            # 2. Crear el grupo y reservas
            with transaction.atomic():
                grupo = GrupoReserva.objects.create(
                    responsable=responsable,
                    observaciones=observaciones
                )
                dias = (fecha_salida - fecha_entrada).days or 1
                total_por_pasajero = 20000 * dias

                for pasajero, habitacion in asignaciones:
                    Reserva.objects.create(
                        grupo=grupo,
                        pasajero=pasajero,
                        habitacion=habitacion,
                        fecha_entrada=fecha_entrada,
                        fecha_salida=fecha_salida,
                        total=total_por_pasajero,
                        usuario=request.user
                    )

            messages.success(request, f'Grupo de reserva registrado correctamente. Total a pagar: ${len(asignaciones) * total_por_pasajero:,}')
            return redirect('listar_grupo_reservas')

        else:
            messages.error(request, 'Revisa los campos del formulario.')

    else:
        form = GrupoReservaForm()

    return render(request, 'grupo_reserva.html', {
        'form': form,
        'pasajeros': pasajeros,
        'habitaciones': habitaciones,
    })

# Listar grupos
@login_required
def listar_grupo_reservas(request):
    grupos = GrupoReserva.objects.all()
    return render(request, 'grupo_reserva_listar.html', {'grupos': grupos})

# Editar grupo
@login_required
def editar_grupo_reserva(request, grupo_id):
    grupo = get_object_or_404(GrupoReserva, pk=grupo_id)
    reservas = Reserva.objects.filter(grupo=grupo)
    pasajeros = list(Pasajero.objects.all())
    habitaciones = list(Habitacion.objects.filter(esta_activa=True))
    
    # Diccionario: pasajero_id -> habitacion_id ya asignada
    pasajero_habitacion_ids = {r.pasajero.id: r.habitacion.id for r in reservas}
    pasajeros_seleccionados = list(pasajero_habitacion_ids.keys())

    if request.method == 'POST':
        form = GrupoReservaForm(request.POST)
        if form.is_valid():
            grupo.responsable = form.cleaned_data['responsable']
            grupo.observaciones = form.cleaned_data['observaciones']
            grupo.save()
            fecha_entrada = form.cleaned_data['fecha_entrada']
            fecha_salida = form.cleaned_data['fecha_salida']
            
            # Lee los pasajeros seleccionados y sus habitaciones
            pasajero_ids = request.POST.getlist('pasajero_ids')
            # Elimina reservas antiguas
            Reserva.objects.filter(grupo=grupo).delete()
            
            errores = []
            conteo = {}
            # Construye habitaciones_asignadas desde POST para recarga si hay error
            habitaciones_asignadas = {
                int(pid): int(request.POST.get(f"habitacion_id_{pid}", 0))
                for pid in pasajero_ids if request.POST.get(f"habitacion_id_{pid}")
            }

            # Crea nuevas reservas de acuerdo a lo asignado en el form
            for pasajero_id in pasajero_ids:
                habitacion_id = request.POST.get(f'habitacion_id_{pasajero_id}')
                if not habitacion_id:
                    errores.append(f"Selecciona una habitación para el pasajero con ID {pasajero_id}")
                    continue
                pasajero = Pasajero.objects.get(pk=pasajero_id)
                habitacion = Habitacion.objects.get(pk=habitacion_id)
                conteo[habitacion.id] = conteo.get(habitacion.id, 0) + 1
                Reserva.objects.create(
                    grupo=grupo,
                    pasajero=pasajero,
                    habitacion=habitacion,
                    fecha_entrada=fecha_entrada,
                    fecha_salida=fecha_salida,
                    total=20000,
                    usuario=request.user
                )
            # Validación de capacidad
            for habitacion in habitaciones:
                if conteo.get(habitacion.id, 0) > habitacion.capacidad:
                    messages.error(request, f"La habitación {habitacion.numero} está sobrepasando su capacidad.")
                    return render(request, 'grupo_reserva_editar.html', {
                        'form': form,
                        'grupo': grupo,
                        'pasajeros': pasajeros,
                        'habitaciones': habitaciones,
                        'pasajeros_seleccionados': [int(i) for i in pasajero_ids],
                        'habitaciones_asignadas': {'pasajero_habitacion_ids': habitaciones_asignadas},
                    })
            if errores:
                for error in errores:
                    messages.error(request, error)
                return render(request, 'grupo_reserva_editar.html', {
                    'form': form,
                    'grupo': grupo,
                    'pasajeros': pasajeros,
                    'habitaciones': habitaciones,
                    'pasajeros_seleccionados': [int(i) for i in pasajero_ids],
                    'habitaciones_asignadas': {'pasajero_habitacion_ids': habitaciones_asignadas},
                })

            messages.success(request, "Grupo de reserva actualizado correctamente.")
            return redirect('listar_grupo_reservas')
        else:
            # Si hay error en form, reconstruir habitaciones_asignadas desde POST
            pasajero_ids = request.POST.getlist('pasajero_ids')
            habitaciones_asignadas = {
                int(pid): int(request.POST.get(f"habitacion_id_{pid}", 0))
                for pid in pasajero_ids if request.POST.get(f"habitacion_id_{pid}")
            }
            return render(request, 'grupo_reserva_editar.html', {
                'form': form,
                'grupo': grupo,
                'pasajeros': pasajeros,
                'habitaciones': habitaciones,
                'pasajeros_seleccionados': [int(i) for i in pasajero_ids],
                'habitaciones_asignadas': {'pasajero_habitacion_ids': habitaciones_asignadas},
            })
    else:
        # GET: Prepara datos de habitaciones asignadas actuales
        habitaciones_asignadas = pasajero_habitacion_ids  # Diccionario pasajero_id: habitacion_id
        initial = {
            'responsable': grupo.responsable,
            'observaciones': grupo.observaciones,
            'fecha_entrada': reservas.first().fecha_entrada if reservas.exists() else None,
            'fecha_salida': reservas.first().fecha_salida if reservas.exists() else None,
        }
        form = GrupoReservaForm(initial=initial)

    return render(request, 'grupo_reserva_editar.html', {
        'form': form,
        'grupo': grupo,
        'pasajeros': pasajeros,
        'habitaciones': habitaciones,
        'pasajeros_seleccionados': pasajeros_seleccionados,
        'habitaciones_asignadas': {'pasajero_habitacion_ids': habitaciones_asignadas},
    })


# Eliminar grupo
@login_required
def eliminar_grupo_reserva(request, grupo_id):
    grupo = get_object_or_404(GrupoReserva, pk=grupo_id)
    if request.method == 'POST':
        grupo.delete()
        messages.success(request, "Grupo eliminado correctamente.")
        return redirect('listar_grupo_reservas')
    return render(request, 'grupo_reserva_eliminar.html', {'grupo': grupo})

