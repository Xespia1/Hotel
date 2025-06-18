from django.urls import path, include
from . import views
from .views import CustomLoginView, CustomLogoutView
from .models import Habitacion
from .forms import HabitacionForm

urlpatterns = [
    path('', views.home_view, name='home'),
    path('pasajeros/', views.lista_pasajeros, name='lista_pasajeros'),
    path('pasajeros/crear/', views.crear_pasajero, name='crear_pasajero'),
    path('pasajeros/editar/<int:pasajero_id>/', views.editar_pasajero, name='editar_pasajero'),
    path('pasajeros/eliminar/<int:pasajero_id>/', views.eliminar_pasajero, name='eliminar_pasajero'),
    path('reporte-excel/', views.exportar_pasajeros_excel, name='reporte_excel'),
    path('habitaciones/', views.lista_habitaciones, name='lista_habitaciones'),
    path('habitaciones/crear/', views.crear_habitacion, name='crear_habitacion'),
    path('habitaciones/editar/<int:habitacion_id>/', views.editar_habitacion, name='editar_habitacion'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('encargados/crear/', views.crear_encargado, name='crear_encargado'),
    path('habitaciones/eliminar/<int:habitacion_id>/', views.eliminar_habitacion, name='eliminar_habitacion'),
    path('habitaciones/habilitar/<int:habitacion_id>/', views.habilitar_habitacion, name='habilitar_habitacion'),
    path('habitaciones/deshabilitar/<int:habitacion_id>/', views.deshabilitar_habitacion, name='deshabilitar_habitacion'),

]
