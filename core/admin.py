from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

admin.site.register(Habitacion)
admin.site.register(Pasajero)
admin.site.register(Reserva)
admin.site.register(Usuario, UserAdmin)
