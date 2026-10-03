import os
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment variables from the .env file.
load_dotenv()

TAVILY_URL = "https://api.tavily.com/search"


# Search for useful learning resources related to a topic.
def search_learning_resources(
    topic: str,
    daily_focus: str | None = None,
    max_results: int = 5,
) -> list[dict[str, Any]]:

    api_key = os.getenv("TAVILY_API_KEY", "").strip()

    if not api_key or not topic.strip():
        return []

    try:
        query = (
            f"{topic} {daily_focus or ''} "
            "official documentation tutorial learning examples"
        ).strip()

        response = httpx.post(
            TAVILY_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            },
            timeout=20.0,
        )

        response.raise_for_status()

        data = response.json()

    except Exception as exc:
        print(f"Tavily search failed: {exc}")
        return []

    resources = []

    # Extract useful resource details from the search results.
    for item in data.get("results", []):
        title = item.get("title")
        url = item.get("url")
        content = item.get("content") or ""

        if not title or not url:
            continue

        resources.append(
            {
                "title": str(title),
                "url": str(url),
                "description": str(content)[:400],
            }
        )

    return resources