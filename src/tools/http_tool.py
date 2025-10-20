# PURPOSE: Simple helper function to fetch text content from a URL.
# CONTEXT: Used when retrieving external data or configuration files in FinSense.
# CREDITS: Original work — no external code reuse.

import requests
from typing import Optional

def fetch(url: str, timeout: Optional[float] = 10.0) -> str:
    """
    Download text content from a given URL.

    parameters:
    - url: str – full URL to request.
    - timeout: float (optional) – max seconds to wait for response (default: 10).

    returns:
    - str – response body as plain text.

    raises:
    - requests.exceptions.RequestException – if the HTTP request fails.
    """
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()  # Ensures HTTP errors raise exceptions instead of returning bad data.
    return r.text
