from typing import override

from django.db import models


class FlexData(models.Model):
    user_id = models.BigIntegerField(unique=True)
    last_flex = models.BigIntegerField(default=0)

    class Meta:
        db_table = "flexdata"

    @override
    def __str__(self):
        return f"FlexData(user={self.user_id})"
