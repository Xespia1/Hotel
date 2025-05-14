from django import forms
from .models import Pasajero, Habitacion
from django.core.exceptions import ValidationError

class PasajeroForm(forms.ModelForm):
    class Meta:
        model = Pasajero
        fields = ['nombre', 'apellido', 'rut', 'telefono', 'email', 'fecha_ingreso', 'fecha_salida']
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
            'fecha_salida': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        fecha_ingreso = cleaned_data.get('fecha_ingreso')
        fecha_salida = cleaned_data.get('fecha_salida')

        if fecha_ingreso and fecha_salida and fecha_salida <= fecha_ingreso:
            raise ValidationError('La fecha de salida debe ser posterior a la fecha de ingreso.')

class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'capacidad', 'orientacion']