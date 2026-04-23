from django.urls import path
from . import views

app_name = "campaigns"

urlpatterns = [
    path("", views.campaign_list, name="list"),
    path("criar/", views.campaign_create, name="create"),
    path("<slug:slug>/", views.campaign_detail, name="detail"),
    path("<slug:slug>/editar/", views.campaign_edit, name="edit"),
    path("<slug:slug>/status/", views.campaign_toggle_status, name="toggle_status"),
]
