from django.contrib import admin
from .models import Pasajero, Habitacion, Reserva

admin.site.register(Habitacion)
admin.site.register(Pasajero)
admin.site.register(Reserva)
