# Generated migration for FlexGuildConfig

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("flex_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FlexGuildConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("guild_id", models.BigIntegerField(unique=True)),
                ("mod_approval_channel_id", models.BigIntegerField(blank=True, null=True)),
                ("public_flex_channel_id", models.BigIntegerField(blank=True, null=True)),
                ("enabled", models.BooleanField(default=False)),
            ],
            options={
                "db_table": "flex_guild_config",
            },
        ),
    ]
