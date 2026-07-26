"""Smoke test: ensure each cog's app command classes can be defined.

discord.py's `@app_commands.command()` decorator runs at class-body time and
calls `_extract_parameters_from_callback` on the decorated function. If a
parameter annotation references a name not in module globals, this raises
NameError during import.

This script configures minimal Django settings, imports each extension module,
and confirms that the cog classes can be defined without raising. If a cog
references a TYPE_CHECKING-only type in a non-interaction parameter
annotation, this test catches it before deployment.

Usage (in any environment where the extras are installed via `uv pip install -e`):
    DJANGO_SETTINGS_MODULE=scripts.test_settings python scripts/verify_app_commands.py
"""

from __future__ import annotations

import importlib
import os
import sys
import traceback

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scripts.test_settings")

import django

django.setup()

PACKAGES: list[str] = [
    "advent_app.advent_ext",
    "cfcommands_app.cfcommands_ext",
    "exchange_app.exchange_ext",
    "flex_app.flex_ext",
    "funhouse_app.funhouse_ext",
    "museum_app.museum_ext",
    "preview_app.preview_ext",
    "reindeerrush_app.reindeerrush_ext",
    "santa_app.santa_ext",
    "specialspawn_app.specialspawn_ext",
    "wishlist_app.wishlist_ext",
    "cardstudio_app.cardstudio_ext",
    "moderation_app.moderation_ext",
    "events_app.events_ext",
]


def main() -> int:
    sys.path.insert(0, r"C:\Portable\AramPacks-BDv3\extra")
    sys.path.insert(0, r"C:\Portable\AramPacks-BDv3")

    failures: list[str] = []
    for pkg in PACKAGES:
        try:
            importlib.import_module(pkg)
        except Exception as e:
            failures.append(f"[import] {pkg}: {type(e).__name__}: {e}")
            traceback.print_exc()
            continue
        sys.stdout.write(f"[ok] {pkg}\n")

    if failures:
        sys.stdout.write("\nFAILURES:\n")
        for line in failures:
            sys.stdout.write(f"  - {line}\n")
        return 1
    sys.stdout.write("\nAll cogs imported without annotation errors.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
