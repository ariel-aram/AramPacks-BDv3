from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Warning",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("guild_id", models.BigIntegerField()),
                ("user_id", models.BigIntegerField()),
                ("moderator_id", models.BigIntegerField()),
                ("reason", models.TextField(default="No reason provided.")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["guild_id", "user_id"], name="moderation__guild_i_idx"),
                ],
            },
        ),
    ]
