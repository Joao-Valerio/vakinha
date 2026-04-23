from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
import uuid


class Campaign(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_ACTIVE = "active"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Rascunho"),
        (STATUS_ACTIVE, "Ativa"),
        (STATUS_COMPLETED, "Concluída"),
        (STATUS_CANCELLED, "Cancelada"),
    ]

    title = models.CharField(max_length=200, verbose_name="Título")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(verbose_name="Descrição")
    goal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Meta (R$)")
    raised = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Arrecadado (R$)"
    )
    creator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="campaigns", verbose_name="Criador"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT, verbose_name="Status"
    )
    image = models.ImageField(
        upload_to="campaigns/", null=True, blank=True, verbose_name="Imagem"
    )
    deadline = models.DateField(null=True, blank=True, verbose_name="Prazo")

    # AI-populated fields
    beneficiary = models.CharField(max_length=200, blank=True, verbose_name="Beneficiário")
    fund_usage = models.TextField(blank=True, verbose_name="Como o dinheiro será usado")
    campaign_reason = models.TextField(blank=True, verbose_name="Motivo da campanha")

    # WhatsApp origin
    created_via_whatsapp = models.BooleanField(default=False)
    whatsapp_jid = models.CharField(max_length=60, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Campanha"
        verbose_name_plural = "Campanhas"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Campaign.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("campaigns:detail", kwargs={"slug": self.slug})

    @property
    def progress_percent(self):
        if not self.goal or self.goal == 0:
            return 0
        percent = (self.raised / self.goal) * 100
        return min(float(percent), 100)

    @property
    def is_goal_reached(self):
        return self.raised >= self.goal

    @property
    def remaining(self):
        return max(self.goal - self.raised, 0)

    @property
    def donors_count(self):
        return self.donations.filter(status="approved").values("donor_email").distinct().count()


class CampaignUpdate(models.Model):
    campaign = models.ForeignKey(
        Campaign, on_delete=models.CASCADE, related_name="updates", verbose_name="Campanha"
    )
    content = models.TextField(verbose_name="Atualização")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Autor"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Atualização"
        verbose_name_plural = "Atualizações"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Atualização de {self.campaign.title} em {self.created_at:%d/%m/%Y}"
