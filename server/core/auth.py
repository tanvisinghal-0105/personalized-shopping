"""
Authentication and authorization for Google employees.

Supports two auth methods:
1. Google Identity-Aware Proxy (IAP) -- for Cloud Run deployed services
2. Google OAuth2 ID tokens -- for local development

Validates that the user has a @google.com email address.
"""

import os
import logging
from typing import Optional, Dict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Allowed email domains (Google employees only)
ALLOWED_DOMAINS = ["google.com"]

# Set to False to disable auth (local dev)
AUTH_ENABLED = os.environ.get("AUTH_ENABLED", "false").lower() == "true"


@lru_cache(maxsize=1)
def _get_google_certs():
    """Fetch Google's public certificates for token verification."""
    import requests

    resp = requests.get("https://www.googleapis.com/oauth2/v3/certs", timeout=10)
    resp.raise_for_status()
    return resp.json()


def verify_google_identity(token: str) -> Optional[Dict]:
    """Verify a Google ID token or IAP JWT.

    Args:
        token: Bearer token from Authorization header or IAP x-goog-iap-jwt-assertion

    Returns:
        Dict with user info (email, name) or None if invalid
    """
    if not AUTH_ENABLED:
        return {"email": "dev@google.com", "name": "Dev User", "auth": "disabled"}

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests

        # Verify the token with Google
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(token, request)

        email = id_info.get("email", "")
        domain = email.split("@")[-1] if "@" in email else ""

        if domain not in ALLOWED_DOMAINS:
            logger.warning(f"[AUTH] Rejected non-Google email: {email}")
            return None

        user = {
            "email": email,
            "name": id_info.get("name", email.split("@")[0]),
            "picture": id_info.get("picture", ""),
            "domain": domain,
        }
        logger.info(f"[AUTH] Authenticated: {email}")
        return user

    except Exception as e:
        logger.warning(f"[AUTH] Token verification failed: {e}")
        return None


def verify_iap_jwt(iap_jwt: str, expected_audience: str = "") -> Optional[Dict]:
    """Verify an IAP JWT assertion (used when behind Cloud IAP).

    Args:
        iap_jwt: The x-goog-iap-jwt-assertion header value
        expected_audience: Expected audience claim

    Returns:
        Dict with user info or None if invalid
    """
    if not AUTH_ENABLED:
        return {"email": "dev@google.com", "name": "Dev User", "auth": "disabled"}

    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token

        request = google_requests.Request()
        id_info = id_token.verify_token(
            iap_jwt,
            request,
            audience=expected_audience,
            certs_url="https://www.gstatic.com/iap/verify/public_key",
        )

        email = id_info.get("email", "")
        domain = email.split("@")[-1] if "@" in email else ""

        if domain not in ALLOWED_DOMAINS:
            logger.warning(f"[AUTH] IAP rejected non-Google email: {email}")
            return None

        return {
            "email": email,
            "name": id_info.get("name", email.split("@")[0]),
            "domain": domain,
            "auth": "iap",
        }

    except Exception as e:
        logger.warning(f"[AUTH] IAP JWT verification failed: {e}")
        return None


def authenticate_websocket(headers: dict) -> Optional[Dict]:
    """Authenticate a WebSocket connection from request headers.

    Checks in order:
    1. IAP JWT (x-goog-iap-jwt-assertion)
    2. Authorization Bearer token
    3. Auth disabled (local dev)

    Returns:
        User info dict or None if unauthorized
    """
    if not AUTH_ENABLED:
        return {"email": "dev@google.com", "name": "Dev User", "auth": "disabled"}

    # Check IAP header first (Cloud Run behind IAP)
    iap_jwt = headers.get("x-goog-iap-jwt-assertion")
    if iap_jwt:
        return verify_iap_jwt(iap_jwt)

    # Check Authorization header
    auth_header = headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        return verify_google_identity(token)

    logger.warning("[AUTH] No auth token provided")
    return None
