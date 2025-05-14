from django.urls import path, include
from . import views

urlpatterns = [
    path('pasajeros/', views.lista_pasajeros, name='lista_pasajeros'),
    path('pasajeros/crear/', views.crear_pasajero, name='crear_pasajero'),
    path('pasajeros/editar/<int:pasajero_id>/', views.editar_pasajero, name='editar_pasajero'),
    path('pasajeros/eliminar/<int:pasajero_id>/', views.eliminar_pasajero, name='eliminar_pasajero'),
    path('reporte-excel/', views.exportar_pasajeros_excel, name='reporte_excel'),
    path('habitaciones/', views.lista_habitaciones, name='lista_habitaciones'),
    path('habitaciones/nueva/', views.crear_habitacion, name='crear_habitacion')
]
