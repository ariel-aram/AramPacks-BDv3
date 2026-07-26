from django.contrib import admin

from cardstudio_app.models import CardConfig


@admin.register(CardConfig)
class CardConfigAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ("enabled",)
    fieldsets = (
        ("Configuration", {"fields": ("enabled",)}),
        (
            "Fonts",
            {
                "fields": (
                    "title_font",
                    "title_size",
                    "capacity_name_font",
                    "capacity_name_size",
                    "capacity_description_font",
                    "capacity_description_size",
                    "stats_font",
                    "stats_size",
                    "credits_font",
                    "credits_size",
                    "rarity_font",
                    "rarity_size",
                )
            },
        ),
        (
            "Title",
            {
                "fields": (
                    "title_x",
                    "title_y",
                    "title_color",
                    "title_stroke_width",
                    "title_stroke_color",
                    "title_anchor",
                )
            },
        ),
        (
            "Ability name",
            {
                "fields": (
                    "capacity_name_x",
                    "capacity_name_y",
                    "capacity_name_color",
                    "capacity_name_stroke_width",
                    "capacity_name_stroke_color",
                    "capacity_name_line_width",
                    "capacity_name_line_spacing",
                )
            },
        ),
        (
            "Ability description",
            {
                "fields": (
                    "capacity_description_x",
                    "capacity_description_y",
                    "capacity_description_color",
                    "capacity_description_stroke_width",
                    "capacity_description_stroke_color",
                    "capacity_description_line_width",
                    "capacity_description_line_spacing",
                )
            },
        ),
        (
            "Stats",
            {
                "fields": (
                    "health_x",
                    "health_y",
                    "health_color",
                    "attack_x",
                    "attack_y",
                    "attack_color",
                    "attack_anchor",
                    "stats_stroke_width",
                    "stats_stroke_color",
                )
            },
        ),
        (
            "Rarity",
            {
                "fields": (
                    "rarity_x",
                    "rarity_y",
                    "rarity_color",
                    "rarity_stroke_width",
                    "rarity_stroke_color",
                )
            },
        ),
        (
            "Credits",
            {
                "fields": (
                    "credits_x",
                    "credits_y",
                    "credits_color",
                    "credits_stroke_width",
                    "credits_stroke_color",
                )
            },
        ),
        (
            "Artwork",
            {"fields": ("artwork_x1", "artwork_y1", "artwork_x2", "artwork_y2")},
        ),
        (
            "Economy icon",
            {"fields": ("icon_size", "icon_x", "icon_y")},
        ),
    )
