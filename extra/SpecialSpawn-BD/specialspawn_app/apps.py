from django.apps import AppConfig


class SpecialSpawnConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "specialspawn_app"
    dpy_package = "specialspawn_app.specialspawn_ext"
