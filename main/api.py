import base64
import json
from typing import Any
from typing import Optional

from django.http import JsonResponse
from django.views.generic import View

from .models import Image
from .models import User
from .utils import process_upload
from .utils import UploadError


class APIView(View):
    def _construct_error_response(
        self, error_code: int, error_message: str, status_code: int = 422
    ) -> JsonResponse:
        """
        Construct a JsonResponse error message.
        """
        response = JsonResponse(
            {"error_code": error_code, "error_message": error_message}
        )
        response.status_code = status_code
        return response

    def _get_auth(self) -> Optional[User]:
        """
        Check the basic auth headers and return a user if they're valid.
        """
        auth = self.request.META.get("HTTP_AUTHORIZATION", "").split()
        if len(auth) != 2 or auth[0].lower() != "basic":
            return None

        try:
            _, api_key = base64.b64decode(auth[1].encode()).split(b":")
        except Exception:
            return None

        user = User.objects.filter(api_key=api_key.decode()).first()
        return user

    def dispatch(self, *args, **kwargs):
        self.image = None

        if self.request.method in ("PUT", "DELETE") or (
            self.request.method == "GET" and "image_id" in kwargs
        ):
            self.image = Image.objects.filter(id=kwargs.get("image_id", "")).first()
            if not self.image:
                return self._construct_error_response(
                    1, "That image doesn't even exist.", status_code=404
                )

        self.json: Any = {}
        if self.request.headers.get("Content-Type") == "application/json":
            try:
                self.json = json.loads(self.request.body)
            except:  # noqa
                return self._construct_error_response(
                    7, "Error while decoding your JSON content."
                )

        assert self.request.method
        handler = getattr(self, self.request.method.lower(), None)

        # Support optional auth.
        self.user = self._get_auth()
        if getattr(handler, "needs_auth", True):
            if not self.user:
                return self._construct_error_response(
                    1,
                    "Invalid API key, I guess? I don't know what you're trying to do.",
                )

        if self.user and self.image and self.image.user != self.user:
            # Check that the image belongs to this user.
            return self._construct_error_response(
                2, "That's not your image, quit playing."
            )

        data = super().dispatch(*args, **kwargs)

        if isinstance(data, JsonResponse):
            return data

        return JsonResponse(data, json_dumps_params={"indent": 2, "sort_keys": True})


class ImageView(APIView):
    def get(self, request, image_id=None):
        if image_id:
            assert self.image
            return JsonResponse(
                self.image.as_dict(), json_dumps_params={"indent": 2, "sort_keys": True}
            )
        else:
            if not self.user:
                return self._construct_error_response(
                    1,
                    "Invalid API key, I guess? I don't know what you're trying to do.",
                )
            return {
                "images": [
                    image.as_dict() for image in self.user.images.order_by("-uploaded")
                ]
            }

    get.needs_auth = False  # type: ignore

    def post(self, request):
        assert self.user
        try:
            image = process_upload(
                request.FILES,
                self.user,
                title=request.POST.get("title"),
                expires_in=(
                    int(request.POST["expires_in"])
                    if request.POST.get("expires_in")
                    else None
                ),
            )
        except UploadError as e:
            return self._construct_error_response(3, str(e))
        else:
            return image.as_dict()

    def put(self, request, image_id=None):
        assert self.image
        try:
            self.image.set_title(self.json.get("title"))
        except ValueError as e:
            return self._construct_error_response(4, str(e))
        self.image.save()
        return self.image.as_dict()

    def delete(self, request, image_id=None):
        assert self.image
        self.image.delete()
        return {}
