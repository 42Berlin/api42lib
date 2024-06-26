import math
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from typing import Dict, Optional

import requests
import yaml
from tqdm import tqdm

from .Token import Token
from .utils import LOG, APIVersion, _detect_v3


class IntraAPIClient:
    verify_requests = True
    __instance = None

    def __new__(cls, *args, **kwargs):
        """
        Ensures that only one instance of IntraAPIClient is created (singleton pattern).

        Returns:
        - IntraAPIClient: The singleton instance of the IntraAPIClient class.
        """

        if cls.__instance is None:
            cls.__instance = super(IntraAPIClient, cls).__new__(cls)
        return cls.__instance

    def __init__(self, config_path: Optional[str] = None, progress_bar: bool = True) -> None:
        """
        Initializes the IntraAPIClient instance.

        This method initializes the IntraAPIClient with the given configuration path and progress bar option. If the instance
        has not been initialized before, it loads the configuration from the specified path or the default path, creates tokens
        for API versions V2 and V3, and marks the instance as initialized.

        Parameters:
        - config_path (Optional[str]): The path to the configuration file. If None, the default path 'config.yml' in the current
        working directory is used.
        - progress_bar (bool): A flag to enable or disable the progress bar during operations.

        Raises:
        - FileNotFoundError: If the specified configuration file does not exist.
        """
        if not hasattr(self, '__initialized'):
            config = self.__load_config(config_path)
            config_v2 = config.get("intra", {}).get("v2", {})
            config_v3 = config.get("intra", {}).get("v3", {})
            self.progress_bar = progress_bar
            self.token: Optional[Token] = None
            self.token_v2 = self.__create_token(config_v2, api_version=APIVersion.V2)
            self.token_v3 = self.__create_token(config_v3, api_version=APIVersion.V3)
            self.__initialized = True

    def __load_config(self, config_file: Optional[str] = None) -> Dict:
        """
        Loads the configuration from the specified file or the default file path.

        Parameters:
        - config_file (Optional[str]): The path to the configuration file. If None, the default path 'config.yml' in the current working directory is used.

        Returns:
        - Dict: The configuration dictionary.

        Raises:
        - FileNotFoundError: If the specified configuration file does not exist.
        - ValueError: If there is an error parsing the configuration file.
        """

        if not config_file:
            config_file = f"{os.environ.get('PWD', '')}/config.yml"
            LOG.debug(f"Using default config file: {config_file}")

        try:
            with open(config_file, "r") as cfg_stream:
                return yaml.load(cfg_stream, Loader=yaml.BaseLoader)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found: {config_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing config file: {e}")

    def __create_token(self, config: Dict, api_version: Optional[APIVersion] = None) -> Token:
        """
        Creates a Token instance based on the given configuration and API version.

        Parameters:
        - config (Dict): The configuration dictionary for the token version.
        - api_version (Optional[APIVersion]): The API version for the token (V2 or V3).

        Returns:
        - Token: The created Token instance.
        """

        return Token(
            client_id=config.get("client", None),
            client_secret=config.get("secret", None),
            token_url=config.get("uri", None),
            scopes=config.get("scopes", None),
            login=config.get("login", None),
            password=config.get("password", None),
            endpoint=config.get("endpoint", None),
            api_version=api_version,
        )

    def __add_auth_header(self, headers: Optional[Dict] = None) -> Dict:
        """
        Adds the authorization header with the current access token to the headers.

        Parameters:
        - headers (Optional[Dict]): The existing headers. If None, an empty dictionary is used.

        Returns:
        - Dict: The headers dictionary with the authorization header added.
        """

        if not headers:
            headers = {}
        headers["Authorization"] = f"Bearer {self.token.access_token}"
        return headers

    def __request(self, method: callable, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Makes an API request with the given method, URL, headers, and additional parameters.
        Handles token expiration, rate limits, and errors.

        Parameters:
        - method (callable): The HTTP method to use for the request (e.g., requests.get, requests.post).
        - url (str): The URL for the request.
        - headers (Optional[Dict]): The headers to include in the request.
        - kwargs: Additional keyword arguments to pass to the request method.

        Returns:
        - requests.Response: The response from the API request.

        Raises:
        - ValueError: If there is an error with the request (e.g., invalid URL, client/server error).
        """

        LOG.debug(f"=====> API {self.token.api_version.value} Request")
        if not self.token or not self.token.is_valid():
            self.token.request_token()

        tries = 0
        while True:
            LOG.debug(f"⏳ Attempting a {method.__name__.upper()} request to {url}")
            res = method(
                url,
                headers=self.__add_auth_header(headers),
                verify=self.verify_requests,
                **kwargs,
            )

            if res.status_code == 401:
                if tries < 5:
                    LOG.debug("💀 Token expired")
                    self.token.request_token()
                    tries += 1
                    continue
                else:
                    LOG.error("❌ Tried to renew token too many times, something's wrong")

            elif res.status_code == 404:
                raise ValueError(f"Invalid URL: {url}")

            elif res.status_code == 429:
                LOG.info(f"🚔 Rate limit exceeded - Waiting {res.headers['Retry-After']}s before requesting again")
                time.sleep(float(res.headers["Retry-After"]))
                continue

            if res.status_code >= 400:
                req_data = "{}{}".format(
                    url,
                    "\n" + str(kwargs["params"]) if "params" in kwargs.keys() else "",
                )
                error_origin = "Client" if res.status_code < 500 else "Server"
                raise ValueError(f"\n{res.headers}\n\n{error_origin}Error. Error {str(res.status_code)}\n{str(res.content)}\n{req_data}")

            LOG.debug(f"✅ Request returned with code {res.status_code}")
            return res

    @_detect_v3
    def get(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        return self.__request(requests.get, url, headers, **kwargs)

    @_detect_v3
    def post(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        return self.__request(requests.post, url, headers, **kwargs)

    @_detect_v3
    def patch(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        return self.__request(requests.patch, url, headers, **kwargs)

    @_detect_v3
    def put(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        return self.__request(requests.put, url, headers, **kwargs)

    @_detect_v3
    def delete(self, url: str, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        return self.__request(requests.delete, url, headers, **kwargs)

    def pages(self, url: str, headers: Optional[Dict] = None, **kwargs) -> list:
        """
        Fetches all pages of data sequentially from the specified URL.

        Parameters:
        - url (str): The URL from which to fetch the data.
        - headers (Optional[Dict]): Optional HTTP headers to send with the request.
        - kwargs: Additional keyword arguments to pass to the `get` method.

        Returns:
        - list: A list of items fetched from all the pages.
        """

        headers = headers or {}
        kwargs["params"] = kwargs.get("params", {}).copy()
        kwargs["params"]["page"] = int(kwargs["params"].get("page", 1))
        kwargs["params"]["per_page"] = kwargs["params"].get("per_page", 100)

        res = self.get(url=url, headers=headers, **kwargs)
        if self.token.api_version == APIVersion.V2:
            items = res.json()
            if "X-Total" not in res.headers:
                return items
            initial_page = int(res.headers.get("X-Page", 1))
            total_pages = math.ceil(int(res.headers.get("X-Total", 1)) / int(res.headers.get("X-Per-Page", 1)))
        elif self.token.api_version == APIVersion.V3:
            data = res.json()
            items = data.get("items", [])
            initial_page = data.get("page", 1)
            total_pages = data.get("pages", 1)

        for page in tqdm(
            range(initial_page + 1, total_pages + 1),
            initial=1,
            total=total_pages,
            desc=url,
            unit="page",
            disable=not self.progress_bar,
        ):
            LOG.debug(f"Fetching page: {page}/{total_pages}")
            kwargs["params"] = kwargs.get("params", {})
            kwargs["params"]["page"] = page
            data = self.get(url=url, headers=headers, **kwargs).json()
            if self.token.api_version == APIVersion.V2:
                items.extend(data)
            elif self.token.api_version == APIVersion.V3:
                items.extend(data.get("items", []))

        return items

    def pages_threaded(self, url: str, headers: Optional[Dict] = None, stop_page: Optional[int] = None, threads: int = 0, thread_timeout: int = 15, **kwargs) -> list:
        """
        Fetches pages of data concurrently using multiple threads.

        Parameters:
        - url (str): The URL from which to fetch the data.
        - headers (Optional[Dict]): Optional HTTP headers to send with the request.
        - stop_page (Optional[int]): The page number at which to stop fetching. If None, all pages will be fetched.
        - threads (int): The number of threads to use for concurrent requests. If <= 0, the method will calculate the number of threads based on the number of CPU cores.
        - thread_timeout (int): The maximum number of seconds to wait for each thread to complete.
        - kwargs: Additional keyword arguments to pass to the `get` method.

        Returns:
        - list: A list of items fetched from the pages.
        """

        headers = headers or {}
        kwargs["params"] = kwargs.get("params", {}).copy()
        kwargs["params"]["page"] = int(kwargs["params"].get("page", 1))
        kwargs["params"]["per_page"] = kwargs["params"].get("per_page", 100)

        def _page_thread(page: int) -> list:
            local_kwargs = deepcopy(kwargs)
            local_kwargs["params"]["page"] = page
            try:
                res = self.get(url=url, headers=headers, **local_kwargs)
                return res.json()
            except Exception as e:
                LOG.error(f"Error fetching page {page}: {e}")
                return []

        res = self.get(url=url, headers=headers, **kwargs)
        if self.token.api_version == APIVersion.V2:
            items = res.json()
            total_items = int(res.headers.get("X-Total", 0))
            per_page = int(res.headers.get("X-Per-Page", 30))
            total_pages = math.ceil(total_items / per_page)
        elif self.token.api_version == APIVersion.V3:
            data = res.json()
            total_pages = data.get("pages", 1)
            items = data.get("items", [])

        if stop_page:
            total_pages = min(total_pages, stop_page)

        if threads <= 0:
            threads = os.cpu_count() * 3

        LOG.debug(f"💻 Using {threads} threads")
        with tqdm(
            total=total_pages,
            initial=1,
            desc=url,
            unit="page",
            disable=not self.progress_bar,
        ) as pbar:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_page = {executor.submit(_page_thread, page): page for page in range(2, total_pages + 1)}

                for future in as_completed(future_to_page):
                    page = future_to_page[future]
                    try:
                        result = future.result(timeout=thread_timeout)
                        if self.token.api_version == APIVersion.V2:
                            items.extend(result)
                        elif self.token.api_version == APIVersion.V3:
                            items.extend(result.get("items", []))
                    except Exception as exc:
                        LOG.error(f"Page {page} generated an exception: {exc}")
                    pbar.update()

        return items

    def progress_bar_disable(self) -> None:
        """
        Disables the progress bar for operations.
        """

        self.progress_bar = False

    def progress_bar_enable(self) -> None:
        """
        Enables the progress bar for operations.
        """

        self.progress_bar = True
