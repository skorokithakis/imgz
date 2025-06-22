from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import User
from opennode import OpenNode

stripe.api_key = settings.STRIPE_SECRET_KEY

STRIPE_REF_ID = "IMGZ"


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
        print("Invalid payload")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        print("Invalid signature")
        return HttpResponse(status=400)

    if event.type != "charge.succeeded":
        return HttpResponse("Wrong type.")

    if not event.data.object.invoice:
        return HttpResponse("No invoice.")

    invoice = stripe.Invoice.retrieve(event.data.object.invoice)
    subscription_id = invoice.subscription
    subscription = stripe.Subscription.retrieve(subscription_id)

    # Ignore any subscription that does not belong to IMGZ
    if subscription.metadata.get("property") != STRIPE_REF_ID:
        return HttpResponse("Wrong property.")

    # Safe access – still assumes the keys exist for IMGZ subscriptions,
    # but won’t crash if they are missing.
    plan_id = subscription.metadata.get("plan")
    user_id = subscription.metadata.get("user_id")

    user = User.objects.filter(pk=user_id).first()

    if not user:
        return HttpResponse("No user.")

    GB = settings.GB
    space = {
        "1GB": 1 * GB,
        "2GB": 2 * GB,
        "50GB": 50 * GB,
        "500GB": 500 * GB,
        "ALLOFIT": 1 * GB,
    }[plan_id]

    user.start_stripe_subscription(subscription_id, space)

    return HttpResponse("K")


def stripe_redirect(request):
    """
    Redirect to the Stripe URL.

    This is done because we need to generate an invoice on the Stripe side, which is
    a rather heavy operation, so we don't want to do it on every load of the pricing
    page.
    """
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in first, duh.")
        return redirect("main:index")

    plan = request.GET.get("plan", "2GB")
    plan = plan if plan in ("2GB", "50GB", "500GB", "ALLOFIT") else "2GB"
    session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        client_reference_id=f"{STRIPE_REF_ID}|{request.user.id}|{plan}",
        payment_method_types=["card"],
        subscription_data={
            "metadata": {
                "property": STRIPE_REF_ID,
                "user_id": request.user.id,
                "plan": plan,
            },
            "items": [{"plan": plan, "quantity": 1}],
        },
        success_url=f"https://{request.site.domain}{reverse('main:payment-return')}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"https://{request.site.domain}{reverse('main:money')}",
    )

    context = {"stripe_session_id": session.id}
    return render(request, "money.html", context)


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
        user.upgrade(2 * settings.GB)
    return HttpResponse("K")


def btc_redirect(request):
    """
    Redirect to the cryptocurrency processor URL.

    This is done because we need to generate an invoice on the processor side, which is
    a rather heavy operation, so we don't want to do it on every load of the pricing
    page.
    """
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in first, duh.")
        return redirect("main:index")

    opennode = OpenNode(
        settings.OPENNODE_API_KEY,
        f"https://{request.site.domain}{reverse('main:btc-webhook')}",
        f"https://{request.site.domain}{reverse('main:payment-return')}?p=c",
        settings.DEBUG,
    )
    i = opennode.get_invoice(
        Decimal(12),
        "USD",
        "Two Gigabytes of IMGZ Please",
        "IMGZ...er?",
        request.user.email,
        order_id=f"{12}|{request.user.id}",
    )
    return redirect(i["invoice_url"])
