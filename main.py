# main.py - WhatsApp Campaign Agent (Agno) - VERSÃO FINAL
import os
import asyncio
import json
import base64
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
from agno import Agent, Tool
from agno.llms import GoogleGenerativeAI
from agno.memory import PostgresChatMemory
import google.generativeai as genai

load_dotenv()

app = FastAPI(title="WhatsApp Campaign Agent")

# ========================================
# CONFIGURAÇÕES (carregadas do .env)
# ========================================
EVOLUTION_URL = os.getenv("EVOLUTION_API_URL")
INSTANCE = os.getenv("EVOLUTION_INSTANCE")
EVOLUTION_TOKEN = os.getenv("EVOLUTION_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
POSTGRES_URL = os.getenv("POSTGRES_URL")

# SITE (COMENTADO - DESCOMENTE QUANDO ESTIVER PRONTO)
# SITE_API_URL = os.getenv("SITE_API_URL")
# SITE_API_TOKEN = os.getenv("SITE_API_TOKEN")

genai.configure(api_key=GEMINI_KEY)

# System Prompt (copiado EXATAMENTE do seu n8n)
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
   - Publicar a campanha
   - Criar uma mensagem curta para compartilhar

────────────────────
EXEMPLO DE RESPOSTA
────────────────────
"Entendi. Essa campanha é para ajudar sua mãe com o tratamento de saúde.  
Agora me conta: qual valor você precisa arrecadar para conseguir pagar esse tratamento?" """

# Armazenamento temporário de campanhas (até ter o site)
campaigns: Dict[str, Dict] = {}

# ========================================
# TOOL: Enviar mensagem WhatsApp
# ========================================
class SendWhatsAppTool(Tool):
    name = "send_whatsapp_message"
    description = "Envia mensagem de volta ao usuário no WhatsApp via Evolution API"
    
    def __call__(self, remote_jid: str, message: str, instance: str = INSTANCE) -> str:
        url = f"{EVOLUTION_URL}/{instance}/message/sendText/{remote_jid}"
        headers = {"apikey": EVOLUTION_TOKEN}
        payload = {
            "delay": 3000,
            "presence": "composing",
            "linkPreview": True,
            "message": message
        }
        response = requests.post(url, json=payload, headers=headers)
        return f"✅ Mensagem enviada para {remote_jid} (Status: {response.status_code})"

# ========================================
# TOOL: Criar campanha (TEMPORÁRIO - em memória)
# ========================================
class CreateCampaignTool(Tool):
    name = "create_campaign"
    description = "Cria campanha de vakinha e retorna ID/link (TEMPORÁRIO - em memória)"
    
    def __call__(self, data: Dict[str, str]) -> str:
        campaign_id = f"campanha_{hash(json.dumps(data))}"
        campaigns[campaign_id] = data
        link = f"https://seusite.com/campanhas/{campaign_id}"
        return f"✅ *Campanha criada com sucesso!*\n\n📋 *ID:* `{campaign_id}`\n🔗 *Link:* {link}\n\nDados salvos:\n" + "\n".join([f"• {k}: {v}" for k, v in data.items()])

# ========================================
# TOOL: Publicar no site (COMENTADA - PRONTO PARA USAR)
# ========================================

class PublishToSiteTool(Tool):
    name = "publish_to_site"
    description = "Publica campanha no site oficial e retorna link público"
    
    def __call__(self, campaign_data: Dict[str, str]) -> str:
        url = f"{http://127.0.0.1:8000}/campanhas"
        headers = {
            "Authorization": f"Bearer {1234567890}",
            "Content-Type": "application/json"
        }
        payload = {
            "title": campaign_data.get("title", "Campanha Vakinha"),
            "description": campaign_data.get("description", ""),
            "goal_value": float(campaign_data.get("goal_value", 0)),
            "deadline": campaign_data.get("deadline", ""),
            "beneficiary": campaign_data.get("beneficiary", ""),
            "reason": campaign_data.get("reason", "")
        }
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 201:
            data = response.json()
            return f"🚀 *Campanha publicada no site!*\n🔗 {data['public_url']}\n📊 ID: {data['id']}"
        else:
            return f"❌ Erro ao publicar: {response.text}"

# ========================================
# Função: Transcrever áudio (Groq Whisper)
# ========================================
async def transcribe_audio(instance: str, message_id: str) -> str:
    # 1. Obter áudio via Evolution API
    url = f"{EVOLUTION_URL}/{instance}/chat/{message_id}"
    headers = {"apikey": EVOLUTION_TOKEN}
    response = requests.get(url, headers=headers)
    audio_data_b64 = response.json().get("audioMessage", {}).get("data")
    
    if not audio_data_b64:
        return "❌ Erro ao baixar áudio"
    
    # 2. Base64 → bytes
    audio_bytes = base64.b64decode(audio_data_b64)
    
    # 3. Groq Whisper
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}"}
    files = {"file": ("audio.ogg", audio_bytes, "audio/ogg")}
    data = {
        "model": "whisper-large-v3",
        "response_format": "json",
        "language": "pt",
        "temperature": 0
    }
    response = requests.post(url, headers=headers, files=files, data=data)
    
    result = response.json()
    return result.get("text", "❌ Erro na transcrição")

# ========================================
# Agente principal (Agno)
# ========================================
async def create_agent(remote_jid: str):
    memory = PostgresChatMemory(
        connection_string=POSTGRES_URL,
        session_id=remote_jid  # Memória por conversa (igual n8n)
    )
    
    agent = Agent(
        name="VakinhaAssistant",
        llm=GoogleGenerativeAI(model="gemini-1.5-flash", api_key=GEMINI_KEY),
        system_prompt=SYSTEM_PROMPT,
        memory=memory,
        tools=[SendWhatsAppTool(), CreateCampaignTool()]  # DESCOMENTE PublishToSiteTool() depois
    )
    return agent

# ========================================
# WEBHOOK PRINCIPAL (equivalente ao seu Webhook n8n)
# ========================================
@app.post("/198dba35-1ff0-4e33-ba8b-59ac5f54178d")
async def whatsapp_webhook(request: Request):
    try:
        data = await request.json()
        
        # Extrair dados (igual nó "Dados")
        body = data.get("body", {})
        instance_key = body.get("instance")
        remote_jid = body["data"]["key"]["remoteJid"]
        message_id = body["data"]["key"]["id"]
        message_type = body["data"]["messageType"]
        conversation = body["data"]["message"].get("conversation", "")
        
        print(f"📱 [{remote_jid}] {conversation[:50]}...")
        
        # SWITCH: Áudio ou Texto (igual seu Switch)
        if message_type == "audioMessage":
            print("🎤 Transcrevendo áudio...")
            message = await transcribe_audio(instance_key, message_id)
        else:
            message = conversation
        
        if not message.strip():
            return JSONResponse({"status": "empty message"})
        
        # Executar Agente Agno (igual seu AI Agent)
        agent = await create_agent(remote_jid)
        response = await agent.run(message)
        
        print(f"🤖 Resposta: {response[:100]}...")
        
        return JSONResponse({
            "status": "success",
            "remoteJid": remote_jid,
            "message": response
        })
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
