from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .models import Image


def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return render(request, "home.html")
    else:
        return render(request, "index.html")


def image_show(request: HttpRequest, image_id: str) -> HttpResponse:
    """Show an image."""
    image = get_object_or_404(Image, pk=image_id)
    response = HttpResponse(image.data, content_type=f"image/{image.format}")
    response["Content-Length"] = len(image.data)
    return response


@login_required
def image_upload(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("main:index")

    user = request.user
    if not user.can_upload:
        messages.error(request, "You cannot upload files.")
        return redirect("main:index")

    data = request.FILES["data"].read()
    name = request.FILES["data"].name
    image = Image.objects.create(data=data, user=user, name=name)
    return redirect(image)
