import logging
import re

import httpx

_T_PATTERNS = (
    r'<input\s+type="hidden"\s+name="t"\s+id="t"\s+value="([^"]+)"\s*/?>',
    r'name="t"[^>]*value="([^"]+)"',
    r'id="t"[^>]*value="([^"]+)"',
    r'value="([^"]+)"[^>]*name="t"',
    r'name=\\"t\\"[^>]*value=\\"([^\\"]+)\\"',
    r'value="(GAA[A-Za-z0-9+/=]{40,})"',
)

_URLS = (
    (
        "https://login.live.com/login.srf?wa=wsignin1.0&rpsnv=21"
        "&ct=1708978285&rver=7.5.2211.0&wp=SA_20MIN"
        "&wreply=https%3a%2f%2faccount.live.com%2fproofs%2fAdd%3fapt%3d2"
        "&lc=1033&id=38936&mkt=en-US"
    ),
    (
        "https://login.live.com/login.srf?wa=wsignin1.0"
        "&wreply=https%3a%2f%2faccount.live.com%2f"
        "&rver=7.5.2211.0&wp=MBI_SSL_SHARED&lc=1033&id=38936"
    ),
)


def _extract_t(html: str) -> str | None:
    for pat in _T_PATTERNS:
        match = re.search(pat, html or "", re.I)
        if match:
            return match.group(1)
    return None


async def get_t(session: httpx.AsyncClient) -> str | None:
    """Scrape the login ``t`` token used by get_amrp / proofs Add handshake.

    Already-signed-in / passwordless sessions often 302 through interrupt
    pages instead of serving the classic hidden ``t`` on the first hop.
    Follow redirects and try a second wsignin if the first page is i5600.
    """
    last_html = ""
    last_status = None
    for url in _URLS:
        try:
            fetch_t = await session.get(url, follow_redirects=True)
        except Exception:
            logging.exception("get_t GET failed")
            continue
        last_html = fetch_t.text or ""
        last_status = fetch_t.status_code
        token = _extract_t(last_html)
        if token:
            return token
        loc = str(getattr(fetch_t, "url", "") or "")
        loc_t = re.search(r"[?&#]t=([^&#]+)", loc)
        if loc_t:
            return loc_t.group(1)

    page_id = re.search(r'PageID" content="([^"]+)"', last_html or "")
    sft = re.search(r'"sFT"\s*:\s*"([^"]+)"', last_html or "")
    logging.warning(
        "get_t: no classic t token (status=%s page=%s sFT=%s len=%s)",
        last_status,
        page_id.group(1) if page_id else "?",
        bool(sft),
        len(last_html or ""),
    )
    return None
