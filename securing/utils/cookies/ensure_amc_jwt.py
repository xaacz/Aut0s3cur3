"""Establish AMCSecAuth / AMCSecAuthJWT for account.microsoft.com APIs.

Without these cookies, personal-info / subscriptions / devices all return 401
(``getPersonalInfoFailed`` / ``unauthorized``). Dona-fork runs a dedicated
amc + amcjwt hop after login; our polish was skipping SSO once MSAAUTH existed.
"""

from __future__ import annotations

import asyncio
import logging
import re
from urllib.parse import urljoin

import httpx

from securing.utils.cookies.safe_cookies import has_cookie
from securing.utils.proxy import format_exception_reason

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(25.0, connect=10.0)


def has_amc_api_cookies(session: httpx.AsyncClient) -> bool:
    return has_cookie(session, "AMCSecAuthJWT") or has_cookie(session, "AMCSecAuth")


async def ensure_amc_jwt(session: httpx.AsyncClient, *, attempts: int = 2) -> bool:
    """Best-effort: walk account.microsoft.com OAuth until AMC JWT is set.

    Mirrors dona ``tokens/amcjwt.py`` + ``tokens/amc.py`` silent-signin.
    Returns True when an AMC API cookie is present afterwards.
    Retries once on ReadTimeout — a lone timeout was aborting whole secure().
    """
    if has_amc_api_cookies(session):
        return True

    for attempt in range(1, max(1, attempts) + 1):
        ok = await _ensure_amc_jwt_once(session, attempt=attempt)
        if ok:
            return True
        if attempt < attempts:
            await asyncio.sleep(1.0 * attempt)
    return False


async def _ensure_amc_jwt_once(session: httpx.AsyncClient, *, attempt: int = 1) -> bool:
    if has_amc_api_cookies(session):
        return True

    try:
        # --- amcjwt-style redirect chase (no JS) ---
        resp = await session.get(
            "https://account.microsoft.com/",
            follow_redirects=False,
            timeout=_TIMEOUT,
        )
        for hop in range(6):
            loc = resp.headers.get("location")
            if not loc:
                break
            if not loc.startswith("http"):
                loc = urljoin(str(resp.url), loc)
            log.info("ensure_amc_jwt hop %s → %s", hop, loc[:180])
            resp = await session.get(loc, follow_redirects=False, timeout=_TIMEOUT)
            if has_amc_api_cookies(session):
                print("[+] - AMCSecAuthJWT established (redirect chase)")
                return True
            # Sometimes the final hop is 200 with Set-Cookie
            if resp.status_code in (200, 302, 303) and has_amc_api_cookies(session):
                return True

        # Follow redirects fully once more (oauth complete pages)
        resp = await session.get(
            "https://account.microsoft.com/",
            follow_redirects=True,
            timeout=_TIMEOUT,
        )
        if has_amc_api_cookies(session):
            print("[+] - AMCSecAuthJWT established (full redirect)")
            return True

        # --- amc-style silent signin with ``t`` token ---
        resp = await session.get(
            "https://account.microsoft.com/",
            follow_redirects=False,
            timeout=_TIMEOUT,
        )
        loc = resp.headers.get("location")
        if loc:
            if not loc.startswith("http"):
                loc = urljoin(str(resp.url), loc)
            step2 = await session.get(loc, follow_redirects=True, timeout=_TIMEOUT)
            text = step2.text or ""
            t_m = re.search(
                r'<input[^>]*name="t"[^>]*value="([^"]+)"',
                text,
                re.I,
            ) or re.search(
                r'<input[^>]*id="t"[^>]*value="([^"]+)"',
                text,
                re.I,
            )
            if t_m:
                # Match dona tokens/amc.py nested complete-silent-signin ru=
                post_urls = (
                    (
                        "https://account.microsoft.com/auth/complete-silent-signin"
                        "?ru=https://account.microsoft.com/"
                        "auth/complete-silent-signin?ru=https%3A%2F%2Faccount.microsoft.com%2F"
                        "&wa=wsignin1.0&refd=login.live.com&wa=wsignin1.0"
                    ),
                    (
                        "https://account.microsoft.com/auth/complete-silent-signin"
                        "?ru=https://account.microsoft.com/"
                        "&wa=wsignin1.0&refd=login.live.com"
                    ),
                )
                for post_url in post_urls:
                    await session.post(
                        post_url,
                        data={"t": t_m.group(1)},
                        headers={"X-Requested-With": "XMLHttpRequest"},
                        follow_redirects=True,
                        timeout=_TIMEOUT,
                    )
                    if has_amc_api_cookies(session):
                        print("[+] - AMCSecAuth established (silent signin)")
                        return True

        # Last resort: hit profile which often finishes oauth
        await session.get(
            "https://account.microsoft.com/profile?lang=en-US",
            follow_redirects=True,
            timeout=_TIMEOUT,
        )
        if has_amc_api_cookies(session):
            print("[+] - AMCSecAuthJWT established (profile hop)")
            return True

        # Passwordless / Gmail / already-signed-in: account.microsoft.com often
        # returns 200 chrome with no Location. Force login.live.com OAuth / wsignin
        # so AMC cookies get issued (needed for names/manage canary).
        if await _oauth_amc_signin(session):
            return True

    except (httpx.TimeoutException, httpx.TransportError) as exc:
        detail = format_exception_reason(exc)
        log.warning("ensure_amc_jwt transport error (attempt %s): %s", attempt, detail)
        print(f"[!] - ensure_amc_jwt failed ({detail}) [attempt {attempt}]")
    except Exception:
        log.exception("ensure_amc_jwt crashed (attempt %s)", attempt)

    ok = has_amc_api_cookies(session)
    if not ok and attempt >= 2:
        print("[!] - No AMCSecAuthJWT — account.microsoft.com APIs will 401")
    return ok


