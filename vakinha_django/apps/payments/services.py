import uuid
import logging
from urllib.parse import urljoin, urlparse

import mercadopago
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def _absolute_return_url(request, view_name: str) -> str:
    """Monta URL absoluta para back_urls do Checkout Pro."""
    path = reverse(view_name)
    site = (getattr(settings, "SITE_URL", "") or "").strip().rstrip("/")
    if site and not site.startswith(("http://", "https://")):
        site = f"https://{site}"
    if site:
        return urljoin(f"{site}/", path.lstrip("/"))
    return request.build_absolute_uri(path)


def _url_allows_auto_return(url: str) -> bool:
    """
    Mercado Pago exige back_urls.success com domínio público (não localhost)
    quando auto_return está definido.
    """
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not host:
        return False
    if host in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
        return False
    return True


def get_mp_sdk():
    return mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)


def create_preference(donation, request):
    """
    Creates a MercadoPago preference and returns (preference_id, init_point).
    Raises ValueError on failure.
    """
    sdk = get_mp_sdk()

    external_reference = str(uuid.uuid4())
    donation.mp_external_reference = external_reference
    donation.save(update_fields=["mp_external_reference"])

    site_base = (settings.SITE_URL or "").strip().rstrip("/")
    if not site_base:
        site_base = request.build_absolute_uri("/").rstrip("/")

    back_urls = {
        "success": _absolute_return_url(request, "payments:success"),
        "failure": _absolute_return_url(request, "payments:failure"),
        "pending": _absolute_return_url(request, "payments:pending"),
    }

    preference_data = {
        "items": [
            {
                "id": str(donation.campaign.pk),
                "title": f"Doação para: {donation.campaign.title}",
                "quantity": 1,
                "unit_price": float(donation.amount),
                "currency_id": "BRL",
            }
        ],
        "payer": {
            "name": donation.donor_name,
            "email": donation.donor_email,
        },
        "back_urls": back_urls,
        "external_reference": external_reference,
        "notification_url": urljoin(f"{site_base}/", reverse("payments:webhook").lstrip("/")),
        "payment_methods": {
            "excluded_payment_types": [],
            "installments": 1,
        },
        "statement_descriptor": "Vakinha IA",
    }

    if _url_allows_auto_return(back_urls["success"]):
        preference_data["auto_return"] = "approved"
    else:
        logger.info(
            "auto_return omitido: back_urls.success não é público (%s). "
            "Defina SITE_URL com domínio acessível (ex.: ngrok) para redirecionamento automático.",
            back_urls["success"],
        )

    result = sdk.preference().create(preference_data)

    if result["status"] != 201:
        logger.error("MercadoPago preference creation failed: %s", result)
        raise ValueError(f"Erro ao criar preferência: {result.get('response', {})}")

    response = result["response"]
    preference_id = response["id"]
    init_point = response["init_point"]

    donation.mp_preference_id = preference_id
    donation.save(update_fields=["mp_preference_id"])

    return preference_id, init_point


def get_payment_info(payment_id: str) -> dict:
    """Fetches payment details from MercadoPago."""
    sdk = get_mp_sdk()
    result = sdk.payment().get(payment_id)
    if result["status"] == 200:
        return result["response"]
    logger.error("Failed to fetch MP payment %s: %s", payment_id, result)
    return {}
