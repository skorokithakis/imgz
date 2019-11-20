from django.http import HttpRequest
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from .models import Image
from .models import User
from .utils import construct_error_response
from .utils import process_upload
from .utils import UploadError


@require_POST
def image_upload(request: HttpRequest) -> JsonResponse:
    user = User.objects.filter(api_key=request.GET.get("api_key")).first()
    if not user:
        return construct_error_response(
            1, "Invalid API key, I guess? I don't know what you're trying to do."
        )

    try:
        image = process_upload(request.FILES, user)
    except UploadError as e:
        return construct_error_response(3, str(e))
    else:
        return JsonResponse(
            image.as_dict(), json_dumps_params={"indent": 2, "sort_keys": True}
        )


@require_http_methods(["GET", "DELETE"])
def image_detail(request: HttpRequest, image_id: str) -> JsonResponse:
    image = Image.objects.filter(id=image_id).first()
    if not image:
        return construct_error_response(1, "Image not found.", status_code=404)

    if request.method == "DELETE":
        user = User.objects.filter(api_key=request.GET.get("api_key")).first()
        if not user:
            return construct_error_response(
                1, "Invalid API key, I guess? I don't know what you're trying to do."
            )

        if image.user != user:
            return construct_error_response(2, "That's not your image, quit playing.")

        image.delete()
        return JsonResponse({})
    else:
        return JsonResponse(
            image.as_dict(), json_dumps_params={"indent": 2, "sort_keys": True}
        )
