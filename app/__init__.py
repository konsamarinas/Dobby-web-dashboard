import logging
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

from config import Config
from app.services.dobby_client import DobbyAPIError, DobbyClient


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    logging.basicConfig(level=getattr(logging, app.config["LOG_LEVEL"], logging.INFO))
    app.extensions["dobby_client"] = DobbyClient(
        app.config["DOBBY_API_URL"],
        timeout=(app.config["DOBBY_API_CONNECT_TIMEOUT"], app.config["DOBBY_API_READ_TIMEOUT"]),
        cache_ttl=app.config["DOBBY_CACHE_TTL"],
        retries=app.config["DOBBY_API_RETRIES"],
    )

    def client():
        return app.extensions["dobby_client"]

    def api_error(exc):
        return jsonify({"error": str(exc), "kind": exc.kind}), exc.status_code or 502

    @app.context_processor
    def inject_globals():
        return {"app_name": "DOBBY Intelligence"}

    @app.get("/")
    def dashboard():
        return render_template("dashboard.html", page="overview")

    @app.get("/metrics")
    def metrics_page():
        return render_template("metrics.html", page="metrics")

    @app.get("/health")
    def health_page():
        return render_template("health.html", page="health")

    @app.get("/recommendations")
    def recommendations_page():
        return render_template("recommendations.html", page="recommendations")

    @app.get("/forecasting")
    def forecasting_page():
        return render_template("forecasting.html", page="forecasting")

    @app.get("/business-impact")
    def business_impact_page():
        return render_template("business_impact.html", page="business-impact")

    @app.get("/api/overview")
    def overview_api():
        started = time.perf_counter()
        try:
            health = client().health()
        except DobbyAPIError as exc:
            return api_error(exc)
        response = {
            "health": health,
            "response_time_ms": round((time.perf_counter() - started) * 1000, 1),
            "last_successful_request": datetime.now(timezone.utc).isoformat(),
        }
        try:
            response["metrics"] = client().metrics()
        except DobbyAPIError as exc:
            response["metrics_error"] = {
                "message": str(exc),
                "status_code": exc.status_code,
                "kind": exc.kind,
            }
        return jsonify(response)

    @app.get("/api/health")
    def health_api():
        started = time.perf_counter()
        try:
            health = client().health()
            return jsonify(
                {
                    "health": health,
                    "response_time_ms": round((time.perf_counter() - started) * 1000, 1),
                    "last_successful_request": datetime.now(timezone.utc).isoformat(),
                }
            )
        except DobbyAPIError as exc:
            return api_error(exc)

    @app.get("/api/metrics")
    def metrics_api():
        try:
            return jsonify(client().metrics())
        except DobbyAPIError as exc:
            return api_error(exc)

    @app.post("/api/recommendations")
    def recommendations_api():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "A JSON request body is required."}), 400
        try:
            return jsonify(client().recommendations(payload))
        except DobbyAPIError as exc:
            return api_error(exc)

    @app.get("/api/forecast")
    def forecast_api():
        allowed = {"business_id", "level", "id", "start_date", "horizon", "order_type"}
        params = {key: value for key, value in request.args.to_dict(flat=True).items() if key in allowed}
        level = params.get("level")
        identifier = params.get("id", "")
        if level == "product" and "_cat_" in identifier:
            return jsonify({"error": "A category ID cannot be used with product-level forecasting. Select Product and enter a product ID, or select Category."}), 400
        if level == "category" and "_prod_" in identifier:
            return jsonify({"error": "A product ID cannot be used with category-level forecasting. Select Category and enter a category ID."}), 400
        try:
            return jsonify(client().forecast(params))
        except DobbyAPIError as exc:
            return api_error(exc)

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return render_template("404.html", page=""), 404

    return app
