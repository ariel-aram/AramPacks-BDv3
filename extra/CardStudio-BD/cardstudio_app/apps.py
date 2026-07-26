from django.apps import AppConfig


class CardStudioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cardstudio_app"
    dpy_package = "cardstudio_app.cardstudio_ext"

    def ready(self):
        from cardstudio_app.image_gen import apply_patches

        apply_patches()
