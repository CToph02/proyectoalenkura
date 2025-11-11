from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ped', '0002_plan_models_and_objetivo_updates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='planevaluacion',
            name='objetivo_general',
            field=models.TextField(blank=True),
        ),
    ]
