# VakeTomatti identity gateway operations

## Modes

`IDENTITY_MODE=development` is for local/integration development only. It resolves `DEVELOPMENT_STATIC` with all Funding permissions. Production rejects this mode.

`IDENTITY_MODE=gateway` is the production integration mode. Configure `IDENTITY_GATEWAY_SHARED_SECRET` from approved secret storage and keep `IDENTITY_GATEWAY_MAX_AGE_SECONDS` short (default 300 seconds).

Preview mode uses the fixed `PREVIEW_FIXTURE` identity regardless of gateway settings.

## Signed request fields

The gateway sends:

- `X-Vake-Actor-Id`
- `X-Vake-Actor-Name` (optional)
- `X-Vake-Permissions` (comma-separated Funding permissions)
- `X-Vake-Identity-Issued-At` (Unix seconds)
- `X-Vake-Identity-Signature` (hex HMAC-SHA256)

The canonical signed message is newline-separated:

`actor_id`, `display_name`, sorted/canonical permissions, `issued_at`, uppercase HTTP method, request path, raw query string.

Funding returns HTTP 401 for missing/invalid/expired signatures and HTTP 403 for an authenticated actor that lacks the required permission.

## Permission mapping

The upstream gateway must map organization roles/groups to the narrowest Funding permissions required. `funding.admin` implies all Funding permissions and should be rare.

Do not send raw OIDC access/ID tokens in audit data. Funding stores only the resolved actor identity/source on approval events.

## Deployment checklist

1. Organization SSO/OIDC authentication is enforced before the gateway signs a request.
2. Direct client access to the Funding service is restricted according to the approved network architecture.
3. Gateway-to-Funding transport uses approved TLS/network controls.
4. Shared signing secret is provisioned through secret management, not `.env` committed to Git.
5. Rotation procedure supports changing the gateway and service secret together.
6. Role/group-to-permission mapping is reviewed with the business/security owner.
7. Negative tests prove ordinary users cannot approve and unsigned/spoofed requests fail.
8. `/api/session` returns only actor/display source/permissions and never tokens or secrets.
