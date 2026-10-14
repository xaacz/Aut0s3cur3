import logging
import httpx


async def remove_2fa(session: httpx.AsyncClient, apicanary: str):
    # Disables 2FA

    remove = await session.post(
        "https://account.live.com/API/Proofs/DisableTfa",
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "x-ms-apiVersion": "2",
            "x-ms-apiTransport": "xhr",
            "uiflvr": "1001",
            "scid": "100109",
            "hpgid": "201030",
            "X-Requested-With": "XMLHttpRequest",
            "canary": apicanary,
        },
        json={
            "uiflvr": 1001,
            "uaid": "abd2ca2a346c43c198c9ca7e4255f3bc",
            "scid": 100109,
            "hpgid": 201030,
        },
    )

    print(f"Remove Response: {remove.text} {remove.status_code}")
    err_code = None
    try:
        data = remove.json()
        err = data.get("error") if isinstance(data, dict) else None
        if isinstance(err, dict):
            err_code = err.get("code")
        elif err is not None:
            err_code = err
    except Exception:
        data = None

    # HTTP 200 + {"error":{"code":"6001"}} is ExpiredCredentials, not success.
    if remove.status_code == 200 and not err_code:
        print("[+] - Disabled 2FA")
        return True

    print(f"[X] - Failed to disable 2FA (status={remove.status_code} err={err_code})")
    logging.error("Failed to disable 2FA: %s", (remove.text or "")[:400])
    return False
