from typing import override

from django.apps import AppConfig


class CardStudioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cardstudio_app"
    dpy_package = "cardstudio_app.cardstudio_ext"

    @override
    def ready(self):
        from cardstudio_app.image_gen import apply_patches  # noqa: PLC0415

        apply_patches()
