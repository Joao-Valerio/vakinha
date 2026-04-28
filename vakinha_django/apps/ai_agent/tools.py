import logging
from typing import Any, Dict, List, Optional

from apps.notifications.services import send_whatsapp_message

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um assistente especializado na criação de campanhas de vakinha (arrecadação coletiva), atuando via WhatsApp e site.

Responda todas as mensagem em portugues

Seu objetivo é guiar o usuário de forma clara, empática e eficiente para criar uma campanha completa e persuasiva, sem pressionar e sem parecer robótico.

────────────────────
COMPORTAMENTO GERAL
────────────────────
- Use linguagem simples, humana e acolhedora
- Seja direto, mas empático
- Nunca peça muitas informações de uma vez
- Faça uma pergunta por mensagem
- Não repita perguntas já respondidas
- Se algo estiver confuso, peça esclarecimento
- Adapte o tom ao sentimento do usuário (urgência, tristeza, esperança)

────────────────────
ETAPAS DA CAMPANHA
────────────────────
Você deve coletar, nesta ordem lógica (mas flexível):

1) Motivo da campanha
2) Para quem é a campanha
3) Objetivo financeiro (valor desejado)
4) Prazo ou urgência
5) Como o dinheiro será usado
6) Se o usuário deseja ajuda para escrever o texto final
7) Se deseja divulgar via WhatsApp ou redes sociais

────────────────────
REGRAS IMPORTANTES
────────────────────
- Se o usuário já informar algum dado espontaneamente, NÃO pergunte novamente
- Se o usuário mencionar valores vagos ("uns 3 mil", "mais ou menos"), confirme
- Se o usuário demonstrar emoção forte, valide o sentimento antes de continuar
- Nunca invente dados
- Nunca finalize a campanha sem confirmar os dados principais

────────────────────
FERRAMENTAS
────────────────────
- Use a ferramenta de criar campanha somente quando o usuário confirmar que quer publicar e você tiver título, descrição/motivo, beneficiário e meta em valores claros.
"""


def _create_campaign_from_dict(data: Dict[str, Any]) -> str:
    from django.conf import settings
    from django.contrib.auth.models import User
    from apps.campaigns.models import Campaign, Category
    from apps.accounts.models import UserProfile

    jid = (data.get("whatsapp_jid") or "").strip()

    creator = None
    if jid:
        try:
            profile = UserProfile.objects.select_related("user").get(whatsapp_jid=jid)
            creator = profile.user
        except UserProfile.DoesNotExist:
            pass

    if creator is None:
        creator = User.objects.filter(is_superuser=True).first()
        if creator is None:
            return "❌ Não foi possível criar a campanha: nenhum usuário (superuser) no sistema. Crie um admin no site."

    try:
        goal = float(data.get("goal_value") or 0)
    except (TypeError, ValueError):
        goal = 0.0

    outros = Category.objects.filter(slug="outros").first()
    slug_cat = (data.get("category_slug") or "").strip()
    cat = Category.objects.filter(slug=slug_cat).first() if slug_cat else None
    if cat is None:
        cat = outros

    campaign = Campaign.objects.create(
        title=data.get("title") or f"Campanha de {data.get('beneficiary', 'vakinha')}",
        description=(data.get("description") or data.get("campaign_reason") or "").strip() or "Campanha criada via WhatsApp.",
        goal=goal,
        creator=creator,
        category=cat,
        status=Campaign.STATUS_ACTIVE,
        beneficiary=(data.get("beneficiary") or "")[:200],
        fund_usage=(data.get("fund_usage") or "")[:2000],
        campaign_reason=(data.get("campaign_reason") or "")[:2000],
        created_via_whatsapp=True,
        whatsapp_jid=jid,
    )
    public_url = f"{settings.SITE_URL.rstrip('/')}/campanhas/{campaign.slug}/"
    return (
        f"✅ *Campanha criada com sucesso!*\n\n"
        f"📋 *Título:* {campaign.title}\n"
        f"💰 *Meta:* R$ {campaign.goal:.2f}\n"
        f"🔗 *Link:* {public_url}\n\n"
        f"Compartilhe o link com seus contatos para começar a receber doações!"
    )


def build_tools_for_session(remote_jid: str) -> List:
    """
    Ferramentas compatíveis com agno 2.x (funções com docstring, registradas no Agent).
    """
    if not remote_jid:
        remote_jid = ""

    def send_whatsapp_reply(message: str) -> str:
        """Envia uma mensagem de texto para o usuário no WhatsApp (Evolution API). Use após formular a resposta ao usuário.

        Args:
            message: Texto a enviar (pode usar formatação simples).
        """
        success = send_whatsapp_message(remote_jid, message)
        if success:
            return f"Mensagem enviada."
        return "Falha ao enviar mensagem (verifique EVOLUTION_* no .env)."

    def create_whatsapp_campaign(
        title: str = "",
        description: str = "",
        campaign_reason: str = "",
        beneficiary: str = "",
        goal_value: str = "0",
        deadline: str = "",
        fund_usage: str = "",
    ) -> str:
        """Cria e publica a campanha no site. Chame somente após o usuário confirmar os dados e pedir para publicar.

        Args:
            title: Título curto da campanha
            description: Descrição completa (pode ser igual ao motivo)
            campaign_reason: Motivo / história
            beneficiary: Para quem é a arrecadação
            goal_value: Meta financeira (número, ex: 5000 ou 5000.00)
            deadline: Prazo ou data relevante (texto)
            fund_usage: Como o dinheiro será usado
        """
        _ = deadline  # guardado no modelo Campaign.deadline se precisar mapear depois
        data: Dict[str, Any] = {
            "title": title.strip(),
            "description": (description or campaign_reason or "").strip(),
            "campaign_reason": (campaign_reason or "").strip(),
            "beneficiary": (beneficiary or "").strip(),
            "goal_value": goal_value,
            "fund_usage": (fund_usage or "").strip(),
            "whatsapp_jid": remote_jid,
        }
        return _create_campaign_from_dict(data)

    return [send_whatsapp_reply, create_whatsapp_campaign]
