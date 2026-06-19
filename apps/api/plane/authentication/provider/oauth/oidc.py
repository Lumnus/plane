# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# Generic OIDC provider — Lumnus addition to the public AGPL fork (Lumnus/plane).
# Plane gates generic OIDC behind EE for commercial reasons; we don't share them, so this adds a
# standards-based OIDC Authorization-Code provider to CE. Endpoints are resolved from the issuer's
# OpenID discovery document ({issuer}/.well-known/openid-configuration) so it works against any
# compliant IdP (our substrate uses Keycloak: https://login.lumnus.net/realms/lumnus).

import os
from datetime import datetime, timedelta
from urllib.parse import urlencode

import pytz
import requests

# Module imports
from plane.authentication.adapter.oauth import OauthAdapter
from plane.license.utils.instance_value import get_configuration_value
from plane.authentication.adapter.error import (
    AUTHENTICATION_ERROR_CODES,
    AuthenticationException,
)


class OIDCOAuthProvider(OauthAdapter):
    provider = "oidc"
    scope = "openid email profile"

    def __init__(self, request, code=None, state=None, callback=None):
        (
            OIDC_CLIENT_ID,
            OIDC_CLIENT_SECRET,
            OIDC_ISSUER,
            OIDC_AUTHORIZE_URL,
            OIDC_TOKEN_URL,
            OIDC_USERINFO_URL,
        ) = get_configuration_value(
            [
                {"key": "OIDC_CLIENT_ID", "default": os.environ.get("OIDC_CLIENT_ID")},
                {"key": "OIDC_CLIENT_SECRET", "default": os.environ.get("OIDC_CLIENT_SECRET")},
                {"key": "OIDC_ISSUER", "default": os.environ.get("OIDC_ISSUER")},
                {"key": "OIDC_AUTHORIZE_URL", "default": os.environ.get("OIDC_AUTHORIZE_URL")},
                {"key": "OIDC_TOKEN_URL", "default": os.environ.get("OIDC_TOKEN_URL")},
                {"key": "OIDC_USERINFO_URL", "default": os.environ.get("OIDC_USERINFO_URL")},
            ]
        )

        if not (OIDC_CLIENT_ID and OIDC_CLIENT_SECRET):
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                error_message="OIDC_NOT_CONFIGURED",
            )

        # Resolve endpoints: explicit URLs win; otherwise discover from the issuer.
        authorize_url, token_url, userinfo_url = (
            OIDC_AUTHORIZE_URL,
            OIDC_TOKEN_URL,
            OIDC_USERINFO_URL,
        )
        if not (authorize_url and token_url and userinfo_url):
            if not OIDC_ISSUER:
                raise AuthenticationException(
                    error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                    error_message="OIDC_NOT_CONFIGURED",
                )
            disc = self._discover(OIDC_ISSUER.rstrip("/"))
            authorize_url = authorize_url or disc.get("authorization_endpoint")
            token_url = token_url or disc.get("token_endpoint")
            userinfo_url = userinfo_url or disc.get("userinfo_endpoint")

        if not (authorize_url and token_url and userinfo_url):
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                error_message="OIDC_NOT_CONFIGURED",
            )

        self.token_url = token_url
        self.userinfo_url = userinfo_url

        client_id = OIDC_CLIENT_ID
        client_secret = OIDC_CLIENT_SECRET

        redirect_uri = (
            f"{'https' if request.is_secure() else 'http'}://{request.get_host()}/auth/oidc/callback/"
        )
        url_params = {
            "client_id": client_id,
            "scope": self.scope,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
        }
        auth_url = f"{authorize_url}?{urlencode(url_params)}"

        super().__init__(
            request,
            self.provider,
            client_id,
            self.scope,
            redirect_uri,
            auth_url,
            self.token_url,
            self.userinfo_url,
            client_secret,
            code,
            callback=callback,
        )

    def _discover(self, issuer):
        try:
            resp = requests.get(f"{issuer}/.well-known/openid-configuration", timeout=10)
            if not resp.ok:
                raise AuthenticationException(
                    error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                    error_message="OIDC_NOT_CONFIGURED",
                )
            return resp.json()
        except requests.RequestException:
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OIDC_NOT_CONFIGURED"],
                error_message="OIDC_NOT_CONFIGURED",
            )

    def set_token_data(self):
        data = {
            "code": self.code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        headers = {"Accept": "application/json"}
        token_response = self.get_user_token(data=data, headers=headers)
        super().set_token_data(
            {
                "access_token": token_response.get("access_token"),
                "refresh_token": token_response.get("refresh_token", None),
                "access_token_expired_at": (
                    datetime.now(tz=pytz.utc) + timedelta(seconds=token_response.get("expires_in"))
                    if token_response.get("expires_in")
                    else None
                ),
                "refresh_token_expired_at": (
                    datetime.now(tz=pytz.utc) + timedelta(seconds=token_response.get("refresh_expires_in"))
                    if token_response.get("refresh_expires_in")
                    else None
                ),
                "id_token": token_response.get("id_token", ""),
            }
        )

    def set_user_data(self):
        user_info_response = self.get_user_response()

        email = user_info_response.get("email")
        if not email:
            raise AuthenticationException(
                error_code=AUTHENTICATION_ERROR_CODES["OIDC_OAUTH_PROVIDER_ERROR"],
                error_message="OIDC_OAUTH_PROVIDER_ERROR: provider returned no email",
            )

        first_name = (
            user_info_response.get("given_name")
            or user_info_response.get("name")
            or user_info_response.get("preferred_username")
            or email
        )
        last_name = user_info_response.get("family_name") or ""

        super().set_user_data(
            {
                "email": email,
                "user": {
                    "provider_id": str(
                        user_info_response.get("sub") or user_info_response.get("id")
                    ),
                    "email": email,
                    "avatar": user_info_response.get("picture", ""),
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_password_autoset": True,
                },
            }
        )
