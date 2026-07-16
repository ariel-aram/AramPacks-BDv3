from enum import IntEnum

from django.db import models


class RewardType(IntEnum):
    RANDOM_SPECIAL = 1
    SELECTED_BALL = 2
    SELECTED_BALL_WITH_SPECIAL = 3


class AdventDayConfig(models.Model):
    day = models.IntegerField()
    enabled = models.BooleanField(default=True)
    reward_type = models.IntegerField(
        choices=[
            (RewardType.RANDOM_SPECIAL.value, "Random Special"),
            (RewardType.SELECTED_BALL.value, "Selected Ball"),
            (RewardType.SELECTED_BALL_WITH_SPECIAL.value, "Selected Ball + Special"),
        ]
    )
    ball = models.ForeignKey(
        "bd_models.Ball",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="advent_reward_ball",
    )
    special = models.ForeignKey(
        "bd_models.Special",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="advent_reward_special",
    )
    label = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "adventdayconfig"

    def __str__(self):
        return f"Day {self.day} ({self.label or 'No label'})"


class AdventClaim(models.Model):
    player = models.ForeignKey("bd_models.Player", on_delete=models.CASCADE, related_name="advent_claims")
    day = models.IntegerField()
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "adventclaim"
        unique_together = ("player", "day")

    def __str__(self):
        return f"{self.player.id} claimed day {self.day}"
