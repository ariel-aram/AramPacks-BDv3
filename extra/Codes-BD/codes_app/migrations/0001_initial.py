import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("bd_models", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PromoCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(help_text="Case-insensitive promo code.", max_length=32, unique=True)),
                (
                    "reward_type",
                    models.CharField(
                        choices=[
                            ("ball", "Countryball"),
                            ("ball_special", "Countryball + Special"),
                            ("money", "Money"),
                        ],
                        default="ball",
                        max_length=16,
                    ),
                ),
                (
                    "amount",
                    models.PositiveBigIntegerField(
                        blank=True, help_text="Money amount (only for money reward).", null=True
                    ),
                ),
                (
                    "ball",
                    models.ForeignKey(
                        blank=True,
                        help_text="Specific ball to give. If blank, a random enabled ball is used.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bd_models.Ball",
                    ),
                ),
                (
                    "special",
                    models.ForeignKey(
                        blank=True,
                        help_text="Special event applied to the ball (only for ball + special reward).",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bd_models.Special",
                    ),
                ),
                (
                    "max_uses",
                    models.PositiveIntegerField(
                        blank=True, help_text="Maximum redemptions. Blank = unlimited.", null=True
                    ),
                ),
                ("uses", models.PositiveIntegerField(default=0)),
                ("single_use_per_user", models.BooleanField(default=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True)),
                ("enabled", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "promocode",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PromoCodeRedemption",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("redeemed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="promocode_redemptions",
                        to="bd_models.Player",
                    ),
                ),
                (
                    "promo_code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="redemptions",
                        to="codes_app.PromoCode",
                    ),
                ),
            ],
            options={
                "db_table": "promocoderedemption",
                "ordering": ["-redeemed_at"],
                "unique_together": {("player", "promo_code")},
            },
        ),
    ]
