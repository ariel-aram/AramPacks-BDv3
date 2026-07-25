from django.contrib import admin

from codes_app.models import PromoCode, PromoCodeRedemption


class PromoCodeRedemptionInline(admin.TabularInline):
    model = PromoCodeRedemption
    extra = 0
    readonly_fields = ("player", "redeemed_at")
    autocomplete_fields = ("player",)
    can_delete = False


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "reward_type",
        "amount",
        "ball",
        "special",
        "uses",
        "max_uses",
        "enabled",
        "expires_at",
    )
    list_filter = ("reward_type", "enabled", "expires_at", "single_use_per_user")
    search_fields = ("code",)
    autocomplete_fields = ("ball", "special")
    readonly_fields = ("uses", "created_at")
    inlines = (PromoCodeRedemptionInline,)
    fieldsets = (
        (None, {"fields": ("code", "reward_type", "enabled", "expires_at")}),
        (
            "Reward configuration",
            {"fields": ("amount", "ball", "special")},
        ),
        (
            "Usage limits",
            {"fields": ("max_uses", "single_use_per_user", "uses")},
        ),
        ("Metadata", {"fields": ("created_at",)}),
    )
    actions = ("activate", "deactivate")

    @admin.action(description="Activate selected promo codes")
    def activate(self, request, queryset):
        queryset.update(enabled=True)

    @admin.action(description="Deactivate selected promo codes")
    def deactivate(self, request, queryset):
        queryset.update(enabled=False)


@admin.register(PromoCodeRedemption)
class PromoCodeRedemptionAdmin(admin.ModelAdmin):
    list_display = ("player", "promo_code", "redeemed_at")
    list_filter = ("redeemed_at",)
    search_fields = ("player__discord_id", "promo_code__code")
    autocomplete_fields = ("player", "promo_code")
    readonly_fields = ("player", "promo_code", "redeemed_at")