_AMC_OAUTH = (
    "https://login.live.com/oauth20_authorize.srf"
    "?client_id=000000004C12AE6F"
    "&response_type=token"
    "&scope=service::account.microsoft.com::MBI_SSL"
    "&redirect_uri=https://account.microsoft.com/auth/complete-signin-oauth"
    "&prompt=none"
)
_AMC_WSIGNIN = (
    "https://login.live.com/login.srf?wa=wsignin1.0"
    "&wreply=https%3A%2F%2Faccount.microsoft.com%2F"
    "&rver=7.5.2211.0&wp=MBI_SSL_SHARED"
)
_T_RE = re.compile(
    r'<input[^>]*(?:name|id)="t"[^>]*value="([^"]+)"'
    r'|<input[^>]*value="([^"]+)"[^>]*(?:name|id)="t"',
    re.I,
)


async def _chase_interrupt_html(session: httpx.AsyncClient, html: str) -> str:
    """Accrou / privacy / pprid forms after already-signed-in OAuth."""
    if not html:
        return html
    low = html.lower()
    if (
        "pprid" not in html
        and "privacynotice" not in low
        and "identity/confirm" not in low
        and "accrou" not in low
    ):
        return html
    try:
        from securing.auth.handle_redirects import handle_redirects

        result = await handle_redirects(session, html)
        if isinstance(result, str) and result not in ("Family", "Recovery"):
            return result
    except Exception as exc:
        log.warning("ensure_amc_jwt interrupt chase failed: %s", exc)
    return html


async def _post_silent_signin(session: httpx.AsyncClient, ticket: str) -> bool:
    post_urls = (
        (
            "https://account.microsoft.com/auth/complete-silent-signin"
            "?ru=https://account.microsoft.com/"
            "auth/complete-silent-signin?ru=https%3A%2F%2Faccount.microsoft.com%2F"
            "&wa=wsignin1.0&refd=login.live.com&wa=wsignin1.0"
        ),
        (
            "https://account.microsoft.com/auth/complete-silent-signin"
            "?ru=https://account.microsoft.com/"
            "&wa=wsignin1.0&refd=login.live.com"
        ),
        "https://account.microsoft.com/auth/complete-signin-oauth",
    )
    for post_url in post_urls:
        try:
            await session.post(
                post_url,
                data={"t": ticket},
                headers={"X-Requested-With": "XMLHttpRequest"},
                follow_redirects=True,
                timeout=_TIMEOUT,
            )
        except (httpx.TimeoutException, httpx.TransportError):
            continue
        if has_amc_api_cookies(session):
            print("[+] - AMCSecAuthJWT established (oauth silent signin)")
            return True
    return False


async def _oauth_amc_signin(session: httpx.AsyncClient) -> bool:
    """Force AMC cookies via login.live.com when the AMC homepage is a dead 200."""
    if has_amc_api_cookies(session):
        return True

    for url in (_AMC_OAUTH, _AMC_WSIGNIN):
        try:
            resp = await session.get(url, follow_redirects=True, timeout=_TIMEOUT)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            log.warning("oauth AMC GET failed (%s): %s", url[:60], exc)
            continue

        html = await _chase_interrupt_html(session, resp.text or "")
        if has_amc_api_cookies(session):
            print("[+] - AMCSecAuthJWT established (oauth redirect)")
            return True

        t_m = _T_RE.search(html or "")
        ticket = (t_m.group(1) or t_m.group(2)) if t_m else None
        if ticket and await _post_silent_signin(session, ticket):
            return True

        # Hash-fragment tokens sometimes land as a follow-up 302 Location
        loc = str(getattr(resp, "url", "") or "")
        if "account.microsoft.com" in loc.lower() and has_amc_api_cookies(session):
            print("[+] - AMCSecAuthJWT established (oauth landing)")
            return True

    return has_amc_api_cookies(session)
