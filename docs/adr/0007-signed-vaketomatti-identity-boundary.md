# ADR 0007: Signed VakeTomatti identity boundary and Funding authorization

Date: 2026-09-15  
Status: Accepted for the standalone-to-platform integration boundary

## Context

VakeVahti needs authenticated actor context for approvals and explicit authorization for Funding operations, but it must not create a competing employee password/user store. The approved organization/VakeTomatti platform is the intended SSO boundary.

A plain `X-User` header is not sufficient because a directly reachable client could forge it. Funding also needs permission-level authorization rather than treating every authenticated employee as an approver.

## Decision

Funding defines domain permissions such as:

- `funding.opportunities.read`
- `funding.opportunities.review`
- `funding.applications.edit`
- `funding.applications.approve`
- `funding.admin`

Production runs with `IDENTITY_MODE=gateway`. The upstream VakeTomatti identity gateway signs a canonical assertion containing actor ID, display name, canonical permission set, issued-at timestamp, HTTP method, path and query. Funding verifies the HMAC-SHA256 signature and short validity window before evaluating permissions.

Approval request bodies contain only the business decision/comment. Actor identity is injected by the backend identity dependency and recorded in the approval event.

Preview and development identities remain available for deterministic local/testing workflows, but `APP_ENV=production` refuses to start unless gateway identity mode is configured with a sufficiently long secret.

## Security properties and limitations

- The signature prevents an ordinary browser from inventing or altering a trusted actor/permission assertion without the gateway secret.
- Binding method/path/query reduces replay to a different Funding operation.
- The short issued-at window bounds replay time; it is not a complete nonce store.
- TLS and network restrictions remain required. HMAC is not a replacement for secure transport or gateway isolation.
- The shared secret must come from approved secret storage and be rotatable; it is never logged or committed.
- The gateway must obtain actor/role facts from the approved organization SSO/OIDC source. Funding does not authenticate passwords itself.

## Alternatives considered

### Trust unsigned identity headers

Rejected. They are only safe when a service is perfectly isolated behind a trusted proxy, and one deployment mistake would turn header spoofing into privilege escalation.

### Build login/password accounts inside Funding

Rejected. It duplicates organization identity, expands credential risk and conflicts with the VakeTomatti integration contract.

### Implement an interactive OIDC login flow in every Funding module

Rejected for the platform boundary. The shared shell/gateway should own organization login and pass the resulting scoped identity to Funding. Funding remains responsible for domain authorization.

## Consequences

- Backend permissions can be tested independently of the eventual organization IdP configuration.
- Approval audit actors are no longer client assertions.
- VakeTomatti needs a small signing adapter after successful SSO authentication/role mapping.
- Production deployment must document secret rotation, gateway reachability and permission mapping before enablement.
