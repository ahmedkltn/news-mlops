"""Same-origin image proxy.

Some sources (e.g. lapresse.tn) serve a "forbidden" placeholder to
cross-site browser image requests (WAF keys on Sec-Fetch-Site / Referer).
Proxying the image through our own origin — with a same-site Referer and no
Sec-Fetch headers — makes the browser load a same-origin URL and gets the
real image. SSRF-guarded: http(s) only, public hosts only, image/* only.
"""
import ipaddress
import logging
import socket
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, HTTPException, Query, Response

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_BYTES = 8 * 1024 * 1024  # 8 MB cap
TIMEOUT = 8


def _is_public_host(host: str) -> bool:
    """Block loopback/private/link-local/reserved targets (SSRF guard)."""
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                return False
        return True
    except Exception:
        return False


@router.get("")
def proxy_image(url: str = Query(..., min_length=8, max_length=2048)):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(400, "Invalid image URL")
    if not _is_public_host(parsed.hostname):
        raise HTTPException(400, "Host not allowed")

    origin = f"{parsed.scheme}://{parsed.hostname}/"
    headers = {
        "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
        "Referer": origin,  # satisfy hotlink protection
    }
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT, stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.info(f"img proxy failed for {url[:80]}: {e}")
        raise HTTPException(502, "Upstream fetch failed")

    ctype = resp.headers.get("Content-Type", "")
    if not ctype.startswith("image/"):
        resp.close()
        raise HTTPException(415, "Not an image")

    chunks, total = [], 0
    for chunk in resp.iter_content(64 * 1024):
        total += len(chunk)
        if total > MAX_BYTES:
            resp.close()
            raise HTTPException(413, "Image too large")
        chunks.append(chunk)
    resp.close()

    return Response(
        content=b"".join(chunks),
        media_type=ctype,
        headers={"Cache-Control": "public, max-age=86400"},
    )
