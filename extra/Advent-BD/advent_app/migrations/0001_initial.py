import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("bd_models", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdventDayConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day", models.IntegerField()),
                ("enabled", models.BooleanField(default=True)),
                (
                    "reward_type",
                    models.IntegerField(
                        choices=[
                            (1, "Random Special"),
                            (2, "Selected Ball"),
                            (3, "Selected Ball + Special"),
                        ]
                    ),
                ),
                (
                    "ball",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="advent_reward_ball",
                        to="bd_models.Ball",
                    ),
                ),
                (
                    "special",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="advent_reward_special",
                        to="bd_models.Special",
                    ),
                ),
                ("label", models.CharField(blank=True, max_length=100, null=True)),
            ],
            options={
                "db_table": "adventdayconfig",
            },
        ),
        migrations.CreateModel(
            name="AdventClaim",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day", models.IntegerField()),
                ("claimed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="advent_claims",
                        to="bd_models.Player",
                    ),
                ),
            ],
            options={
                "db_table": "adventclaim",
                "unique_together": {("player", "day")},
            },
        ),
    ]
