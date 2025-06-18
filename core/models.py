from djongo import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class Pasajero(models.Model):
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=15)
    fecha_ingreso = models.DateField(default=timezone.now)
    fecha_salida = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Habitacion(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    capacidad = models.PositiveIntegerField(default=1)
    detalles = models.CharField(max_length=100)
    esta_activa = models.BooleanField(default=True)

    def __str__(self):
        return f'Habitación {self.numero} (Capacidad: {self.capacidad})'
      
class Reserva(models.Model):
    pasajero = models.ForeignKey(Pasajero, on_delete=models.CASCADE)
    habitacion = models.ForeignKey(Habitacion, on_delete=models.CASCADE)
    fecha_entrada = models.DateField()
    fecha_salida = models.DateField(null=True, blank=True)
    total = models.IntegerField()
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)  # <--- NUEVO

    def __str__(self):
        return f"Reserva de {self.pasajero} - Habitación {self.habitacion.numero}"
    
class Usuario(AbstractUser):
    ROL_CHOICES = (
        ('administrador', 'Administrador'),
        ('encargado', 'Encargado'),
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)