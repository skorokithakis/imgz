"""The main application's URLs."""
from django.urls import path
from django.urls import re_path
from django.views.generic import TemplateView

from . import api
from . import views

app_name = "main"
urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.image_upload, name="image-upload"),
    path("latest/", views.latest, name="latest"),
    path("logout", views.logout, name="logout"),
    path("help/faq/", TemplateView.as_view(template_name="faq.html"), name="faq"),
    path("help/terms/", TemplateView.as_view(template_name="terms.html"), name="terms"),
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
