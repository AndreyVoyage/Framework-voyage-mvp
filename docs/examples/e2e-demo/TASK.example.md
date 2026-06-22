# Generated task example: Add User Authentication to the API

> **Generated, non-canonical example.** This represents a legacy `TASK.md`-style artifact. The adjacent `task.yaml` remains the canonical task specification.

## Role: developer
## Mode: implement
## Priority: high

## Description

Implement JWT-based authentication for the REST API endpoints.

## Acceptance criteria

- [ ] POST /auth/login returns a JWT for valid demo credentials
- [ ] POST /auth/register creates a user with a bcrypt-hashed password
- [ ] GET /api/protected returns 401 without a valid token
- [ ] Tokens expire after 24 hours
- [ ] Passwords use bcrypt with cost factor 12
- [ ] Authentication endpoints are limited to 5 requests per minute

## Files to read

- `src/api/routes.py`
- `src/auth/jwt_handler.py`

## Files to modify

- `src/api/routes.py`
- `src/auth/jwt_handler.py`
- `tests/test_auth.py`

## Tests

- `test_login_valid_credentials_returns_token`
- `test_login_invalid_credentials_returns_401`
- `test_protected_endpoint_without_token_returns_401`
- `test_token_expiration_after_24h`
- `test_password_hashing_uses_bcrypt`
- `test_auth_rate_limit_five_requests_per_minute`

## Rules

- [ ] Stay within the listed file scope.
- [ ] Do not commit or push without explicit instruction.
- [ ] Do not expose secrets or use real credentials.
- [ ] Run the required tests before handoff.
- [ ] Report deviations instead of guessing.
