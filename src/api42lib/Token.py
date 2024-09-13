import logging
from base64 import b64encode
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import requests

from .utils import APIVersion

logger = logging.getLogger(__name__)


@dataclass
class Token:
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token_url: Optional[str] = None
    endpoint: Optional[str] = None
    scopes: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    otp: Optional[str] = None
    api_version: Optional[APIVersion] = None
    is_v3: bool = False
    access_token: Optional[str] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    refresh_expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None

    def __post_init__(self) -> None:
        self.is_v3 = self.api_version == APIVersion.V3

    def __set_token(self, res: Dict) -> None:
        """
        Sets the token attributes based on the response from the token request.

        Parameters:
        - res (Dict): The response dictionary containing token information.
        """

        now_utc = datetime.now(timezone.utc)
        self.access_token = res.get("access_token", self.access_token)
        self.created_at = now_utc
        self.expires_in = int(res.get("expires_in", 0))
        self.otp = res.get("otp", self.otp)
        self.expires_at = self.created_at + timedelta(seconds=self.expires_in)
        self.refresh_token = res.get("refresh_token", self.refresh_token)
        self.refresh_expires_in = int(res.get("refresh_expires_in", 0))
        self.refresh_expires_at = now_utc + timedelta(seconds=self.refresh_expires_in)

    def __set_payload_v2(self) -> Dict:
        """
        Creates the payload for the V2 token request.

        Returns:
        - Dict: The payload dictionary for the V2 token request.
        """

        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": self.scopes,
        }

    def __set_payload_v3(self) -> Dict:
        """
        Creates the payload for the V3 token request, handling refresh token logic.

        Returns:
        - Dict: The payload dictionary for the V3 token request.
        """

        is_refresheable = self.refresh_token and self.refresh_expires_at > datetime.now(
            timezone.utc
        )
        if is_refresheable:
            return {"grant_type": "refresh_token", "refresh_token": self.refresh_token}
        return {
            "grant_type": "password",
            "username": self.login,
            "password": self.password,
            **({"otp": self.otp} if self.otp else {}),
        }

    def is_valid(self) -> bool:
        """
        Checks if the current token is valid (not expired).

        Returns:
        - bool: True if the token is valid, False otherwise.
        """

        if self.access_token is None or self.expires_at is None:
            logger.debug("⏳ No valid token found. Fetching new one")
            return False
        if self.expires_at < datetime.now(timezone.utc):
            logger.debug(f"💀 Token {self.api_version.value} expired. Fetching new one")
            return False
        return True

    def request_token(self) -> None:
        """
        Requests a new token from the token URL based on the API version.
        Sets the token attributes based on the response.
        """

        payload = self.__set_payload_v3() if self.is_v3 else self.__set_payload_v2()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": b"Basic "
            + b64encode(
                bytes(self.client_id + ":" + self.client_secret, encoding="utf-8")
            ),
        }

        logger.debug(f"⏳ Attempting to get a {self.api_version.value} token")
        res = requests.post(self.token_url, headers=headers, data=payload)
        if res.status_code == 401:
            raise Exception(
                f"Probably invalid client_id, client_secret or OTP code: {res.text}"
            )
        elif res.status_code != 200:
            raise Exception(f"Error while fetching token: {res.text}")

        try:
            data = res.json()
        except Exception as e:
            raise Exception(f"Error while parsing token response: {e}")

        self.__set_token(data)
        logger.debug(
            f"🔑 Got {self.api_version.value} token -> '{self.access_token:10.10}...'"
        )
