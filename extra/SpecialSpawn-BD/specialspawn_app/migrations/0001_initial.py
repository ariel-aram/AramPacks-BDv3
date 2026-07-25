from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SpecialSpawnConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("guild_id", models.BigIntegerField(unique=True)),
                ("special_channel", models.BigIntegerField(null=True)),
            ],
            options={
                "db_table": "specialspawnconfig",
            },
        ),
    ]
