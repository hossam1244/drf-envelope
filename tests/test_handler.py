import pytest

pytestmark = pytest.mark.django_db


def test_validation_error_shape(client):
    response = client.post(
        "/signup/", {"email": "not-an-email", "password": "short"}, content_type="application/json"
    )

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "validation_failed"
    assert error["message"] == "Request failed validation."
    assert "email" in error["details"]
    assert "password" in error["details"]


def test_domain_api_error_passes_through_with_details(client):
    response = client.post("/pay/", {}, content_type="application/json")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "insufficient_funds"
    assert "enough funds" in error["message"]
    assert error["details"] == {"available": "10.00", "requested": "50.00"}


def test_unhandled_exception_becomes_clean_500(client):
    response = client.post("/boom/", {}, content_type="application/json")

    assert response.status_code == 500
    error = response.json()["error"]
    assert error["code"] == "internal_error"
    assert error["message"] == "An unexpected error occurred."
    assert "kaboom" not in response.content.decode()


def test_authentication_failure_code(client):
    response = client.get("/me/")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


def test_not_found_envelope(client):
    response = client.get("/missing/")

    assert response.status_code == 404
    body = response.json()["error"]
    assert body["code"] == "not_found"
    assert "message" in body


def test_detail_only_becomes_message(client):
    from drf_envelope.handler import envelope_error_body

    body = envelope_error_body("x", "plain message")
    assert body == {"error": {"code": "x", "message": "plain message"}}


def test_api_error_defaults():
    from drf_envelope.handler import ApiError

    error = ApiError("something")
    assert error.status_code == 400
    assert error.default_code == "error"
    assert str(error.detail) == "something"
    assert error.details is None
