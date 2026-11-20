"""Pencari prospek UMKM lokal otomatis gratis menggunakan OpenStreetMap (Nominatim)."""

from __future__ import annotations

import math
import time
from typing import Any

import httpx
from pydantic import BaseModel

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
_DEFAULT_HEADERS = {
    "User-Agent": "DennMikiMultiAgent/1.0 (local-umkm-lead-finder)",
    "Accept-Language": "id,en;q=0.8",
}

_EXCLUDED_CATEGORIES = {
    "highway",
    "boundary",
    "place",
    "waterway",
    "natural",
    "railway",
    "landuse",
    "aeroway",
}

# Daftar jaringan/franchise nasional & global umum agar hasil fokus ke UMKM lokal.
_BIG_CHAIN_KEYWORDS = (
    "starbucks",
    "kopi kenangan",
    "janji jiwa",
    "fore coffee",
    "point coffee",
    "tuku",
    "tomoro coffee",
    "mixue",
    "chatime",
    "indomaret",
    "alfamart",
    "alfamidi",
    "mcdonald",
    "kfc",
    "burger king",
    "pizza hut",
    "domino",
    "hokben",
    "solaria",
    "j.co",
    "dunkin",
    "richeese factory",
    "mie gacoan",
    "guardian",
    "watsons",
    "miniso",
)


class LeadDiscoveryError(RuntimeError):
    """Dilempar ketika pencarian prospek UMKM otomatis gagal."""


class DiscoveredLead(BaseModel):
    """Satu kandidat prospek UMKM yang ditemukan dari peta OpenStreetMap."""

    nama_usaha: str
    kategori: str
    kota: str
    alamat: str = ""
    kontak: str = ""
    saluran: str = "whatsapp"
    punya_website: bool = False
    website_url: str = ""
    catatan: str = ""
    sumber_url: str = ""


def _is_big_chain(name: str) -> bool:
    lowered = name.casefold()
    return any(chain in lowered for chain in _BIG_CHAIN_KEYWORDS)


def _extract_contact(extratags: dict[str, Any]) -> tuple[str, str]:
    whatsapp = (extratags.get("contact:whatsapp") or "").strip()
    if whatsapp:
        return whatsapp, "whatsapp"

    phone = (extratags.get("phone") or extratags.get("contact:phone") or "").strip()
    if phone:
        return phone, "whatsapp"

    instagram = (
        extratags.get("contact:instagram") or extratags.get("instagram") or ""
    ).strip()
    if instagram:
        return instagram, "instagram"

    email = (extratags.get("email") or extratags.get("contact:email") or "").strip()
    if email:
        return email, "email"

    return "", "whatsapp"


def _build_address(address: dict[str, Any]) -> str:
    parts: list[str] = []
    road = (address.get("road") or "").strip()
    house = (address.get("house_number") or "").strip()
    if road:
        parts.append(f"{road} No. {house}" if house else road)

    for key in ("neighbourhood", "suburb", "village", "city_district", "town", "city"):
        val = (address.get(key) or "").strip()
        if val and val not in parts:
            parts.append(val)
    return ", ".join(parts[:4])


def _osm_url(item: dict[str, Any]) -> str:
    osm_type = (item.get("osm_type") or "").strip().lower()
    osm_id = item.get("osm_id")
    if osm_type in ("node", "way", "relation") and osm_id:
        return f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
    return ""


