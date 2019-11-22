from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import User
from opennode import OpenNode

stripe.api_key = settings.STRIPE_SECRET_KEY

STRIPE_REF_ID = "IMGZ"


def get_price() -> Decimal:
    return Decimal(settings.ANNUAL_PRICE_PER_GB + (User.objects.all().count() / 1000))


@require_http_methods(["POST"])
def stripe_webhook(request):
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.META["HTTP_STRIPE_SIGNATURE"],
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    refid = event.data.object.client_reference_id
    if not refid or not refid.startswith(f"{STRIPE_REF_ID}|"):
        return HttpResponse("K")
    customer_id = refid.split("|")[1]

    user = User.objects.filter(pk=customer_id).first()
    if user:
        user.upgrade()
    return HttpResponse("K")


@require_http_methods(["POST"])
def btc_webhook(request):
    opennode = OpenNode(settings.OPENNODE_API_KEY)
    if (
        "id" not in request.POST
        or "order_id" not in request.POST
        or "|" not in request.POST["order_id"]
        or "hashed_order" not in request.POST
        or opennode.verify_data(request.POST["id"], request.POST["hashed_order"])
        is False
    ):
        return HttpResponse("H")

    if not request.POST.get("status", "") == "paid":
        return HttpResponse("I")

    _, user_id = request.POST["order_id"].split("|")
    user = User.objects.filter(pk=user_id).first()
    if user:
        user.upgrade()
    return HttpResponse("K")


@login_required
def stripe_redirect(request):
    """
    Redirect to the Stripe URL.

    This is done because we need to generate an invoice on the Stripe side, which is
    a rather heavy operation, so we don't want to do it on every load of the pricing
    page.
    """
    session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        client_reference_id=f"{STRIPE_REF_ID}|{request.user.id}",
        payment_method_types=["card"],
        line_items=[
            {
                "name": request.site.name,
                "description": f"ONE YEAR OF {request.site.name}",
                "amount": int(get_price() * 100),
                "currency": "usd",
                "quantity": 1,
            }
        ],
        success_url=f"https://{request.site.domain}{reverse('main:payment-return')}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"https://{request.site.domain}{reverse('main:money')}",
    )

    context = {"stripe_session_id": session.id, "price": get_price()}
    return render(request, "money.html", context)


@login_required
def btc_redirect(request):
    """
    Redirect to the cryptocurrency processor URL.

    This is done because we need to generate an invoice on the processor side, which is
    a rather heavy operation, so we don't want to do it on every load of the pricing
    page.
    """
    opennode = OpenNode(
        settings.OPENNODE_API_KEY,
        f"https://{request.site.domain}{reverse('main:btc-webhook')}",
        f"https://{request.site.domain}{reverse('main:payment-return')}?p=c",
        settings.DEBUG,
    )
    i = opennode.get_invoice(
        get_price(),
        "USD",
        "One Gigabyte of IMGZ Please",
        "IMGZ...er?",
        request.user.email,
        order_id=f"{get_price()}|{request.user.id}",
    )
    return redirect(i["invoice_url"])


def payment_view(request):
    return render(request, "money.html", {"price": get_price()})


def payment_return(request):
    return render(request, "thanks.html")
