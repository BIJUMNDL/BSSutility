from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transmedia", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Spare",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("terminal_equipment", models.CharField(blank=True, max_length=10, null=True)),
                ("date_of_decommissioning", models.DateField(blank=True, null=True)),
                ("terminalequipment_id", models.CharField(blank=True, max_length=30, null=True)),
                ("date_of_commissioning", models.DateField(blank=True, null=True)),
                ("stored", models.CharField(blank=True, choices=[("BSS_STORE", "BSS Store"), ("IN_SITE", "In site")], max_length=20, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("record", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, to="transmedia.mediainventory")),
            ],
        ),
    ]
