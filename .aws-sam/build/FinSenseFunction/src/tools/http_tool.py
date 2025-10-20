import requests
from typing import Optional

def fetch(url: str, timeout: Optional[float] = 10.0) -> str:
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text
