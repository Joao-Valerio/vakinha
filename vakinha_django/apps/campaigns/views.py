from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Campaign, CampaignUpdate
from .forms import CampaignForm, CampaignUpdateForm


def campaign_list(request):
    campaigns = Campaign.objects.filter(status=Campaign.STATUS_ACTIVE).select_related("creator")
    query = request.GET.get("q", "")
    if query:
        campaigns = campaigns.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    paginator = Paginator(campaigns, 12)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "campaigns/list.html", {"page_obj": page, "query": query})


def campaign_detail(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug)
    if campaign.status == Campaign.STATUS_DRAFT and campaign.creator != request.user:
        from django.http import Http404
        raise Http404

    updates = campaign.updates.all()
    donations = campaign.donations.filter(status="approved", anonymous=False).order_by("-created_at")[:10]
    update_form = None

    if request.user == campaign.creator:
        if request.method == "POST":
            update_form = CampaignUpdateForm(request.POST)
            if update_form.is_valid():
                update = update_form.save(commit=False)
                update.campaign = campaign
                update.author = request.user
                update.save()
                messages.success(request, "Atualização publicada!")
                return redirect("campaigns:detail", slug=slug)
        else:
            update_form = CampaignUpdateForm()

    return render(request, "campaigns/detail.html", {
        "campaign": campaign,
        "updates": updates,
        "donations": donations,
        "update_form": update_form,
    })


@login_required
def campaign_create(request):
    if request.method == "POST":
        form = CampaignForm(request.POST, request.FILES)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.creator = request.user
            campaign.status = Campaign.STATUS_ACTIVE
            campaign.save()
            messages.success(request, "Campanha criada com sucesso!")
            return redirect("campaigns:detail", slug=campaign.slug)
    else:
        form = CampaignForm()
    return render(request, "campaigns/create.html", {"form": form})


@login_required
def campaign_edit(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug, creator=request.user)
    if request.method == "POST":
        form = CampaignForm(request.POST, request.FILES, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, "Campanha atualizada!")
            return redirect("campaigns:detail", slug=campaign.slug)
    else:
        form = CampaignForm(instance=campaign)
    return render(request, "campaigns/edit.html", {"form": form, "campaign": campaign})


@login_required
def campaign_toggle_status(request, slug):
    campaign = get_object_or_404(Campaign, slug=slug, creator=request.user)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "activate" and campaign.status == Campaign.STATUS_DRAFT:
            campaign.status = Campaign.STATUS_ACTIVE
            messages.success(request, "Campanha ativada!")
        elif action == "pause" and campaign.status == Campaign.STATUS_ACTIVE:
            campaign.status = Campaign.STATUS_DRAFT
            messages.success(request, "Campanha pausada.")
        elif action == "complete" and campaign.status == Campaign.STATUS_ACTIVE:
            campaign.status = Campaign.STATUS_COMPLETED
            messages.success(request, "Campanha encerrada.")
        campaign.save()
    return redirect("campaigns:detail", slug=slug)
