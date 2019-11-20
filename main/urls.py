"""The main application's URLs."""
from django.urls import path
from django.urls import re_path

from . import api
from . import views

app_name = "main"
urlpatterns = [
    path("", views.index, name="index"),
    path("logout", views.logout, name="logout"),
    path("upload/", views.image_upload, name="image-upload"),
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
    path("api/images/", api.image_upload, name="api-image-upload"),
    path("api/images/<image_id>/", api.image_detail, name="api-image-detail"),
]
