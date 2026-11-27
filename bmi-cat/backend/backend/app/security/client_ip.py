import ipaddress


def resolve_client_ip(request, settings=None) -> str:
    """Return the client address, trusting proxy headers only from known peers."""
    direct = request.client.host if request and request.client else "unknown"
    if settings is None:
        settings = getattr(getattr(getattr(request, "app", None), "state", None), "settings", None)
    trusted = set(getattr(settings, "trusted_proxies", ()) or ())
    if direct not in trusted:
        return direct
    forwarded = request.headers.get("x-forwarded-for", "") if request else ""
    chain = [value.strip() for value in forwarded.split(",") if value.strip()]
    if not chain:
        return direct
    try:
        for value in chain:
            ipaddress.ip_address(value)
    except ValueError:
        return direct
    for value in reversed(chain):
        if value not in trusted:
            return value
    return direct
