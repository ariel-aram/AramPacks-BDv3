from django.apps import AppConfig


class SpecialSpawnConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "specialspawn"
    dpy_package = "specialspawn.ext"
