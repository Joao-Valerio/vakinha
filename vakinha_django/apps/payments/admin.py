from django.contrib import admin
from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ("campaign", "donor_name", "amount", "status", "payment_method", "created_at")
    list_filter = ("status", "payment_method", "anonymous")
    search_fields = ("donor_name", "donor_email", "campaign__title", "mp_payment_id")
    readonly_fields = ("mp_preference_id", "mp_payment_id", "mp_external_reference", "created_at", "updated_at")
    date_hierarchy = "created_at"
