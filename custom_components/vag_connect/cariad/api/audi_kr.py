# Copyright 2026 Prash Balan (@its-me-prash) — GNU AGPL v3.0-or-later
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audi South Korea (myAudi KR) — APAC CARIAD-BFF client.

Live KR discovery:
  issuer:    https://identity.ap.vwgroup.io
  authorize: https://identity.ap.vwgroup.io/oidc/v1/authorize
  token:     https://ap.bff.cariad.digital/auth/v1/idk/oidc/token
  BFF:       https://ap.bff.cariad.digital

KR exposes no RFC-8628 device_authorization_endpoint, so this client uses the
existing e-mail/password Authorization-Code + PKCE path.
"""

from __future__ import annotations

from aiohttp import ClientSession

from .._home_region import HomeRegionCache
from ..auth.idk import IDKAuth
from ..models import BRAND_AUDI_KR
from .audi import AudiClient
from .base import CariadBaseClient

_AP_BFF_BASE = "https://ap.bff.cariad.digital"
_AP_IDP_BASE = "https://identity.ap.vwgroup.io"
_AP_AUTHORIZE_URL = f"{_AP_IDP_BASE}/oidc/v1/authorize"
_AP_TOKEN_URL = f"{_AP_BFF_BASE}/auth/v1/idk/oidc/token"


class AudiKRClient(AudiClient):
    """myAudi South Korea using the VW Group APAC IdentityKit/BFF."""

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
        spin: str = "",
    ) -> None:
        # AudiClient binds BRAND_AUDI (EMEA), so initialise the common base
        # directly with the KR BrandConfig, then restore VWEU regional caches.
        CariadBaseClient.__init__(
            self, session, BRAND_AUDI_KR, email, password, spin
        )
        self._azs_token: str | None = None
        self._vehicle_bases: dict[str, str] = {}
        self._home_region_cache: HomeRegionCache = HomeRegionCache()

        self._auth = IDKAuth(
            session,
            BRAND_AUDI_KR,
            authorize_url_override=_AP_AUTHORIZE_URL,
            token_url_override=_AP_TOKEN_URL,
            idk_base_override=_AP_IDP_BASE,
        )

    def _garage_base(self) -> str:
        return _AP_BFF_BASE

    def _base_for_vin(self, vin: str) -> str:
        bases: dict[str, str] = getattr(self, "_vehicle_bases", {})
        return bases.get(vin, _AP_BFF_BASE)

    def _azs_token_url(self) -> str:
        return f"{_AP_BFF_BASE}/login/v1/audi/token"

    def _engine_base(self) -> str:
        return f"{_AP_BFF_BASE}/vehicle/v1/engine"
