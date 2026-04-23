from django.urls import path
from . import views

app_name = "ai_agent"

urlpatterns = [
    path("webhook/<str:token>/", views.whatsapp_webhook, name="webhook"),
]
