# drf-envelope

**Uniform error envelopes for Django REST Framework.**

Every failure becomes one shape, with stable machine-readable codes:

```json
{"error": {"code": "insufficient_funds", "message": "The account does not hold enough funds…", "details": {"available": "10.00"}}}
```

[![CI](https://github.com/hossam1244/drf-envelope/actions/workflows/ci.yml/badge.svg)](https://github.com/hossam1244/drf-envelope/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/badge/pypi-0.1.0-blue)](https://pypi.org/project/drf-envelope/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why

DRF's default error output is inconsistent by design: `{"detail": "…"}` for
most errors, `{"field": ["msg", …]}` for validation, `{"detail": "…"}` with
different semantics for permissions — and nothing your mobile clients can
switch on. Every serious API eventually writes the same wrapper: one
envelope, one vocabulary, structured details where they exist. This is that
wrapper, extracted from a banking-grade backend
([novabank-api](https://github.com/hossam1244/novabank-api)).

* **One shape everywhere** — auth, permissions, validation, throttling,
  not-found, domain errors, and (sanitized) 500s.
* **Stable codes** — `validation_failed`, `authentication_failed`,
  `rate_limited`, `permission_denied`, `not_found`, `internal_error`, plus
  your own.
* **`ApiError`** — raise domain errors from services with a code, message,
  structured details, and status — the envelope flows out automatically.
* **500s never leak internals** — the exception is logged server-side with a
  traceback; the client sees a clean `internal_error`.

## Install

```bash
pip install drf-envelope   # (PyPI soon; until then: pip install git+https://github.com/hossam1244/drf-envelope.git)
```

```python
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "drf_envelope.handler.envelope_exception_handler",
}
```

Raise domain errors anywhere:

```python
from drf_envelope.handler import ApiError


def checkout(cart):
    if cart.total > account.balance:
        raise ApiError(
            "The account does not hold enough funds for this payment.",
            code="insufficient_funds",
            details={"available": str(account.balance), "requested": str(cart.total)},
            status_code=422,
        )
```

Clients get a contract they can depend on:

| Situation | Status | `error.code` |
|---|---|---|
| Field validation | 400 | `validation_failed` (details carry the field map) |
| Bad credentials | 401 | `authentication_failed` |
| Missing/insufficient auth | 401 | `not_authenticated` |
| Forbidden | 403 | `permission_denied` |
| Throttled | 429 | `rate_limited` |
| Not found | 404 | `not_found` |
| Domain `ApiError` | yours | yours |
| Unhandled | 500 | `internal_error` (message generic; details logged, not leaked) |

## Testing

7 tests: validation shape with field details, domain `ApiError` pass-through,
sanitized 500s, auth/404 codes, envelope helper, and `ApiError` defaults.

```bash
pip install -e . && pytest
```

## License

[MIT](LICENSE)
