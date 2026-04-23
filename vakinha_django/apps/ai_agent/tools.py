import logging
from typing import Dict
from agno import Tool
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
SAÍDA ESTRUTURADA
────────────────────
Sempre que possível, extraia informações da mensagem do usuário e organize internamente nos seguintes campos:

- campaign_reason
- beneficiary
- goal_value
- deadline
- fund_usage
- campaign_stage

────────────────────
FINALIZAÇÃO
────────────────────
Quando todas as informações forem coletadas:

1) Gere um TEXTO DE CAMPANHA claro e humano
2) Resuma os dados principais
3) Pergunte se o usuário deseja:
   - Editar algo
   - Publicar a campanha no site
   - Criar uma mensagem curta para compartilhar

────────────────────
EXEMPLO DE RESPOSTA
────────────────────
"Entendi. Essa campanha é para ajudar sua mãe com o tratamento de saúde.
Agora me conta: qual valor você precisa arrecadar para conseguir pagar esse tratamento?" """


class SendWhatsAppTool(Tool):
    name = "send_whatsapp_message"
    description = "Envia mensagem de volta ao usuário no WhatsApp via Evolution API"

    def __call__(self, remote_jid: str, message: str) -> str:
        success = send_whatsapp_message(remote_jid, message)
        if success:
            return f"Mensagem enviada para {remote_jid}"
        return f"Falha ao enviar mensagem para {remote_jid}"


class CreateCampaignTool(Tool):
    name = "create_campaign"
    description = (
        "Cria campanha de vakinha no banco de dados e retorna ID/link público. "
        "Use quando o usuário confirmar todos os dados e quiser publicar."
    )

    def __call__(self, data: Dict[str, str]) -> str:
        from django.contrib.auth.models import User
        from apps.campaigns.models import Campaign
        from django.conf import settings

        jid = data.get("whatsapp_jid", "")

        # Find user by whatsapp_jid if possible
        creator = None
        if jid:
            try:
                from apps.accounts.models import UserProfile
                profile = UserProfile.objects.select_related("user").get(whatsapp_jid=jid)
                creator = profile.user
            except Exception:
                pass

        if creator is None:
            creator = User.objects.filter(is_superuser=True).first()
            if creator is None:
                return "❌ Não foi possível criar a campanha: nenhum usuário associado ao WhatsApp."

        try:
            goal = float(data.get("goal_value", 0))
        except (ValueError, TypeError):
            goal = 0.0

        campaign = Campaign.objects.create(
            title=data.get("title") or f"Campanha de {data.get('beneficiary', 'vakinha')}",
            description=data.get("description") or data.get("campaign_reason", ""),
            goal=goal,
            creator=creator,
            status=Campaign.STATUS_ACTIVE,
            beneficiary=data.get("beneficiary", ""),
            fund_usage=data.get("fund_usage", ""),
            campaign_reason=data.get("campaign_reason", ""),
            created_via_whatsapp=True,
            whatsapp_jid=jid,
        )

        public_url = f"{settings.SITE_URL}/campanhas/{campaign.slug}/"
        return (
            f"✅ *Campanha criada com sucesso!*\n\n"
            f"📋 *Título:* {campaign.title}\n"
            f"💰 *Meta:* R$ {campaign.goal:.2f}\n"
            f"🔗 *Link:* {public_url}\n\n"
            f"Compartilhe o link com seus contatos para começar a receber doações!"
        )


class PublishToSiteTool(Tool):
    name = "publish_to_site"
    description = "Publica campanha no site oficial e retorna link público"

    def __call__(self, campaign_data: Dict[str, str]) -> str:
        return CreateCampaignTool()(campaign_data)
