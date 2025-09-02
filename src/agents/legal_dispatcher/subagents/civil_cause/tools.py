import os

import httpx

from bs4 import BeautifulSoup


async def fetch_civil_law() -> str:
    """Returns the civil law of Brazil"""

    url = os.environ.get("CIVIL_LAW_URL")
    httpx_headers = httpx.Headers(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
            )
        }
    )
    httpx_timeout = httpx.Timeout(30.0, connect=5.0)
    with httpx.Client(
        headers=httpx_headers,
        timeout=httpx_timeout
    ) as httpx_client:
        response = httpx_client.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        text_content = soup.get_text()

        parsed_contents = []
        for chunk in text_content.splitlines():
            chunk = chunk.strip()
            if not chunk:
                continue

            parsed_contents.append(chunk)

    final_content = "\n".join(parsed_contents)

    return final_content
