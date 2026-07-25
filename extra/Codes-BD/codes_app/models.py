from __future__ import annotations

import random
from typing import TYPE_CHECKING

from bd_models.models import Ball, BallInstance, Player, Special
from django.db import models
from django.utils import timezone
from settings.models import settings

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class PromoCode(models.Model):
    class RewardType(models.TextChoices):
        BALL = "ball", "Countryball"
        BALL_SPECIAL = "ball_special", "Countryball + Special"
        MONEY = "money", "Money"

    code = models.CharField(max_length=32, unique=True, help_text="Case-insensitive promo code.")
    reward_type = models.CharField(max_length=16, choices=RewardType.choices, default=RewardType.BALL)
    amount = models.PositiveBigIntegerField(null=True, blank=True, help_text="Money amount (only for money reward).")
    ball = models.ForeignKey(
        Ball,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Specific ball to give. If blank, a random enabled ball is used.",
    )
    special = models.ForeignKey(
        Special,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Special event applied to the ball (only for ball + special reward).",
    )
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum redemptions. Blank = unlimited.")
    uses = models.PositiveIntegerField(default=0, editable=False)
    single_use_per_user = models.BooleanField(
        default=True, help_text="Restrict each player to one redemption of this code."
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = "promocode"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_exhausted(self) -> bool:
        if self.max_uses is None:
            return False
        return self.uses >= self.max_uses

    async def redeem(
        self,
        player: Player,
        *,
        bot: "BallsDexBot",
    ) -> tuple[bool, str]:
        if not self.enabled or self.is_expired:
            return False, "This promo code is no longer valid."
        if self.is_exhausted:
            return False, "This promo code has reached its maximum uses."
        if (
            self.single_use_per_user
            and await PromoCodeRedemption.objects.filter(player=player, promo_code=self).aexists()
        ):
            return False, "You have already redeemed this code."

        if self.reward_type == PromoCode.RewardType.MONEY:
            if not settings.currency_enabled:
                return False, "Currency is not enabled on this bot."
            if not self.amount:
                return False, "This code is misconfigured (missing amount)."
            await player.add_money(self.amount)
            reward_text = f"**{self.amount} {settings.currency_display_name(bot)}**"

        else:
            if self.reward_type == PromoCode.RewardType.BALL_SPECIAL and self.special is None:
                return False, "This code is misconfigured (missing special event)."

            if self.ball is not None:
                chosen_ball = self.ball
            else:
                enabled_balls = [b async for b in Ball.enabled_objects.all()]
                if not enabled_balls:
                    return False, "No balls are available for redemption right now."
                chosen_ball = random.choice(enabled_balls)

            special = self.special if self.reward_type == PromoCode.RewardType.BALL_SPECIAL else None
            atk_bonus = random.randint(-settings.max_attack_bonus, settings.max_attack_bonus)
            hp_bonus = random.randint(-settings.max_health_bonus, settings.max_health_bonus)

            await BallInstance.objects.acreate(
                player=player,
                ball=chosen_ball,
                special=special,
                attack_bonus=atk_bonus,
                health_bonus=hp_bonus,
                server_id=0,
            )

            reward_text = f"**{chosen_ball.country}**"
            if special is not None:
                reward_text = f"{special.emoji or ''} {special.name} {reward_text}"

        self.uses += 1
        await self.asave(update_fields=["uses"])
        await PromoCodeRedemption.objects.acreate(player=player, promo_code=self)
        return True, f"Promo code redeemed! You received {reward_text}."


class PromoCodeRedemption(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="promocode_redemptions")
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="redemptions")
    redeemed_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        db_table = "promocoderedemption"
        unique_together = [["player", "promo_code"]]
        ordering = ["-redeemed_at"]

    def __str__(self) -> str:
        return f"{self.player.discord_id} redeemed {self.promo_code.code}"
