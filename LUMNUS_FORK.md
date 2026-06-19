# Lumnus fork of Plane CE — delta documentation

This is **Lumnus's fork** of [Plane](https://github.com/makeplane/plane) Community Edition, branch `preview`. It is **public** (AGPL-3.0; public availability satisfies the license — we do not PR upstream). We enhance the CE the way upstream gates features behind paid cloud tiers, **re-implementing them in the open** rather than unlocking flags (the paid features live in a closed EE repo with **no `ee/` directory in CE**).

> **Substrate-side counterpart:** *how we choose to deploy + operate + tenant* Plane lives in the substrate at `docs/project/plane-adoption-ledger.md` (Hub repo, private). This file documents only the **code deltas from upstream CE**. Keep both current.

## Deltas from upstream Plane CE

### 1. Generic OIDC authentication provider (`4159746`)

Standards OIDC Authorization-Code provider so Plane authenticates against any OIDC IdP (we use Keycloak). Upstream gates SSO behind paid tiers; this is a clean generic provider, CE-licensed.

- **NEW** `apps/api/plane/authentication/provider/oauth/oidc.py` — `OIDCOAuthProvider`; discovery via `{OIDC_ISSUER}/.well-known/openid-configuration` (or explicit `OIDC_*_URL`); scope `openid email profile`; userinfo → email/sub mapping.
- **NEW** `apps/api/plane/authentication/views/{app,space}/oidc.py` — initiate + callback views.
- **EDIT** `urls.py` (oidc routes) · `views/__init__.py` (exports) · `adapter/error.py` (`OIDC_NOT_CONFIGURED` 5113, `OIDC_OAUTH_PROVIDER_ERROR` 5124) · `utils/instance_config_variables/core.py` (oidc config block + aggregate) · `license/api/views/instance.py` (`is_oidc_enabled`).
- **EDIT** `apps/web/core/hooks/oauth/core.tsx` ("Sign in with SSO" button + `isOAuthEnabled`) · `packages/types/src/instance/base.ts` (`is_oidc_enabled`).
- **Config** (env): `IS_OIDC_ENABLED=1`, `OIDC_ISSUER`, `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`. Redirect URIs: `/auth/oidc/callback/` + `/auth/spaces/oidc/callback/`.

### 2. Remove "Billing & Plans" from settings nav

Self-hosted; no cloud billing. The settings-sidebar "Billing & Plans" entry is removed.

- **EDIT** `packages/constants/src/settings/workspace.ts` — removed `WORKSPACE_SETTINGS["billing-and-plans"]` from `GROUPED_WORKSPACE_SETTINGS[ADMINISTRATION]`. The entry *definition* is retained (so `apps/web/app/.../settings/(workspace)/billing/header.tsx` + the route still type-check); the `/settings/billing` route is **orphaned** (unreachable via nav). Minimal, low-risk; the visible "pin in the eye" is gone.

## Build + deploy (the enhancement loop)

1. Edit here; commit + push to `Lumnus/plane@preview`.
2. Build images → `registry.lab.lumnus.net/staging/lumnus/plane-{backend,frontend,admin,space,live}:lumnus-<date>-<feat>`. **The Helm chart uses ONE global `planeVersion` tag → retag ALL 5 images on a bump.**
3. Bump `planeVersion` in the substrate's `infra/cluster-blast/apps/plane/values.yaml`; ArgoCD app `plane` syncs.
4. Update this file (code delta) + the substrate adoption-ledger (integration choice).

## Rebasing on upstream

Deltas are deliberately **additive + minimally-invasive** (new files + small edits) to ease rebasing on upstream `preview`. When pulling upstream: rebase, re-apply the small edits in the EDIT lists above (new files carry cleanly), rebuild.
