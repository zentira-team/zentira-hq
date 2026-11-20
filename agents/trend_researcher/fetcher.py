"""Pengambil dan parser feed RSS Google Trends Indonesia."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx
from pydantic import BaseModel, Field

GOOGLE_TRENDS_RSS_URL = "https://trends.google.com/trending/rss"
_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DennMikiMultiAgent/1.0)",
}


class TrendFetchError(RuntimeError):
    """Dilempar ketika gagal mengambil atau mem-parsing feed Google Trends RSS."""


class NewsSnippet(BaseModel):
    """Ringkasan berita pendukung yang menempel pada satu item tren."""

    title: str
    source: str = ""
    snippet: str = ""
    url: str = ""


class TrendItem(BaseModel):
    """Satu topik tren dari Google Trends RSS."""

    title: str
    approx_traffic: str = ""
    pub_date: str = ""
    news_items: list[NewsSnippet] = Field(default_factory=list)


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(parent: ET.Element, local_name: str) -> str:
    for child in parent:
        if _local_tag(child.tag) == local_name:
            return (child.text or "").strip()
    return ""


def _children_by_local(parent: ET.Element, local_name: str) -> list[ET.Element]:
    return [child for child in parent if _local_tag(child.tag) == local_name]


def parse_trends_rss(xml_content: str, max_items: int = 20) -> list[TrendItem]:
    """Mem-parsing XML Google Trends RSS menjadi daftar TrendItem unik."""
    if not xml_content or not xml_content.strip():
        raise TrendFetchError("Konten XML Google Trends RSS kosong.")

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise TrendFetchError(f"Format XML Google Trends RSS tidak valid: {exc}") from exc

    if max_items <= 0:
        return []

    trends: list[TrendItem] = []
    seen_titles: set[str] = set()

    for item_el in root.iter():
        if _local_tag(item_el.tag) != "item":
            continue

        title = _child_text(item_el, "title")
        normalized_title = title.casefold()
        if not title or normalized_title in seen_titles:
            continue
        seen_titles.add(normalized_title)

        news_snippets: list[NewsSnippet] = []
        for news_el in _children_by_local(item_el, "news_item")[:3]:
            news_title = _child_text(news_el, "news_item_title")
            if not news_title:
                continue
            news_snippets.append(
                NewsSnippet(
                    title=news_title,
                    source=_child_text(news_el, "news_item_source"),
                    snippet=_child_text(news_el, "news_item_snippet"),
                    url=_child_text(news_el, "news_item_url"),
                )
            )

        trends.append(
            TrendItem(
                title=title,
                approx_traffic=_child_text(item_el, "approx_traffic"),
                pub_date=_child_text(item_el, "pubDate"),
                news_items=news_snippets,
            )
        )

        if len(trends) >= max_items:
            break

    return trends


def fetch_google_trends(
    geo: str = "ID",
    max_items: int = 20,
    timeout: float = 15.0,
) -> list[TrendItem]:
    """Mengambil tren terbaru dari feed RSS gratis Google Trends."""
    try:
        response = httpx.get(
            GOOGLE_TRENDS_RSS_URL,
            params={"geo": geo.upper()},
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise TrendFetchError(
            f"Gagal mengambil Google Trends RSS (geo={geo}): {exc}"
        ) from exc

    return parse_trends_rss(response.text, max_items=max_items)
