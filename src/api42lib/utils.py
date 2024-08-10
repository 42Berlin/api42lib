import logging
import re
from enum import Enum
from typing import Dict, Optional

REGEX_URL_V2 = r"^(https:\/\/api\.intra\.42\.fr|^(?!\/?v3\/|\/?freeze|\/?pace-system))(?!\/?v3\/|\/?freeze|\/?pace-system)(\/?(?:[a-zA-Z0-9_-]+\/?)*)$"
REGEX_URL_V3 = r"^(\/?(v3\/)?(freeze|pace-system)\/(v\d)\/([\w\-\/]*))$"


logger = logging.getLogger(__name__)


class APIVersion(Enum):
    V2 = "v2"
    V3 = "v3"


def _detect_v3(func) -> callable:
    """
    A decorator function that detects the API version based on the URL pattern and sets the appropriate token.

    Parameters:
    - func (callable): The function to be wrapped by the decorator.

    Returns:
    - callable: The wrapped function with API version detection logic.
    """

    def wrapper(self, url: str, headers: Optional[Dict] = None, **kwargs) -> callable:
        headers = headers or {}
        url = url.strip()
        logger.debug("======================================")
        if re.match(REGEX_URL_V2, url):
            self.token = self.token_v2
            api_route = url.replace(self.token.endpoint, "").lstrip("/").lstrip("v2/")
            url = f"{self.token.endpoint}/{api_route}"
        else:
            self.token = self.token_v3
            if match := re.match(REGEX_URL_V3, url):
                url = f"https://{match.group(3)}.42.fr/api/{match.group(4)}/{match.group(5)}"
            logger.debug(f"Using {APIVersion.V3.value} token")
        return func(self, url, headers, **kwargs)

    return wrapper