def parse_nominatim_places(
    raw_places: list[dict[str, Any]],
    default_city: str,
    default_category: str,
    only_without_website: bool = True,
    exclude_chains: bool = True,
    limit: int = 10,
) -> list[DiscoveredLead]:
    """Memfilter dan mem-parsing daftar hasil POI Nominatim menjadi kandidat prospek UMKM."""
    if limit <= 0:
        return []

    results: list[DiscoveredLead] = []
    seen_names: set[str] = set()

    for item in raw_places:
        category_cls = (item.get("category") or item.get("class") or "").strip().lower()
        if category_cls in _EXCLUDED_CATEGORIES:
            continue

        name = (item.get("name") or "").strip()
        if not name:
            display = (item.get("display_name") or "").strip()
            name = display.split(",")[0].strip() if display else ""
        if not name:
            continue

        norm_name = name.casefold()
        if norm_name in seen_names:
            continue
        if exclude_chains and _is_big_chain(name):
            continue

        extratags = item.get("extratags") or {}
        website_url = (
            extratags.get("website")
            or extratags.get("contact:website")
            or extratags.get("url")
            or ""
        ).strip()
        has_website = bool(website_url)
        if only_without_website and has_website:
            continue

        seen_names.add(norm_name)
        address = item.get("address") or {}
        alamat = _build_address(address)
        kota = (
            (address.get("city") or address.get("town") or address.get("county") or default_city)
            .strip()
        )
        poi_type = (item.get("type") or "").replace("_", " ").strip()
        kategori = default_category.strip().title() if default_category.strip() else (poi_type.title() or "UMKM")

        kontak, saluran = _extract_contact(extratags)
        sumber_url = _osm_url(item)

        note_parts: list[str] = ["Sumber: OpenStreetMap"]
        if alamat:
            note_parts.append(f"Alamat: {alamat}")
        opening_hours = (extratags.get("opening_hours") or "").strip()
        if opening_hours:
            note_parts.append(f"Jam buka: {opening_hours}")
        if not has_website:
            note_parts.append("Belum tercantum website di OSM")
        if not kontak:
            note_parts.append("Kontak WA/IG belum terisi di OSM (cek Google Maps/IG)")
        if sumber_url:
            note_parts.append(f"Peta: {sumber_url}")

        results.append(
            DiscoveredLead(
                nama_usaha=name,
                kategori=kategori,
                kota=kota,
                alamat=alamat,
                kontak=kontak,
                saluran=saluran,
                punya_website=has_website,
                website_url=website_url,
                catatan=" | ".join(note_parts),
                sumber_url=sumber_url,
            )
        )

        if len(results) >= limit:
            break

    return results


def discover_umkm_leads(
    keyword: str,
    city: str,
    radius_km: float = 5.0,
    limit: int = 10,
    only_without_website: bool = True,
    exclude_chains: bool = True,
    timeout: float = 15.0,
) -> list[DiscoveredLead]:
    """Mencari kandidat UMKM lokal otomatis berdasarkan kata kunci & kota via OpenStreetMap."""
    cleaned_keyword = keyword.strip()
    cleaned_city = city.strip()
    if not cleaned_keyword:
        raise LeadDiscoveryError("Kata kunci jenis usaha (--keyword) tidak boleh kosong.")
    if not cleaned_city:
        raise LeadDiscoveryError("Nama kota/daerah (--city) tidak boleh kosong.")

    radius = max(1.0, min(25.0, radius_km))
    geo_query = cleaned_city if "indonesia" in cleaned_city.lower() else f"{cleaned_city}, Indonesia"

    try:
        geo_resp = httpx.get(
            NOMINATIM_SEARCH_URL,
            params={"q": geo_query, "format": "jsonv2", "limit": 1},
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LeadDiscoveryError(
            f"Gagal mencari koordinat kota '{cleaned_city}' di OpenStreetMap: {exc}"
        ) from exc

    if not geo_data:
        raise LeadDiscoveryError(
            f"Lokasi '{cleaned_city}' tidak ditemukan di OpenStreetMap. Coba tulis nama kota/kecamatan yang lebih umum."
        )

    lat = float(geo_data[0]["lat"])
    lon = float(geo_data[0]["lon"])
    delta_lat = radius / 111.0
    delta_lon = radius / (111.0 * max(0.2, math.cos(math.radians(lat))))
    south, north = lat - delta_lat, lat + delta_lat
    west, east = lon - delta_lon, lon + delta_lon

    # Hormati batas 1 request/detik Nominatim agar tidak terkena rate limit.
    time.sleep(1.05)

    fetch_limit = min(40, max(limit * 3, 15))
    try:
        poi_resp = httpx.get(
            NOMINATIM_SEARCH_URL,
            params={
                "q": cleaned_keyword,
                "format": "jsonv2",
                "viewbox": f"{west},{north},{east},{south}",
                "bounded": 1,
                "extratags": 1,
                "addressdetails": 1,
                "limit": fetch_limit,
            },
            headers=_DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )
        poi_resp.raise_for_status()
        poi_data = poi_resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LeadDiscoveryError(
            f"Gagal mencari prospek '{cleaned_keyword}' di sekitar {cleaned_city}: {exc}"
        ) from exc

    return parse_nominatim_places(
        raw_places=poi_data if isinstance(poi_data, list) else [],
        default_city=cleaned_city,
        default_category=cleaned_keyword,
        only_without_website=only_without_website,
        exclude_chains=exclude_chains,
        limit=limit,
    )
