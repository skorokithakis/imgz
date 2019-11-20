from typing import Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_POST
from loginas.utils import restore_original_login

from .models import Image
from .utils import process_upload
from .utils import UploadError


@login_required
def logout(request):
    restore_original_login(request)
    return redirect(settings.LOGOUT_REDIRECT_URL)


def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        if request.user.is_paying:
            return render(
                request,
                "paying.html",
                {"images": request.user.images.order_by("-uploaded")},
            )
        else:
            template = "home.html"
    else:
        template = "index.html"

    return render(request, template)


def image_show_thumbnail(
    request: HttpRequest, image_id: str, size: str, extension: Optional[str] = None
) -> HttpResponse:
    """
    Show a bare image.
    """
    image = get_object_or_404(Image, pk=image_id)
    if size != "512":
        return HttpResponseNotFound("Thumbnail not found.")

    data = bytes(image.thumbnail_512)
    response = HttpResponse(data, content_type=f"image/{image.format}")
    response["Content-Length"] = len(data)
    return response


def image_page(
    request: HttpRequest, image_id: str, extension: Optional[str] = None
) -> HttpResponse:
    """
    Show an image page.
    """
    image = get_object_or_404(Image, pk=image_id)
    image.increment_views()
    return render(request, "image.html", {"image": image})


def image_show(
    request: HttpRequest, image_id: str, extension: Optional[str] = None
) -> HttpResponse:
    """
    Show a bare image.
    """
    image = get_object_or_404(Image, pk=image_id)
    # We cast to bytes here because this is a memoryview on Postgres
    # but just bytes on SQLite.
    data = bytes(image.data)
    response = HttpResponse(data, content_type=f"image/{image.format}")
    response["Content-Length"] = len(data)
    return response


@login_required
@require_POST
def image_delete(
    request: HttpRequest, image_id: str, extension: Optional[str] = None
) -> HttpResponse:
    get_object_or_404(Image, pk=image_id, user=request.user).delete()
    messages.success(request, "Okay, the image is gone. It was a dick pic, wasn't it?")
    return redirect("main:index")


@login_required
def image_upload(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return render(request, "upload.html")

    try:
        image = process_upload(request.FILES, request.user)
    except UploadError as e:
        messages.error(request, str(e))
        return redirect("main:index")
    else:
        return redirect(image)
