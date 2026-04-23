from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("doar/<slug:slug>/", views.donate_view, name="donate"),
    path("webhook/", views.webhook, name="webhook"),
    path("sucesso/", views.payment_success, name="success"),
    path("falha/", views.payment_failure, name="failure"),
    path("pendente/", views.payment_pending, name="pending"),
]
