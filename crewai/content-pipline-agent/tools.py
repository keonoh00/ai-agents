import os
import re
from typing import Dict, List

from crewai.tools import tool
from dotenv import load_dotenv
from firecrawl import Firecrawl
from firecrawl.v2.types import Document, ScrapeOptions, SearchData

load_dotenv()


@tool
def web_search_tool(query: str) -> List[Dict[str, str]]:
    """
    Web Search Tool

    Args:
      query: The query to search the web for.

    Returns:
      A list of search results with the website content in markdown format.
    """

    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        return []
    app = Firecrawl(api_key=api_key)

    response: SearchData = app.search(
        query=query,
        limit=5,
        scrape_options=ScrapeOptions(
            formats=["markdown"],
        ),
    )

    cleaned_chunks: List[Dict[str, str]] = []

    if not response.web:
        return []

    for result in response.web:
        if isinstance(result, Document):
            metadata = result.metadata_typed
            title = metadata.title or ""
            url = metadata.source_url or metadata.url or ""
            markdown = result.markdown or ""

            cleaned = re.sub(r"\\+|\n+", "", markdown).strip()
            cleaned = re.sub(r"\[[^\]]+\]\([^\)]+\)|https?://[^\s]+", "", cleaned)

            cleaned_chunks.append(
                {
                    "title": title,
                    "url": url,
                    "markdown": cleaned,
                }
            )

    return cleaned_chunks
