"""The main application's URLs."""
from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

from . import api
from . import views
from . import views_payment

app_name = "main"
urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.image_upload, name="image-upload"),
    path("latest/", views.latest, name="latest"),
    path("logout", views.logout, name="logout"),
    re_path(r"^(?P<image_id>i[a-zA-Z0-9]{7})/$", views.image_page, name="image-page"),
    re_path(
        r"^(?P<image_id>i[a-zA-Z0-9]{7})/delete/$",
        views.image_delete,
        name="image-delete",
    ),
    re_path(
        r"^(?P<image_id>i[a-zA-Z0-9]{7})_(?P<size>\d+)\.(?P<extension>\w+)$",
        views.image_show_thumbnail,
        name="image-show-thumb",
    ),
    re_path(
        r"^(?P<image_id>i[a-zA-Z0-9]{7})\.(?P<extension>\w+)$",
        views.image_show,
        name="image-show",
    ),
]

urlpatterns += [
    path("api/image/", api.image_upload, name="api-image-upload"),
    path("api/image/<image_id>/", api.image_detail, name="api-image-detail"),
]

urlpatterns += [
    path("help/faq/", TemplateView.as_view(template_name="faq.html"), name="faq"),
    path("help/terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
]

urlpatterns += [
    path("money/", views_payment.payment_view, name="money"),
    path("money/stripe/", views_payment.stripe_redirect, name="stripe-redirect"),
    path(
        "money/stripe/webhook/",
        views_payment.stripe_webhook,
        name="stripe-webhook",
    ),
    path(
        "money/cryptocurrency/", views_payment.btc_redirect, name="btc-redirect"
    ),
    path(
        "money/cryptocurrency/webhook/",
        views_payment.btc_webhook,
        name="btc-webhook",
    ),
    path("money/thanks/", views_payment.payment_return, name="payment-return"),
]
