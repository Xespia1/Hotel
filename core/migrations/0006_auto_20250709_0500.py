# Generated by Django 3.0.14 on 2025-07-09 09:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20250709_0154'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reserva',
            name='grupo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reservas', to='core.GrupoReserva'),
        ),
    ]
