from django import forms
from .models import Campaign, CampaignUpdate


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = (
            "title",
            "description",
            "goal",
            "deadline",
            "image",
            "beneficiary",
            "fund_usage",
            "campaign_reason",
        )
        widgets = {
            "title": forms.TextInput(
                attrs={"placeholder": "Ex: Tratamento de saúde da minha mãe"}
            ),
            "description": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Conte sua história com detalhes..."}
            ),
            "goal": forms.NumberInput(
                attrs={"placeholder": "0.00", "step": "0.01", "min": "10"}
            ),
            "deadline": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
            "beneficiary": forms.TextInput(
                attrs={"placeholder": "Para quem é esta campanha?"}
            ),
            "fund_usage": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Como o dinheiro será utilizado?"}
            ),
            "campaign_reason": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Qual o motivo desta campanha?"}
            ),
        }
        labels = {
            "title": "Título da Campanha",
            "description": "Descrição",
            "goal": "Meta (R$)",
            "deadline": "Prazo",
            "image": "Foto da Campanha",
            "beneficiary": "Beneficiário",
            "fund_usage": "Como será usado o dinheiro",
            "campaign_reason": "Motivo da campanha",
        }


class CampaignUpdateForm(forms.ModelForm):
    class Meta:
        model = CampaignUpdate
        fields = ("content",)
        widgets = {
            "content": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Compartilhe uma novidade com seus doadores..."}
            ),
        }
        labels = {"content": "Nova atualização"}
