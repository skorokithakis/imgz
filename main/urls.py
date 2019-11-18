"""The main application's URLs."""
from django.urls import path
from django.urls import re_path

from . import views

app_name = "main"
urlpatterns = [
    path("", views.index, name="index"),
    path("upload/", views.image_upload, name="image-upload"),
    re_path(r"^i(?P<image_id>[a-zA-Z0-9]{7})/$", views.image_show, name="image-show"),
    re_path(
        r"^i(?P<image_id>[a-zA-Z0-9]{7})(\.\w+|/)$",
        views.image_show,
        name="image-show-ext",
    ),
]
