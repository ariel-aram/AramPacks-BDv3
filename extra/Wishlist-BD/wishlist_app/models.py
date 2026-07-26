from typing import override

from django.db import models


class WishlistItem(models.Model):
    user_id = models.BigIntegerField()
    ball_country = models.CharField(max_length=48)

    class Meta:
        db_table = "wishlistitem"
        unique_together = [("user_id", "ball_country")]

    @override
    def __str__(self):
        return f"WishlistItem(user={self.user_id}, ball={self.ball_country})"
