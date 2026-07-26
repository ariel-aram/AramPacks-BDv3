from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FlexData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.BigIntegerField(unique=True)),
                ("last_flex", models.BigIntegerField(default=0)),
            ],
            options={
                "db_table": "flexdata",
            },
        ),
    ]
