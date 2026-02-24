from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transmedia", "0002_spare"),
    ]

    operations = [
        migrations.CreateModel(
            name="Diversion",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("site_name", models.CharField(max_length=150)),
                ("diversion_letter_no", models.CharField(max_length=80)),
                ("remarks", models.CharField(blank=True, max_length=250, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("record", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to="transmedia.mediainventory")),
            ],
        ),
    ]
