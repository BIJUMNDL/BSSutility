from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transmedia", "0003_diversion"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Spare",
            new_name="SpareDMW",
        ),
        migrations.RenameModel(
            old_name="Diversion",
            new_name="DiversionDMW",
        ),
    ]
