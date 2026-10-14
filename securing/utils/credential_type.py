import logging
import httpx

logger = logging.getLogger(__name__)

async def fetch_credential_type(email: str) -> dict | None:
    """Read-only GetCredentialType probe for Microsoft accounts."""
    if not email or "@" not in email:
        return None
    url = "https://login.live.com/GetCredentialType.srf"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Referer": "https://login.live.com/",
    }
    payload = {
        "checkPhones": True,
        "country": "",
        "federationFlags": 0,
        "flowToken": "",
        "forceotclogin": False,
        "isCookieBannerShown": False,
        "isExternalFederationDisallowed": False,
        "isFederationDisabled": False,
        "isFidoSupported": True,
        "isOtherIdpSupported": False,
        "isReactLoginRequest": True,
        "isRemoteConnectSupported": False,
        "isRemoteNGCSupported": True,
        "isSignup": False,
        "otclogindisallowed": False,
        "username": email,
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning(f"GetCredentialType failed for {email}: {exc}")
    return None
