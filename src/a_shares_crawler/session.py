import json
from pathlib import Path
from typing import Any

import requests

REQUEST_HEADERS: dict[str, str] = {}
REQUEST_COOKIES: dict[str, str] = {}
REQUEST_PARAMS: dict[str, Any] = {}

DEFAULT_CONFIG_PATH = Path("config.json")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> None:
    """Loads request configuration from a JSON file.

    The JSON file should contain `headers`, `cookies`, and `params` keys.
    See `config.example.json` for the expected format.

    Parameters
    ----------
    path
        Path to the JSON configuration file.
    """
    with open(path) as f:
        config = json.load(f)

    REQUEST_HEADERS.update(config.get("headers", {}))
    REQUEST_COOKIES.update(config.get("cookies", {}))
    REQUEST_PARAMS.update(config.get("params", {}))


def create_session() -> requests.Session:
    """Creates a requests session with configured headers and cookies."""
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)
    session.cookies.update(REQUEST_COOKIES)
    return session
