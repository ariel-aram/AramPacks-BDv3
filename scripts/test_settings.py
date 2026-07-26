"""Minimal Django settings for smoke-testing cog imports."""

from __future__ import annotations

SECRET_KEY = "test"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "advent_app",
    "cardstudio_app",
    "cfcommands_app",
    "events_app",
    "exchange_app",
    "flex_app",
    "funhouse_app",
    "moderation_app",
    "museum_app",
    "preview_app",
    "reindeerrush_app",
    "santa_app",
    "specialspawn_app",
    "wishlist_app",
]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
