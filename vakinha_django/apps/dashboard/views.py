import json
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDay, TruncMonth
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from apps.campaigns.models import Campaign
from apps.payments.models import Donation


@login_required
def dashboard_index(request):
    user = request.user
    campaigns = Campaign.objects.filter(creator=user).order_by("-created_at")

    # Overall stats
    total_raised = (
        Donation.objects.filter(campaign__creator=user, status=Donation.STATUS_APPROVED)
        .aggregate(total=Sum("amount"))["total"]
        or 0
    )
    total_donations = Donation.objects.filter(
        campaign__creator=user, status=Donation.STATUS_APPROVED
    ).count()
    active_campaigns = campaigns.filter(status=Campaign.STATUS_ACTIVE).count()
    total_donors = (
        Donation.objects.filter(campaign__creator=user, status=Donation.STATUS_APPROVED)
        .values("donor_email")
        .distinct()
        .count()
    )

    # Last 30 days donations chart data
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_donations = (
        Donation.objects.filter(
            campaign__creator=user,
            status=Donation.STATUS_APPROVED,
            created_at__gte=thirty_days_ago,
        )
        .annotate(day=TruncDay("created_at"))
        .values("day")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("day")
    )

    chart_labels = []
    chart_amounts = []
    for entry in daily_donations:
        chart_labels.append(entry["day"].strftime("%d/%m"))
        chart_amounts.append(float(entry["total"]))

    # Per-campaign stats
    campaign_stats = []
    for campaign in campaigns[:10]:
        approved_donations = campaign.donations.filter(status=Donation.STATUS_APPROVED)
        campaign_stats.append({
            "campaign": campaign,
            "total_raised": approved_donations.aggregate(t=Sum("amount"))["t"] or 0,
            "donations_count": approved_donations.count(),
        })

    # Recent donations across all campaigns
    recent_donations = (
        Donation.objects.filter(campaign__creator=user, status=Donation.STATUS_APPROVED)
        .select_related("campaign")
        .order_by("-created_at")[:10]
    )

    context = {
        "total_raised": total_raised,
        "total_donations": total_donations,
        "active_campaigns": active_campaigns,
        "total_donors": total_donors,
        "campaigns": campaigns,
        "campaign_stats": campaign_stats,
        "recent_donations": recent_donations,
        "chart_labels": json.dumps(chart_labels),
        "chart_amounts": json.dumps(chart_amounts),
    }
    return render(request, "dashboard/index.html", context)
