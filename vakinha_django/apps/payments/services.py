import uuid
import logging
import mercadopago
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


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

    base_url = settings.SITE_URL
    back_urls = {
        "success": base_url + reverse("payments:success"),
        "failure": base_url + reverse("payments:failure"),
        "pending": base_url + reverse("payments:pending"),
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
        "auto_return": "approved",
        "external_reference": external_reference,
        "notification_url": base_url + reverse("payments:webhook"),
        "payment_methods": {
            "excluded_payment_types": [],
            "installments": 1,
        },
        "statement_descriptor": "Vakinha IA",
    }

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
