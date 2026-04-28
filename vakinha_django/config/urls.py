from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView

from apps.campaigns.models import Campaign


def home_view(request):
    from django.shortcuts import render
    campaigns = (
        Campaign.objects.filter(status=Campaign.STATUS_ACTIVE)
        .select_related("category", "creator")
        .order_by("-created_at")[:6]
    )
    return render(request, "home.html", {"campaigns": campaigns})


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("health/", health_check, name="health"),
    path("accounts/", include("apps.accounts.urls")),
    path("campanhas/", include("apps.campaigns.urls")),
    path("payments/", include("apps.payments.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("ai/", include("apps.ai_agent.urls")),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
