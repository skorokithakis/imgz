import json
from typing import Any

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

    def dispatch(self, *args, **kwargs):
        if self.request.method != "POST":
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

        self.user = None
        assert self.request.method
        handler = getattr(self, self.request.method.lower(), None)
        if getattr(handler, "needs_auth", True):
            self.user = User.objects.filter(
                api_key=self.request.GET.get("api_key")
            ).first()
            if not self.user:
                return self._construct_error_response(
                    1,
                    "Invalid API key, I guess? I don't know what you're trying to do.",
                )

            assert self.image
            if getattr(self, "image", None) and self.image.user != self.user:
                return self._construct_error_response(
                    2, "That's not your image, quit playing."
                )

        data = super().dispatch(*args, **kwargs)

        if isinstance(data, JsonResponse):
            return data

        return JsonResponse(data, json_dumps_params={"indent": 2, "sort_keys": True})


class ImageView(APIView):
    def get(self, request, image_id=None):
        assert self.image
        return JsonResponse(
            self.image.as_dict(), json_dumps_params={"indent": 2, "sort_keys": True}
        )

    get.needs_auth = False  # type: ignore

    def post(self, request):
        assert self.user
        try:
            image = process_upload(
                request.FILES, self.user, title=request.POST.get("title")
            )
        except UploadError as e:
            return self._construct_error_response(3, str(e))
        else:
            return image.as_dict()

    def put(self, request, image_id=None):
        assert self.image
        if not self.json.get("title"):
            return self._construct_error_response(
                4, "You didn't specify a title. Typical."
            )
        self.image.title = self.json["title"]
        self.image.save()
        return self.image.as_dict()

    def delete(self, request, image_id=None):
        assert self.image
        self.image.delete()
        return {}
