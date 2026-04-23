import logging
from celery import shared_task
from .services import send_email, send_whatsapp_message

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    max_retries=3,
    name="notifications.send_donation_email",
)
def send_donation_email(self, donation_pk: int):
    from apps.payments.models import Donation

    try:
        donation = Donation.objects.select_related("campaign", "campaign__creator").get(pk=donation_pk)
    except Donation.DoesNotExist:
        logger.warning("Donation %s not found for email notification", donation_pk)
        return

    campaign = donation.campaign

    # Email to donor
    send_email(
        subject=f"Obrigado pela sua doação a '{campaign.title}'!",
        to_email=donation.donor_email,
        template_html="notifications/email_donation_donor.html",
        context={"donation": donation, "campaign": campaign},
    )

    # Email to campaign creator
    send_email(
        subject=f"Nova doação recebida na sua campanha!",
        to_email=campaign.creator.email,
        template_html="notifications/email_donation_creator.html",
        context={"donation": donation, "campaign": campaign},
    )

    logger.info("Donation emails sent for donation #%s", donation_pk)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    max_retries=3,
    name="notifications.send_whatsapp_notification",
)
def send_whatsapp_notification(self, jid: str, message: str):
    success = send_whatsapp_message(jid, message)
    if not success:
        raise self.retry(countdown=30)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=60,
    max_retries=3,
    name="notifications.send_campaign_update_email",
)
def send_campaign_update_email(self, update_pk: int):
    from apps.campaigns.models import CampaignUpdate
    from apps.payments.models import Donation

    try:
        update = CampaignUpdate.objects.select_related("campaign").get(pk=update_pk)
    except CampaignUpdate.DoesNotExist:
        return

    campaign = update.campaign
    donor_emails = (
        Donation.objects.filter(campaign=campaign, status=Donation.STATUS_APPROVED)
        .values_list("donor_email", flat=True)
        .distinct()
    )

    for email in donor_emails:
        try:
            send_email(
                subject=f"Nova atualização na campanha '{campaign.title}'",
                to_email=email,
                template_html="notifications/email_campaign_update.html",
                context={"update": update, "campaign": campaign},
            )
        except Exception as exc:
            logger.error("Failed update email to %s: %s", email, exc)

    logger.info("Campaign update emails sent for update #%s", update_pk)
