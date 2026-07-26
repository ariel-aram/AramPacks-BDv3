from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="WishlistItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.BigIntegerField()),
                ("ball_country", models.CharField(max_length=48)),
            ],
            options={
                "db_table": "wishlistitem",
                "unique_together": {("user_id", "ball_country")},
            },
        ),
    ]
