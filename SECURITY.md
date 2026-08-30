# Security Baseline

VakeVahti is being developed as a workplace automation system and must remain maintainable, auditable and safe to hand over.

## Repository and data handling

- Do not commit passwords, access tokens, connection secrets, private certificates or production credentials.
- Do not commit confidential workplace documents, personal data or proprietary source material to the public repository.
- Use sanitized fixtures and examples for public tests/documentation.
- Runtime secrets belong in approved environment/secret-management facilities.

## Authentication and authorization

The current development demo is not a production authorization boundary. Before organizational deployment, access must use the approved Vake/Vaketomate identity mechanism and explicit role/permission checks.

Authentication does not imply authorization to every capability.

## External source access

- External source URLs are administrator-controlled configuration, not arbitrary user-supplied fetch targets.
- Use normal HTTP behavior and published pages/APIs; do not implement anti-bot evasion.
- Apply timeouts and fail visibly on network/source-structure errors.
- A source failure must not be interpreted as successful empty data.

## Audit and logging

- Persist source-run lifecycle and bounded failure metadata.
- Do not store authentication tokens, passwords or unnecessary personal data in audit records.
- Production logs should use structured logging, controlled retention and access restrictions.
- Correlation/run IDs should connect related operational activity without exposing secrets.

## Database

- PostgreSQL schema changes use Alembic migrations.
- Use least-privilege database credentials in deployed environments.
- Keep integrity invariants in the database as well as application validation.
- Backups, restoration tests, retention and decommissioning must be documented before production use.

## Dependencies and CI

Ruff, strict mypy, unit/integration tests and migration application are required quality gates. Dependency/security scanning will be added before production deployment.

## Reporting a security issue

For workplace deployment, use the organization's approved security/incident channel. Do not publish sensitive vulnerability details, production configuration or credentials in a public GitHub issue.
