import hashlib
import hmac
import json
import logging
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.campaigns.models import Campaign
from apps.notifications.tasks import send_donation_email, send_whatsapp_notification
from .models import Donation
from .services import create_preference, get_payment_info

logger = logging.getLogger(__name__)

PRESET_AMOUNTS = [10, 25, 50, 100, 250, 500]


def donate_view(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug, status=Campaign.STATUS_ACTIVE)

    if request.method == "POST":
        amount_raw = request.POST.get("amount", "").replace(",", ".")
        custom_amount = request.POST.get("custom_amount", "").replace(",", ".")

        try:
            amount = Decimal(custom_amount if custom_amount else amount_raw)
            if amount < Decimal("1.00"):
                raise ValueError("Valor mínimo é R$ 1,00")
        except (ValueError, Exception) as exc:
            messages.error(request, str(exc) if "mínimo" in str(exc) else "Valor inválido.")
            return redirect("payments:donate", slug=slug)

        donor_name = request.POST.get("donor_name", "").strip()
        donor_email = request.POST.get("donor_email", "").strip()
        message = request.POST.get("message", "").strip()
        anonymous = request.POST.get("anonymous") == "on"

        if not donor_name or not donor_email:
            messages.error(request, "Nome e e-mail são obrigatórios.")
            return redirect("payments:donate", slug=slug)

        donation = Donation.objects.create(
            campaign=campaign,
            donor=request.user if request.user.is_authenticated else None,
            donor_name=donor_name,
            donor_email=donor_email,
            amount=amount,
            message=message,
            anonymous=anonymous,
        )

        try:
            _, init_point = create_preference(donation, request)
            return redirect(init_point)
        except ValueError as exc:
            donation.delete()
            messages.error(request, f"Erro ao processar pagamento: {exc}")
            return redirect("payments:donate", slug=slug)

    return render(request, "payments/donate.html", {
        "campaign": campaign,
        "preset_amounts": PRESET_AMOUNTS,
    })


def payment_success(request):
    payment_id = request.GET.get("payment_id")
    external_ref = request.GET.get("external_reference")
    status = request.GET.get("status")

    donation = None
    if external_ref:
        donation = Donation.objects.filter(mp_external_reference=external_ref).first()

    if donation and status == "approved":
        _approve_donation(donation, payment_id)

    return render(request, "payments/success.html", {"donation": donation})


def payment_failure(request):
    external_ref = request.GET.get("external_reference")
    donation = None
    if external_ref:
        donation = Donation.objects.filter(mp_external_reference=external_ref).first()
        if donation and donation.status == Donation.STATUS_PENDING:
            donation.status = Donation.STATUS_CANCELLED
            donation.save(update_fields=["status"])
    return render(request, "payments/failure.html", {"donation": donation})


def payment_pending(request):
    return render(request, "payments/pending.html", {})


@csrf_exempt
@require_POST
def webhook(request):
    """
    Receives MercadoPago IPN (Instant Payment Notification).
    Validates HMAC signature then updates donation status.
    """
    # Validate MP signature
    sig_header = request.headers.get("x-signature", "")
    sig_id = request.headers.get("x-request-id", "")
    query_id = request.GET.get("data.id", "") or request.GET.get("id", "")

    if settings.MERCADOPAGO_WEBHOOK_SECRET and sig_header:
        parts = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
        ts = parts.get("ts", "")
        v1 = parts.get("v1", "")
        manifest = f"id:{query_id};request-id:{sig_id};ts:{ts};"
        expected = hmac.new(
            settings.MERCADOPAGO_WEBHOOK_SECRET.encode(),
            manifest.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, v1):
            logger.warning("Invalid MercadoPago webhook signature")
            return HttpResponse(status=400)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    topic = body.get("type") or request.GET.get("topic", "")
    resource_id = body.get("data", {}).get("id") or query_id

    if topic != "payment" or not resource_id:
        return HttpResponse(status=200)

    payment_info = get_payment_info(resource_id)
    if not payment_info:
        return HttpResponse(status=200)

    external_ref = payment_info.get("external_reference")
    mp_status = payment_info.get("status")
    payment_method_id = payment_info.get("payment_type_id", "")

    donation = Donation.objects.filter(mp_external_reference=external_ref).first()
    if not donation:
        return HttpResponse(status=200)

    donation.mp_payment_id = str(resource_id)
    donation.payment_method = payment_method_id[:20]
    donation.save(update_fields=["mp_payment_id", "payment_method"])

    if mp_status == "approved" and donation.status != Donation.STATUS_APPROVED:
        _approve_donation(donation, resource_id)
    elif mp_status in ("rejected", "cancelled") and donation.status == Donation.STATUS_PENDING:
        donation.status = Donation.STATUS_REJECTED
        donation.save(update_fields=["status"])

    return HttpResponse(status=200)


def _approve_donation(donation: Donation, payment_id=None):
    """Marks donation as approved and fires notifications."""
    if donation.status == Donation.STATUS_APPROVED:
        return

    donation.status = Donation.STATUS_APPROVED
    if payment_id:
        donation.mp_payment_id = str(payment_id)
    donation.save(update_fields=["status", "mp_payment_id"])

    # Update campaign raised amount
    campaign = donation.campaign
    Campaign.objects.filter(pk=campaign.pk).update(
        raised=campaign.raised + donation.amount
    )
    campaign.refresh_from_db()

    # Fire notifications asynchronously
    send_donation_email.delay(donation.pk)
    if campaign.whatsapp_jid:
        send_whatsapp_notification.delay(
            jid=campaign.whatsapp_jid,
            message=(
                f"🎉 Nova doação recebida!\n\n"
                f"*R$ {donation.amount:.2f}* para sua campanha *{campaign.title}*.\n"
                f"Total arrecadado: R$ {campaign.raised:.2f} de R$ {campaign.goal:.2f}"
            ),
        )
