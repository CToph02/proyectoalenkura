from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("aula", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="proyectoaula",
            name="gantt_data",
            field=models.TextField(blank=True),
        ),
    ]

