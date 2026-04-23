from django.contrib import admin
from .models import Campaign, CampaignUpdate


class CampaignUpdateInline(admin.TabularInline):
    model = CampaignUpdate
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "creator", "status", "goal", "raised", "progress_percent", "created_at")
    list_filter = ("status", "created_via_whatsapp")
    search_fields = ("title", "creator__username", "creator__email")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("raised", "created_at", "updated_at")
    inlines = [CampaignUpdateInline]

    def progress_percent(self, obj):
        return f"{obj.progress_percent:.1f}%"
    progress_percent.short_description = "Progresso"


@admin.register(CampaignUpdate)
class CampaignUpdateAdmin(admin.ModelAdmin):
    list_display = ("campaign", "author", "created_at")
    list_filter = ("created_at",)
