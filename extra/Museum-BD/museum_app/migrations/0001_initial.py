from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="MuseumCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.BigIntegerField()),
                ("card_id", models.CharField(max_length=64)),
                ("position", models.IntegerField()),
            ],
            options={
                "db_table": "museumcard",
                "ordering": ["user_id", "position"],
                "unique_together": {("user_id", "position")},
            },
        ),
    ]
