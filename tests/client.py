import base64

from django.http import HttpResponse
from django.test.client import Client
from django.test.client import MULTIPART_CONTENT


class APIClient(Client):
    def __init__(self, *args, **kwargs) -> None:
        self.api_key = kwargs.pop("api_key")
        super().__init__(*args, **kwargs)

    def _add_auth_header(self, extra_dict) -> HttpResponse:
        extras = extra_dict.copy()
        data = f":{self.api_key}"
        credentials = base64.b64encode(data.encode("utf-8")).strip()
        auth_string = f'Basic {credentials.decode("utf-8")}'
        extras.setdefault("HTTP_AUTHORIZATION", auth_string)
        return extras

    def delete(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        secure=False,
        **extra,
    ) -> HttpResponse:
        return super().delete(
            path,
            data=data,
            content_type=content_type,
            secure=secure,
            **self._add_auth_header(extra),
        )

    def get(self, path, data=None, secure=False, **extra) -> HttpResponse:
        return super().get(
            path, data=data, secure=secure, **self._add_auth_header(extra)
        )

    def post(
        self, path, data=None, content_type=MULTIPART_CONTENT, secure=False, **extra
    ) -> HttpResponse:
        return super().post(
            path,
            data=data,
            content_type=content_type,
            secure=secure,
            **self._add_auth_header(extra),
        )

    def put(
        self,
        path,
        data="",
        content_type="application/octet-stream",
        follow=False,
        secure=False,
        **extra,
    ) -> HttpResponse:
        return super().put(
            path,
            data=data,
            content_type=content_type,
            follow=follow,
            secure=secure,
            **self._add_auth_header(extra),
        )
