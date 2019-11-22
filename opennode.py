import hashlib
import hmac
import random
import string
from decimal import Decimal
from typing import Any
from typing import Optional

import requests


class OpenNode:
    def __init__(
        self,
        api_key: str,
        callback_url: str = "",
        success_url: str = "",
        dev: bool = False,
    ):
        self._api_key = api_key
        self._dev = dev
        self._callback_url = callback_url
        self._success_url = success_url

    def get_url(self, url: str) -> str:
        base = (
            "https://dev-api.opennode.co/v1/%s"
            if self._dev
            else "https://api.opennode.co/v1/%s"
        )
        return base % url

    def get_invoice(
        self,
        amount: Decimal,
        currency: str,
        description: str,
        customer_name: str,
        customer_email: str,
        order_id: Optional[str] = None,
        auto_settle: bool = False,
    ) -> Any:
        """
        Generate a new invoice for the given data.
        """
        if order_id is None:
            order_id = "".join(
                random.choice(string.ascii_letters + string.digits) for _ in range(16)
            )
        r = requests.post(
            self.get_url("charges"),
            headers={"Authorization": self._api_key},
            json={
                "description": description,
                "amount": str(amount),
                "currency": currency,
                "order_id": order_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "callback_url": self._callback_url,
                "success_url": self._success_url,
                "auto_settle": auto_settle,
            },
        )
        data = r.json()["data"]
        data["invoice_url"] = (
            "https://dev-checkout.opennode.co/"
            if self._dev
            else "https://checkout.opennode.co/"
        ) + data["id"]
        return data

    def verify_data(self, order_id: str, signature: str) -> bool:
        """
        Verify that a webhook's signature is correct for the given order_id.
        """
        return (
            hmac.new(
                self._api_key.encode("utf8"),
                msg=order_id.encode("utf8"),
                digestmod=hashlib.sha256,
            ).hexdigest()
            == signature
        )
