import os
import time

import joblib
import pandas as pd
import requests
from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from prometheus_client import Counter, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware


app = Flask(__name__)

# Expose Prometheus metrics separately from Flask request handling.
app.wsgi_app = DispatcherMiddleware(
    app.wsgi_app,
    {"/metrics": make_wsgi_app()},
)


# -------------------- Prometheus metrics --------------------

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["route", "method", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["route", "method"],
)

PREDICTIONS = Counter(
    "predictions_total",
    "Successful model predictions",
    ["result"],
)

PREDICTION_FAILURES = Counter(
    "prediction_failures_total",
    "Failed prediction attempts",
    ["stage"],
)

INFERENCE_TIME = Histogram(
    "model_inference_duration_seconds",
    "Time spent computing predictions and probabilities",
)

DB_SAVE_ATTEMPTS = Counter(
    "db_save_attempts_total",
    "Attempts to save prediction records",
    ["outcome"],
)

DB_SAVE_DURATION = Histogram(
    "db_save_request_duration_seconds",
    "Time spent calling the database service to save a record",
)

# Initialize known label values so they appear before the first event.
for result in ("Pass", "Fail"):
    PREDICTIONS.labels(result=result)

for stage in ("validation", "inference"):
    PREDICTION_FAILURES.labels(stage=stage)

for outcome in ("success", "failure"):
    DB_SAVE_ATTEMPTS.labels(outcome=outcome)


@app.before_request
def start_request_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def record_http_metrics(response):
    # Keep health probes separate from application traffic.
    # /metrics is handled by the WSGI middleware above.
    if request.endpoint in ("health", "ready"):
        return response

    # Use route templates instead of raw URLs to limit label values.
    route = request.url_rule.rule if request.url_rule else "unmatched"

    HTTP_REQUESTS.labels(
        route=route,
        method=request.method,
        status=str(response.status_code),
    ).inc()

    started = getattr(g, "request_start_time", None)
    if started is not None:
        HTTP_REQUEST_DURATION.labels(
            route=route,
            method=request.method,
        ).observe(time.perf_counter() - started)

    return response


# -------------------- Application configuration --------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.environ.get(
    "MODEL_PATH",
    os.path.join(BASE_DIR, "model.pkl"),
)

# Inside Docker Compose, use the database service name.
# For local runs, set DB_SERVICE_URL=http://localhost:8001.
DB_SERVICE_URL = os.environ.get(
    "DB_SERVICE_URL",
    "http://dbapp:8001",
)

NUMERIC_FEATURES = [
    "Study_Hours_per_Week",
    "Attendance_Rate",
    "Past_Exam_Scores",
]

CATEGORICAL_FEATURES = [
    "Gender",
    "Parental_Education_Level",
    "Internet_Access_at_Home",
    "Extracurricular_Activities",
]

# Final_Exam_Score is intentionally excluded to prevent target leakage.
FEATURES = [
    "Gender",
    "Study_Hours_per_Week",
    "Attendance_Rate",
    "Past_Exam_Scores",
    "Parental_Education_Level",
    "Internet_Access_at_Home",
    "Extracurricular_Activities",
]

model = joblib.load(MODEL_PATH)

LABEL_MAP = {
    0: "Fail",
    1: "Pass",
    "0": "Fail",
    "1": "Pass",
}


# -------------------- Helper functions --------------------

def to_label(value):
    return LABEL_MAP.get(value, str(value))


def get_probability(inp):
    """Return {"Fail": p, "Pass": p}, or None if unavailable."""
    if not hasattr(model, "predict_proba"):
        return None

    probs = model.predict_proba(inp)[0]
    result = {
        to_label(c): float(p)
        for c, p in zip(model.classes_, probs)
    }

    return result if {"Fail", "Pass"} <= result.keys() else None


def parse_input(data):
    """Validate incoming form/JSON data and return a clean dict."""
    row = {}

    for col in FEATURES:
        value = data.get(col)

        if value is None or str(value).strip() == "":
            raise ValueError(f"Missing field: {col}")

        if col in NUMERIC_FEATURES:
            try:
                row[col] = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"{col} must be a number") from None
        else:
            row[col] = str(value).strip()

    return row


def save_record(row, prediction):
    """Save a record without letting database failures break predictions."""
    try:
        with DB_SAVE_DURATION.time():
            response = requests.post(
                f"{DB_SERVICE_URL}/add_record",
                json={**row, "prediction": prediction},
                timeout=3,
            )
            response.raise_for_status()

        DB_SAVE_ATTEMPTS.labels(outcome="success").inc()

    except requests.RequestException as exc:
        DB_SAVE_ATTEMPTS.labels(outcome="failure").inc()
        app.logger.warning(
            "Could not save record to DB service: %s",
            exc,
        )


# -------------------- Routes --------------------

@app.route("/")
def welcome():
    return render_template("index.html")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return redirect(url_for("welcome"))

    data = (
        request.get_json(silent=True)
        if request.is_json
        else request.form
    )

    try:
        if request.is_json and not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object")

        row = parse_input(data or {})

    except ValueError as exc:
        PREDICTION_FAILURES.labels(stage="validation").inc()

        if request.is_json:
            return jsonify({"error": str(exc)}), 400

        return render_template(
            "index.html",
            error=str(exc),
        ), 400

    try:
        inp = pd.DataFrame([row], columns=FEATURES)

        with INFERENCE_TIME.time():
            prediction = to_label(model.predict(inp)[0])
            probability = get_probability(inp)

        if prediction not in ("Pass", "Fail"):
            raise ValueError("Model returned an unexpected prediction label")

    except Exception:
        PREDICTION_FAILURES.labels(stage="inference").inc()
        app.logger.exception("Model inference failed")

        message = "Prediction failed. Please try again later."

        if request.is_json:
            return jsonify({"error": message}), 500

        return render_template(
            "index.html",
            error=message,
        ), 500

    # A successful prediction is counted even if saving it later fails.
    PREDICTIONS.labels(result=prediction).inc()

    save_record(row, prediction)

    if request.is_json:
        return jsonify({
            "prediction": prediction,
            "probability": probability,
        })

    return render_template(
        "prediction.html",
        prediction=prediction,
        probability=probability,
    )


@app.route("/show-records", methods=["GET"])
def show_records():
    try:
        response = requests.get(
            f"{DB_SERVICE_URL}/get_records",
            timeout=3,
        )
        response.raise_for_status()

        return render_template(
            "records.html",
            records=response.json(),
        )

    except requests.RequestException as exc:
        app.logger.warning("Could not fetch records: %s", exc)

        return render_template(
            "records.html",
            records=[],
            error="Database service is unavailable.",
        ), 503


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/ready")
def ready():
    return jsonify({
        "status": "ready",
        "model_loaded": model is not None,
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False,
    )