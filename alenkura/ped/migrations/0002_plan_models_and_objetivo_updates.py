from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_asignatura_objetivo_evaluacion'),
        ('ped', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlanEvaluacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('objetivo_general', models.TextField()),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('actualizado_en', models.DateTimeField(auto_now=True)),
                ('decreto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='planes', to='ped.decreto')),
            ],
        ),
        migrations.CreateModel(
            name='PlanAsignatura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('procedimiento', models.TextField(blank=True)),
                ('instrumento', models.TextField(blank=True)),
                ('asignatura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planes_evaluacion', to='core.asignatura')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_asignaturas', to='ped.planevaluacion')),
            ],
            options={
                'unique_together': {('plan', 'asignatura')},
            },
        ),
        migrations.CreateModel(
            name='PlanEje',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido', models.TextField()),
                ('eje', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='planificaciones', to='core.eje')),
                ('plan_asignatura', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='plan_ejes', to='ped.planasignatura')),
            ],
            options={
                'unique_together': {('plan_asignatura', 'eje')},
            },
        ),
        migrations.AddField(
            model_name='objetivogeneral',
            name='plan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='objetivos_generales', to='ped.planevaluacion'),
        ),
        migrations.AlterField(
            model_name='objetivogeneral',
            name='objAsignatura',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='objetivos_generales', to='core.asignatura'),
        ),
    ]
