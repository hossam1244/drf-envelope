"""The exception handler: every failure becomes one envelope.

    {"error": {"code": "insufficient_funds", "message": "...", "details": {...}}}

Clients get the same shape everywhere, with stable machine-readable codes —
instead of DRF's mixed `{"detail": ...}` / `{"field": ["msg"]}` output.
"""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)

#: Stable renames so clients depend on vocabulary, not DRF internals.
CODE_REWRITES: dict[str, str] = {
    "invalid": "validation_failed",
    "no_active_account": "authentication_failed",  # simplejwt's login failure
    "throttled": "rate_limited",
    "not_found_or_permission_denied": "permission_denied",
}

FALLBACK_MESSAGE = "An unexpected error occurred."


def envelope_error_body(code: str, message: str, details: Any = None) -> dict:
    """Builds the uniform body — exported for services that want to raise
    pre-shaped errors."""
    body: dict = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"error": body}


class EnvelopeExceptionHandler:
    """Drop-in ``EXCEPTION_HANDLER`` for DRF.

    ```python
    REST_FRAMEWORK = {
        "EXCEPTION_HANDLER": "drf_envelope.handler.envelope_exception_handler"
    }
    ```
    """

    def __call__(self, exc: Exception, context: dict) -> Response | None:
        if isinstance(exc, DjangoValidationError):
            exc = drf_exceptions.ValidationError(detail=exc.message_dict)

        response = drf_exception_handler(exc, context)

        if response is None:
            logger.exception("Unhandled API exception", exc_info=exc)
            return Response(envelope_error_body("internal_error", FALLBACK_MESSAGE), status=500)

        code = self.code_for(exc)
        message, details = self.message_and_details(response.data)

        # ApiError carries structured details the base handler can't know about.
        domain_details = getattr(exc, "details", None)
        if domain_details is not None:
            details = domain_details

        response.data = envelope_error_body(code, message, details)
        return response

    # -- internals ----------------------------------------------------------

    def code_for(self, exc: Exception) -> str:
        if isinstance(exc, drf_exceptions.APIException):
            codes = exc.get_codes()
            if isinstance(codes, str):
                return CODE_REWRITES.get(codes, codes)
            return CODE_REWRITES.get(exc.default_code, exc.default_code)
        if isinstance(exc, DjangoPermissionDenied):
            return "permission_denied"
        if isinstance(exc, Http404):
            return "not_found"
        return "error"

    def message_and_details(self, data: Any) -> tuple[str, Any]:
        if isinstance(data, dict) and set(data) == {"detail"}:
            return str(data["detail"]), None
        if isinstance(data, dict):
            # Field-level validation errors: keep the mapping under details.
            return "Request failed validation.", data
        if isinstance(data, list):
            return "Request failed validation.", {"non_field_errors": data}
        return FALLBACK_MESSAGE, None


#: Module-level function reference for the settings string.
envelope_exception_handler = EnvelopeExceptionHandler()


class ApiError(drf_exceptions.APIException):
    """Raise from services with a stable code, message, and structured details.

    ```python
    raise ApiError(
        "The account does not hold enough funds for this payment.",
        code="insufficient_funds",
        details={"available": "10.00", "requested": "50.00"},
        status_code=422,
    )
    ```
    """

    status_code = 400
    default_code = "error"
    default_detail = "Something went wrong."

    def __init__(
        self,
        detail: str | None = None,
        *,
        code: str | None = None,
        details: Any = None,
        status_code: int | None = None,
    ) -> None:
        if detail is None:
            detail = self.default_detail
        super().__init__(detail=detail, code=code or self.default_code)
        self.details = details
        if status_code is not None:
            self.status_code = status_code
