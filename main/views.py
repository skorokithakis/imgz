from typing import Optional

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from .models import Image
from .models import User


def construct_error_response(
    error_code: int, error_message: str, status_code: int = 422
) -> JsonResponse:
    """
    Construct a JsonResponse error message.

    This is just a boilerplate-saving class.
    """
    response = JsonResponse({"error_code": error_code, "error_message": error_message})
    response.status_code = status_code
    return response


def index(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return render(request, "home.html")
    else:
        return render(request, "index.html")


def image_page(
    request: HttpRequest, image_id: str, extension: Optional[str] = None
) -> HttpResponse:
    """
    Show an image page.
    """
    image = get_object_or_404(Image, pk=image_id)
    return render(request, "image.html", {"image": image})


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
def image_upload(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("main:index")

    user = request.user
    if not user.can_upload:
        messages.error(request, "You cannot upload files, you need to pay. PAY!")
        return redirect("main:index")

    if "data" not in request.FILES:
        messages.error(request, "You need to specify an image to upload.")
        return redirect("main:index")

    data = request.FILES["data"].read()
    name = request.FILES["data"].name
    try:
        image = Image.objects.create(data=data, user=user, name=name)
    except OSError:
        messages.error(
            request, "That file was straight trash, try uploading something else."
        )
        return redirect("main:index")

    return redirect(image)


@require_POST
def api_image_upload(request: HttpRequest) -> JsonResponse:
    user = User.objects.filter(api_key=request.GET.get("api_key")).first()
    if not user:
        return construct_error_response(
            1, "Invalid API key, I guess? I don't know what you're trying to do."
        )

    if not user.can_upload:
        return construct_error_response(2, "No upload without money! Pay now!")

    if "data" not in request.FILES:
        return construct_error_response(
            4, "You're trying to do something funky there but I don't know what."
        )

    data = request.FILES["data"].read()
    name = request.FILES["data"].name
    try:
        image = Image.objects.create(data=data, user=user, name=name)
    except OSError:
        return construct_error_response(
            3, "That image file was straight trash. Get a good one."
        )
    except ValueError as e:
        return construct_error_response(4, str(e))

    return JsonResponse(
        image.as_dict(), json_dumps_params={"indent": 2, "sort_keys": True}
    )


@require_GET
def api_image_detail(request: HttpRequest, image_id: str) -> JsonResponse:
    image = Image.objects.filter(id=image_id).first()
    if not image:
        response = construct_error_response(1, "Image not found.", status_code=404)
    else:
        return JsonResponse(
            image.as_dict(), json_dumps_params={"indent": 2, "sort_keys": True}
        )
    return response
