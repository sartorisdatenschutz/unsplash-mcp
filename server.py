# -*- coding: utf-8 -*-
"""Unsplash MCP Server with local stdio and remote HTTP transport support."""

import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Union

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

UNSPLASH_API_BASE = "https://api.unsplash.com"
mcp = FastMCP("Unsplash MCP Server")


@dataclass
class UnsplashPhoto:
    """Represents an Unsplash photo with full attribution data."""

    id: str
    description: Optional[str]
    alt_description: Optional[str]
    urls: Dict[str, str]
    width: int
    height: int
    color: str
    blur_hash: Optional[str]
    photographer_name: str
    photographer_username: str
    photographer_url: str
    photo_url: str
    attribution_text: str
    attribution_html: str


def _get_access_key() -> str:
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not access_key:
        raise ValueError(
            "Missing UNSPLASH_ACCESS_KEY environment variable. "
            "Get your key from https://unsplash.com/developers"
        )
    return access_key


def _get_headers() -> Dict[str, str]:
    return {
        "Accept-Version": "v1",
        "Authorization": f"Client-ID {_get_access_key()}",
    }


def _photo_to_dataclass(photo: dict) -> UnsplashPhoto:
    user = photo["user"]
    photographer_name = user.get("name", user["username"])
    photographer_username = user["username"]
    photographer_url = (
        f"https://unsplash.com/@{photographer_username}"
        "?utm_source=mcp_server&utm_medium=referral"
    )
    separator = "&" if "?" in photo["links"]["html"] else "?"
    photo_url = (
        photo["links"]["html"]
        + separator
        + "utm_source=mcp_server&utm_medium=referral"
    )
    attribution_text = f"Photo by {photographer_name} on Unsplash"
    attribution_html = (
        f'Photo by <a href="{photographer_url}">{photographer_name}</a> '
        'on <a href="https://unsplash.com/?utm_source=mcp_server&utm_medium=referral">'
        "Unsplash</a>"
    )

    return UnsplashPhoto(
        id=photo["id"],
        description=photo.get("description"),
        alt_description=photo.get("alt_description"),
        urls=photo["urls"],
        width=photo["width"],
        height=photo["height"],
        color=photo.get("color", "#000000"),
        blur_hash=photo.get("blur_hash"),
        photographer_name=photographer_name,
        photographer_username=photographer_username,
        photographer_url=photographer_url,
        photo_url=photo_url,
        attribution_text=attribution_text,
        attribution_html=attribution_html,
    )


@mcp.tool()
async def search_photos(
    query: str,
    page: Union[int, str] = 1,
    per_page: Union[int, str] = 10,
    order_by: str = "relevant",
    color: Optional[str] = None,
    orientation: Optional[str] = None,
    content_filter: str = "low",
) -> List[UnsplashPhoto]:
    """Search Unsplash photos and return image URLs plus attribution data."""
    try:
        page_int = int(page)
    except (ValueError, TypeError):
        page_int = 1

    try:
        per_page_int = int(per_page)
    except (ValueError, TypeError):
        per_page_int = 10

    params = {
        "query": query,
        "page": max(1, page_int),
        "per_page": min(max(1, per_page_int), 30),
        "order_by": order_by,
        "content_filter": content_filter,
    }
    if color:
        params["color"] = color
    if orientation:
        params["orientation"] = orientation

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{UNSPLASH_API_BASE}/search/photos",
                params=params,
                headers=_get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return [_photo_to_dataclass(photo) for photo in response.json()["results"]]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ValueError("Invalid Unsplash API key. Check UNSPLASH_ACCESS_KEY.") from exc
        if exc.response.status_code == 403:
            raise ValueError("Unsplash rate limit exceeded.") from exc
        raise ValueError(
            f"Unsplash API error: {exc.response.status_code} - {exc.response.text}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ValueError("Request timed out. Please try again.") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to search photos: {exc}") from exc


@mcp.tool()
async def get_random_photos(
    query: Optional[str] = None,
    count: Union[int, str] = 1,
    orientation: Optional[str] = None,
    content_filter: str = "low",
) -> List[UnsplashPhoto]:
    """Get random Unsplash photos, optionally filtered by keyword."""
    try:
        count_int = int(count)
    except (ValueError, TypeError):
        count_int = 1
    count_int = min(max(1, count_int), 30)

    params = {"count": count_int, "content_filter": content_filter}
    if query:
        params["query"] = query
    if orientation:
        params["orientation"] = orientation

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{UNSPLASH_API_BASE}/photos/random",
                params=params,
                headers=_get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            photos = data if isinstance(data, list) else [data]
            return [_photo_to_dataclass(photo) for photo in photos]
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ValueError("Invalid Unsplash API key. Check UNSPLASH_ACCESS_KEY.") from exc
        if exc.response.status_code == 403:
            raise ValueError("Unsplash rate limit exceeded.") from exc
        raise ValueError(
            f"Unsplash API error: {exc.response.status_code} - {exc.response.text}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ValueError("Request timed out. Please try again.") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to get random photos: {exc}") from exc


@mcp.tool()
async def track_download(photo_id: str) -> str:
    """Trigger Unsplash's download tracking endpoint and return its download URL."""
    if not photo_id or not photo_id.strip():
        raise ValueError("photo_id is required")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{UNSPLASH_API_BASE}/photos/{photo_id}/download",
                headers=_get_headers(),
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json().get("url", "")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 401:
            raise ValueError("Invalid Unsplash API key. Check UNSPLASH_ACCESS_KEY.") from exc
        if exc.response.status_code == 404:
            raise ValueError(f"Photo not found: {photo_id}") from exc
        if exc.response.status_code == 403:
            raise ValueError("Unsplash rate limit exceeded.") from exc
        raise ValueError(
            f"Unsplash API error: {exc.response.status_code} - {exc.response.text}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise ValueError("Request timed out. Please try again.") from exc
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Failed to track download: {exc}") from exc


def run_server() -> None:
    """Run stdio locally or Streamable HTTP in Docker/remote deployments."""
    transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()

    if transport in {"http", "streamable-http"}:
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="http", host=host, port=port)
        return

    if transport != "stdio":
        raise ValueError("MCP_TRANSPORT must be 'stdio', 'http', or 'streamable-http'.")

    mcp.run()


if __name__ == "__main__":
    run_server()
