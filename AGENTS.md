# AGENTS.md

## Commands

```bash
uv tool run pyright          # typecheck (NOT `uv run pyright` — that fails)
uv run ruff check .          # lint
uv run ruff format .         # format
uv run toml-sort pyproject.toml  # sort TOML
uv run mdformat README.md    # format markdown
uv run pymarkdown scan README.md  # lint markdown
uv lock                      # regenerate lockfile after dep changes
```

No test runner — these are Ballsdex plugins, tested via the host bot.

## Architecture

This repo is a **collection of Ballsdex v3 extra packages** (not a standalone app). Each package in `extra/` is a Django app containing a discord.py cog.

Package structure (e.g. `extra/Flex-BD/`):

```text
Flex-BD/
  pyproject.toml              # hatchling build, name = "flex-bd"
  flex_app/
    __init__.py               # empty
    apps.py                   # AppConfig with dpy_package = "flex_app.flex_ext"
    migrations/
    flex_ext/
      __init__.py             # async def setup(bot): await bot.add_cog(Flex(bot))
      cog.py                  # the actual cog class
```

`config/extra.toml` registers packages for the Ballsdex host bot.

## Key Conventions

- **Python 3.14**, line-length 120, 4-space indent
- **Django ORM**: always use async methods (`.aget()`, `.acreate()`, `.afirst()`, `.acount()`, `.aexists()`, `.adelete()`, `.aget_or_create()`)
- **Models**: imported from `bd_models.models` (Ball, BallInstance, Player, Special, etc.)
- **Transformers**: use `app_commands.Transform[ResultType, TransformerClass]` annotation pattern, never bare `BallTransformer`
- **Components v2**: all interactive cogs use `discord.ui.View`, `discord.ui.Button`, `discord.ui.Select`, `discord.ui.Modal`
- **Type narrowing**: `interaction.guild` is `Guild | None`, `interaction.user` is `User | Member` — assert or check before use in guild-only commands
- **`# type: ignore[attr-defined]`**: needed for Django model `.id` field (auto-generated, invisible to pyright) and `child.disabled` on View children

## Dependency Overrides

Ballsdex pins `django==6.0.0` and `Pillow==12.0.0` exactly. `[tool.uv.override-dependencies]` forces patched versions (Django 6.0.7, Pillow 12.3.0). Do not remove this.

## Pyright Config

- `include = ["extra"]` — only checks the extra packages
- Excludes `**/migrations`
- `reportUnnecessaryTypeIgnoreComment = true` — don't add unnecessary ignores
- `reportIncompatibleMethodOverride = "warning"` — use `# type: ignore[override]` for intentional overrides (e.g. `cog_unload`)
