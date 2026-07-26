from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CardConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=True, help_text="Use Card Studio for card generation.")),
                (
                    "title_font",
                    models.FileField(
                        blank=True,
                        help_text="Title font (.ttf/.otf).",
                        null=True,
                        upload_to="cardstudio/fonts/",
                    ),
                ),
                ("title_size", models.PositiveIntegerField(default=170)),
                (
                    "capacity_name_font",
                    models.FileField(
                        blank=True,
                        help_text="Ability name font (.ttf/.otf).",
                        null=True,
                        upload_to="cardstudio/fonts/",
                    ),
                ),
                ("capacity_name_size", models.PositiveIntegerField(default=110)),
                (
                    "capacity_description_font",
                    models.FileField(
                        blank=True,
                        help_text="Ability description font (.ttf/.otf).",
                        null=True,
                        upload_to="cardstudio/fonts/",
                    ),
                ),
                ("capacity_description_size", models.PositiveIntegerField(default=75)),
                (
                    "stats_font",
                    models.FileField(
                        blank=True, help_text="Health/attack font.", null=True, upload_to="cardstudio/fonts/"
                    ),
                ),
                ("stats_size", models.PositiveIntegerField(default=130)),
                (
                    "credits_font",
                    models.FileField(blank=True, help_text="Credits font.", null=True, upload_to="cardstudio/fonts/"),
                ),
                ("credits_size", models.PositiveIntegerField(default=40)),
                (
                    "rarity_font",
                    models.FileField(blank=True, help_text="Rarity font.", null=True, upload_to="cardstudio/fonts/"),
                ),
                ("rarity_size", models.PositiveIntegerField(default=130)),
                ("title_x", models.IntegerField(default=50)),
                ("title_y", models.IntegerField(default=20)),
                ("title_color", models.CharField(max_length=7, default="#000000")),
                ("title_stroke_width", models.PositiveIntegerField(default=2)),
                ("title_stroke_color", models.CharField(max_length=7, default="#000000")),
                ("title_anchor", models.CharField(blank=True, default="", max_length=3)),
                ("capacity_name_x", models.IntegerField(default=100)),
                ("capacity_name_y", models.IntegerField(default=1050)),
                ("capacity_name_color", models.CharField(max_length=7, default="#E6E6E6")),
                ("capacity_name_stroke_width", models.PositiveIntegerField(default=2)),
                ("capacity_name_stroke_color", models.CharField(max_length=7, default="#000000")),
                ("capacity_name_line_width", models.PositiveIntegerField(default=26)),
                ("capacity_name_line_spacing", models.IntegerField(default=100)),
                ("capacity_description_x", models.IntegerField(default=60)),
                ("capacity_description_y", models.IntegerField(default=1100)),
                ("capacity_description_color", models.CharField(max_length=7, default="#000000")),
                ("capacity_description_stroke_width", models.PositiveIntegerField(default=1)),
                ("capacity_description_stroke_color", models.CharField(max_length=7, default="#000000")),
                ("capacity_description_line_width", models.PositiveIntegerField(default=32)),
                ("capacity_description_line_spacing", models.IntegerField(default=80)),
                ("health_x", models.IntegerField(default=320)),
                ("health_y", models.IntegerField(default=1670)),
                ("health_color", models.CharField(max_length=7, default="#ED7365")),
                ("attack_x", models.IntegerField(default=1120)),
                ("attack_y", models.IntegerField(default=1670)),
                ("attack_color", models.CharField(max_length=7, default="#FCC24C")),
                ("attack_anchor", models.CharField(default="ra", max_length=3)),
                ("stats_stroke_width", models.PositiveIntegerField(default=1)),
                ("stats_stroke_color", models.CharField(max_length=7, default="#000000")),
                ("rarity_x", models.IntegerField(default=1200)),
                ("rarity_y", models.IntegerField(default=50)),
                ("rarity_color", models.CharField(max_length=7, default="#000000")),
                ("rarity_stroke_width", models.PositiveIntegerField(default=2)),
                ("rarity_stroke_color", models.CharField(max_length=7, default="#000000")),
                ("credits_x", models.IntegerField(default=30)),
                ("credits_y", models.IntegerField(default=1870)),
                (
                    "credits_color",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Blank uses the automatic contrast color.",
                        max_length=7,
                    ),
                ),
                ("credits_stroke_width", models.PositiveIntegerField(default=0)),
                ("credits_stroke_color", models.CharField(max_length=7, default="#FFFFFF")),
                ("artwork_x1", models.IntegerField(default=34)),
                ("artwork_y1", models.IntegerField(default=261)),
                ("artwork_x2", models.IntegerField(default=1393)),
                ("artwork_y2", models.IntegerField(default=992)),
                ("icon_size", models.PositiveIntegerField(default=192)),
                ("icon_x", models.IntegerField(default=1200)),
                ("icon_y", models.IntegerField(default=30)),
            ],
            options={
                "db_table": "cardstudio_config",
                "verbose_name": "Card Studio configuration",
                "verbose_name_plural": "Card Studio configuration",
            },
        ),
    ]
