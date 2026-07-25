from django.apps import AppConfig


class CodesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "codes_app"
    dpy_package = "codes_app.codes_ext"
