from django.db import models
from django.contrib.auth.models import User
from apps.campaigns.models import Campaign


class Donation(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_REFUNDED = "refunded"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendente"),
        (STATUS_APPROVED, "Aprovado"),
        (STATUS_REJECTED, "Rejeitado"),
        (STATUS_CANCELLED, "Cancelado"),
        (STATUS_REFUNDED, "Reembolsado"),
    ]

    PAYMENT_PIX = "pix"
    PAYMENT_CREDIT_CARD = "credit_card"
    PAYMENT_BOLETO = "boleto"

    PAYMENT_METHOD_CHOICES = [
        (PAYMENT_PIX, "PIX"),
        (PAYMENT_CREDIT_CARD, "Cartão de Crédito"),
        (PAYMENT_BOLETO, "Boleto"),
    ]

    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="donations", verbose_name="Campanha"
    )
    donor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
        verbose_name="Doador (conta)",
    )
    donor_name = models.CharField(max_length=100, verbose_name="Nome do doador")
    donor_email = models.EmailField(verbose_name="E-mail do doador")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Valor (R$)")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name="Status"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, verbose_name="Método de pagamento"
    )
    message = models.TextField(blank=True, verbose_name="Mensagem para o criador")
    anonymous = models.BooleanField(default=False, verbose_name="Doação anônima")

    # MercadoPago IDs
    mp_preference_id = models.CharField(max_length=200, blank=True)
    mp_payment_id = models.CharField(max_length=100, blank=True)
    mp_external_reference = models.CharField(max_length=100, blank=True, unique=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Doação"
        verbose_name_plural = "Doações"
        ordering = ["-created_at"]

    def __str__(self):
        name = "Anônimo" if self.anonymous else self.donor_name
        return f"R$ {self.amount} de {name} para {self.campaign.title}"

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED
