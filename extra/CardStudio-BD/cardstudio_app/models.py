from __future__ import annotations

from typing import Any, override

from django.core.exceptions import ValidationError
from django.db import models


class CardConfig(models.Model):
    enabled = models.BooleanField(default=True, help_text="Use Card Studio for card generation.")

    title_font = models.FileField(
        upload_to="cardstudio/fonts/", null=True, blank=True, help_text="Title font (.ttf/.otf."
    )
    title_size = models.PositiveIntegerField(default=170)

    capacity_name_font = models.FileField(
        upload_to="cardstudio/fonts/", null=True, blank=True, help_text="Ability name font (.ttf/.otf)."
    )
    capacity_name_size = models.PositiveIntegerField(default=110)

    capacity_description_font = models.FileField(
        upload_to="cardstudio/fonts/", null=True, blank=True, help_text="Ability description font (.ttf/.otf)."
    )
    capacity_description_size = models.PositiveIntegerField(default=75)

    stats_font = models.FileField(upload_to="cardstudio/fonts/", null=True, blank=True, help_text="Health/attack font.")
    stats_size = models.PositiveIntegerField(default=130)

    credits_font = models.FileField(upload_to="cardstudio/fonts/", null=True, blank=True, help_text="Credits font.")
    credits_size = models.PositiveIntegerField(default=40)

    rarity_font = models.FileField(upload_to="cardstudio/fonts/", null=True, blank=True, help_text="Rarity font.")
    rarity_size = models.PositiveIntegerField(default=130)

    title_x = models.IntegerField(default=50)
    title_y = models.IntegerField(default=20)
    title_color = models.CharField(max_length=7, default="#000000")
    title_stroke_width = models.PositiveIntegerField(default=2)
    title_stroke_color = models.CharField(max_length=7, default="#000000")
    title_anchor = models.CharField(max_length=3, blank=True, default="")

    capacity_name_x = models.IntegerField(default=100)
    capacity_name_y = models.IntegerField(default=1050)
    capacity_name_color = models.CharField(max_length=7, default="#E6E6E6")
    capacity_name_stroke_width = models.PositiveIntegerField(default=2)
    capacity_name_stroke_color = models.CharField(max_length=7, default="#000000")
    capacity_name_line_width = models.PositiveIntegerField(default=26)
    capacity_name_line_spacing = models.IntegerField(default=100)

    capacity_description_x = models.IntegerField(default=60)
    capacity_description_y = models.IntegerField(default=1100)
    capacity_description_color = models.CharField(max_length=7, default="#000000")
    capacity_description_stroke_width = models.PositiveIntegerField(default=1)
    capacity_description_stroke_color = models.CharField(max_length=7, default="#000000")
    capacity_description_line_width = models.PositiveIntegerField(default=32)
    capacity_description_line_spacing = models.IntegerField(default=80)

    health_x = models.IntegerField(default=320)
    health_y = models.IntegerField(default=1670)
    health_color = models.CharField(max_length=7, default="#ED7365")

    attack_x = models.IntegerField(default=1120)
    attack_y = models.IntegerField(default=1670)
    attack_color = models.CharField(max_length=7, default="#FCC24C")
    attack_anchor = models.CharField(max_length=3, default="ra")

    stats_stroke_width = models.PositiveIntegerField(default=1)
    stats_stroke_color = models.CharField(max_length=7, default="#000000")

    rarity_x = models.IntegerField(default=1200)
    rarity_y = models.IntegerField(default=50)
    rarity_color = models.CharField(max_length=7, default="#000000")
    rarity_stroke_width = models.PositiveIntegerField(default=2)
    rarity_stroke_color = models.CharField(max_length=7, default="#000000")

    credits_x = models.IntegerField(default=30)
    credits_y = models.IntegerField(default=1870)
    credits_color = models.CharField(
        max_length=7, blank=True, default="", help_text="Blank uses the automatic contrast color."
    )
    credits_stroke_width = models.PositiveIntegerField(default=0)
    credits_stroke_color = models.CharField(max_length=7, default="#FFFFFF")

    artwork_x1 = models.IntegerField(default=34)
    artwork_y1 = models.IntegerField(default=261)
    artwork_x2 = models.IntegerField(default=1393)
    artwork_y2 = models.IntegerField(default=992)

    icon_size = models.PositiveIntegerField(default=192)
    icon_x = models.IntegerField(default=1200)
    icon_y = models.IntegerField(default=30)

    objects = models.Manager()

    class Meta:
        db_table = "cardstudio_config"
        verbose_name = "Card Studio configuration"
        verbose_name_plural = "Card Studio configuration"

    @override
    def __str__(self) -> str:
        return "Card Studio configuration"

    @override
    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self.pk and CardConfig.objects.exists():
            raise ValidationError("Only one Card Studio configuration can exist.")
        return super().save(*args, **kwargs)

    @classmethod
    def get_config(cls) -> CardConfig | None:
        try:
            config = cls.objects.first()
            if config is None:
                config = cls.objects.create()
            return config
        except Exception:
            return None
