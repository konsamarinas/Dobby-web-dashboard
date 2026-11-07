from unittest.mock import Mock

import requests

import pytest

from app import create_app
from app.services.dobby_client import DobbyAPIError, DobbyClient


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


def test_pages_render(app):
    client = app.test_client()
    for path in ("/", "/metrics", "/health", "/recommendations", "/forecasting"):
        response = client.get(path)
        assert response.status_code == 200
        assert b"DOBBY Intelligence" in response.data


def test_recommendations_proxy_uses_client(app):
    mock_client = Mock()
    mock_client.recommendations.return_value = {"recommendations": [], "model_version": "rec-v2.0"}
    app.extensions["dobby_client"] = mock_client
    response = app.test_client().post("/api/recommendations", json={"business_id": "b"})
    assert response.status_code == 200
    mock_client.recommendations.assert_called_once_with({"business_id": "b"})


def test_client_rejects_non_object_response(monkeypatch):
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = []
    monkeypatch.setattr("requests.request", lambda *args, **kwargs: response)
    with pytest.raises(DobbyAPIError, match="unexpected response"):
        DobbyClient("https://example.test").health()


def test_api_failure_is_visible(app):
    mock_client = Mock()
    mock_client.health.side_effect = DobbyAPIError("The DOBBY API timed out.")
    app.extensions["dobby_client"] = mock_client
    response = app.test_client().get("/api/health")
    assert response.status_code == 502
    assert b"timed out" in response.data


def test_forecast_filters_unknown_parameters(app):
    mock_client = Mock()
    mock_client.forecast.return_value = {"forecast": []}
    app.extensions["dobby_client"] = mock_client
    response = app.test_client().get("/api/forecast?business_id=b&level=product&id=p&unexpected=x")
    assert response.status_code == 200
    mock_client.forecast.assert_called_once_with({"business_id": "b", "level": "product", "id": "p"})


def test_category_id_cannot_be_submitted_as_product(app):
    response = app.test_client().get(
        "/api/forecast?business_id=shop_commercial&level=product&id=shop_commercial_cat_coffee"
    )
    assert response.status_code == 400
    assert b"category ID cannot be used" in response.data


def test_category_forecast_is_forwarded(app):
    mock_client = Mock()
    mock_client.forecast.return_value = {"forecast": []}
    app.extensions["dobby_client"] = mock_client
    response = app.test_client().get(
        "/api/forecast?business_id=shop_commercial&level=category&id=shop_commercial_cat_coffee"
    )
    assert response.status_code == 200
    mock_client.forecast.assert_called_once_with(
        {"business_id": "shop_commercial", "level": "category", "id": "shop_commercial_cat_coffee"}
    )


def test_overview_keeps_health_when_metrics_times_out(app):
    mock_client = Mock()
    mock_client.health.return_value = {"status": "ok", "model_versions": {"forecast": "fc-v1.0"}}
    mock_client.metrics.side_effect = DobbyAPIError("The metrics request timed out.", 504, "timeout")
    app.extensions["dobby_client"] = mock_client
    response = app.test_client().get("/api/overview")
    assert response.status_code == 200
    assert response.json["health"]["status"] == "ok"
    assert response.json["metrics_error"]["kind"] == "timeout"


def test_client_retries_get_timeout_once(monkeypatch):
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "ok"}
    calls = iter([requests.Timeout("cold start"), response])

    def request(*args, **kwargs):
        value = next(calls)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr("requests.request", request)
    result = DobbyClient("https://example.test", retries=1).health()
    assert result == {"status": "ok"}


def test_metrics_are_cached(monkeypatch):
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {"recommendations": {}}
    request = Mock(return_value=response)
    monkeypatch.setattr("requests.request", request)
    client = DobbyClient("https://example.test", cache_ttl=30, retries=0)
    assert client.metrics() == client.metrics()
    request.assert_called_once()


def test_http_404_is_distinguished(monkeypatch):
    response = Mock()
    response.status_code = 404
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    monkeypatch.setattr("requests.request", Mock(return_value=response))
    with pytest.raises(DobbyAPIError) as raised:
        DobbyClient("https://example.test", retries=0).forecast({"id": "missing"})
    assert raised.value.status_code == 404
    assert raised.value.kind == "http"


def test_client_passes_explicit_connect_and_read_timeout(monkeypatch):
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = {"status": "ok"}
    request = Mock(return_value=response)
    monkeypatch.setattr("requests.request", request)
    DobbyClient("http://127.0.0.1:8000", timeout=(2, 9), retries=0).health()
    assert request.call_args.kwargs["timeout"] == (2, 9)


def test_client_does_not_retry_404(monkeypatch):
    response = Mock()
    response.status_code = 404
    response.raise_for_status.side_effect = requests.HTTPError(response=response)
    request = Mock(return_value=response)
    monkeypatch.setattr("requests.request", request)
    with pytest.raises(DobbyAPIError):
        DobbyClient("https://example.test", retries=3).health()
    request.assert_called_once()
