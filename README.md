# Moderation-BD

A moderation extra package for [Ballsdex v3](https://github.com/Ballsdex-Team/BallsDex-DiscordBot).

Provides slash commands for common moderation actions: kick, ban, unban, mute, unmute, warn, purge, slowmode, lock/unlock channels, and nickname management. Warnings are persisted in the database and visible in the admin panel. And blah blah blah.

The base for this extra package comes from [molteencreates/BallsDex-DiscordBot-Moderation-Package](https://github.com/molteencreates/BallsDex-DiscordBot-Moderation-Package), with some modifications to fit the Ballsdex v3 ecosystem. Therefore, the proper credits goes to [**molteencreates**](https://github.com/molteencreates) for the original package.

## Disclaimer

For this extra package to work, you must enable the following permissions for the bot:

- `Kick Members`
- `Ban Members`
- `Manage Roles`
- `Manage Channels`
- `Change Nickname`

If you leave these permissions disabled, then bye bye, get out of this repository. `>:(`

## Commands

| Command | Description |
|---------|-------------|
| `/kick` | Kick a user from the server |
| `/ban` | Ban a user from the server |
| `/unban` | Unban a user by tag (Explosives#6969) |
| `/mute` | Mute a user with a "Muted" role |
| `/unmute` | Unmute a user |
| `/setmutedrole` | Set the role used for muting members |
| `/warn` | Warn a user (persisted in database) |
| `/warnings` | List warnings for a user |
| `/clearwarnings` | Clear all warnings for a user |
| `/purge` | Purge messages in the channel |
| `/slowmode` | Set slowmode in the channel |
| `/lock` | Lock the channel |
| `/unlock` | Unlock the channel |
| `/nickname` | Change a user's nickname |

## Installation

### Docker

Add the following to your `config/extra.toml`:

```toml
[[ballsdex.packages]]
location = "git+https://github.com/aramhosting/Moderation-BD.git@1.1.0"
path = "moderation_app"
enabled = true
```

Then rebuild and restart:

```bash
docker compose up --build
```

### Without Docker

1. Clone or download this repository into your `extra/` folder
2. Add the following to your `config/extra.toml`:

```toml
[[ballsdex.packages]]
location = ""
path = "moderation_app"
enabled = true
editable = true
```

3. Install the package: `uv pip install -e extra/Moderation-BD`
4. Run migrations: `python3 -m django makemigrations moderation_app && python3 -m django migrate`
5. Start the bot

## Requirements

- Ballsdex >= 3.0.0
- Python >= 3.14

## License

MIT
