from django import forms
from .models import Campaign, CampaignUpdate, Category


class CampaignForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = (
            "title",
            "category",
            "description",
            "goal",
            "deadline",
            "image",
            "beneficiary",
            "fund_usage",
            "campaign_reason",
        )
        widgets = {
            "category": forms.Select(
                attrs={"class": "w-full border border-gray-200 rounded-xl py-2.5 px-3 text-sm focus:ring-2 focus:ring-primary-400 focus:border-transparent bg-white"}
            ),
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
            "category": "Categoria",
            "title": "Título da Campanha",
            "description": "Descrição",
            "goal": "Meta (R$)",
            "deadline": "Prazo",
            "image": "Foto da Campanha",
            "beneficiary": "Beneficiário",
            "fund_usage": "Como será usado o dinheiro",
            "campaign_reason": "Motivo da campanha",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        fld = self.fields["category"]
        fld.queryset = Category.objects.order_by("ordering", "name")
        fld.required = True
        fld.empty_label = "Escolha uma categoria…"


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
