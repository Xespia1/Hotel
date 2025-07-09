from django import forms
from .models import *
from django.core.exceptions import ValidationError
import re

class PasajeroForm(forms.ModelForm):
    habitacion = forms.ModelChoiceField(
        queryset=Habitacion.objects.filter(esta_activa=True),
        label='Habitación',
        required=True
    )
    class Meta:
        model = Pasajero
        fields = ['rut','nombre', 'apellido','email',  'telefono',  'fecha_ingreso', 'fecha_salida']
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
            'fecha_salida': forms.DateInput(attrs={'type': 'date'}),
        }
        
        def clean_rut(self):
            rut = self.cleaned_data['rut'].replace(' ', '').upper()
            if not re.match(r'^\d{7,8}-[0-9K]$', rut):
                raise forms.ValidationError('El formato del RUT debe ser 12345678-9 o 12345678-K, sin puntos ni espacios.')
            return rut
    
        def clean(self):
            cleaned_data = super().clean()
            fecha_ingreso = cleaned_data.get('fecha_ingreso')
            fecha_salida = cleaned_data.get('fecha_salida')

            if fecha_ingreso and fecha_salida and fecha_salida <= fecha_ingreso:
             raise ValidationError('La fecha de salida debe ser posterior a la fecha de ingreso.')

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['pasajero', 'habitacion', 'fecha_entrada', 'fecha_salida']

    # Opcional: solo mostrar habitaciones activas
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['habitacion'].queryset = Habitacion.objects.filter(esta_activa=True)
        self.fields['fecha_entrada'].initial = timezone.now().date()

class GrupoReservaForm(forms.ModelForm):
    pasajeros = forms.ModelMultipleChoiceField(
        queryset=Pasajero.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Pasajeros del grupo"
    )
    habitaciones = forms.ModelMultipleChoiceField(
        queryset=Habitacion.objects.filter(esta_activa=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Habitaciones a asignar"
    )
    fecha_entrada = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_salida = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = GrupoReserva
        fields = ['responsable', 'observaciones']

class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = ['numero', 'capacidad', 'detalles']
        
class AsignacionPasajeroHabitacionForm(forms.Form):
    pasajero = forms.ModelChoiceField(queryset=Pasajero.objects.none(), widget=forms.HiddenInput)
    habitacion = forms.ModelChoiceField(queryset=Habitacion.objects.none(), label="Habitación asignada")

class EncargadoCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar Contraseña', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name']

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.rol = 'encargado'
        if commit:
            user.save()
        return user