import os

import joblib
import pandas as pd
import requests
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.environ.get("MODEL_PATH", os.path.join(BASE_DIR, "model.pkl"))
# Inside docker compose the DB service is reachable by its service name.
# For local runs: set DB_SERVICE_URL=http://localhost:8001
DB_SERVICE_URL = os.environ.get("DB_SERVICE_URL", "http://dbapp:8001")

NUMERIC_FEATURES = ["Study_Hours_per_Week", "Attendance_Rate", "Past_Exam_Scores"]
CATEGORICAL_FEATURES = [
    "Gender",
    "Parental_Education_Level",
    "Internet_Access_at_Home",
    "Extracurricular_Activities",
]
# Final_Exam_Score is intentionally NOT used (target leakage).
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

# The model was trained on a numeric target (0 = Fail, 1 = Pass).
# Text labels pass through unchanged, so this also works if the model returns "Pass"/"Fail".
LABEL_MAP = {0: "Fail", 1: "Pass", "0": "Fail", "1": "Pass"}


def to_label(value):
    return LABEL_MAP.get(value, str(value))


def get_probability(inp):
    """Return {"Fail": p, "Pass": p} or None if the model can't provide it."""
    if not hasattr(model, "predict_proba"):
        return None
    probs = model.predict_proba(inp)[0]
    result = {to_label(c): float(p) for c, p in zip(model.classes_, probs)}
    return result if {"Fail", "Pass"} <= result.keys() else None


def parse_input(data):
    """Validate the incoming form/JSON data and return a clean dict."""
    row = {}
    for col in FEATURES:
        value = data.get(col)
        if value is None or str(value).strip() == "":
            raise ValueError(f"Missing field: {col}")
        if col in NUMERIC_FEATURES:
            try:
                row[col] = float(value)
            except ValueError:
                raise ValueError(f"{col} must be a number")
        else:
            row[col] = str(value).strip()
    return row


def save_record(row, prediction):
    """Send the record to the DB service. A DB failure must not break predictions."""
    try:
        response = requests.post(
            f"{DB_SERVICE_URL}/add_record",
            json={**row, "prediction": prediction},
            timeout=3,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        app.logger.warning("Could not save record to DB service: %s", exc)


@app.route("/")
def welcome():
    return render_template("index.html")


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        return redirect(url_for("welcome"))

    data = request.get_json(silent=True) if request.is_json else request.form

    try:
        row = parse_input(data or {})
    except ValueError as exc:
        if request.is_json:
            return jsonify({"error": str(exc)}), 400
        return render_template("index.html", error=str(exc)), 400

    inp = pd.DataFrame([row], columns=FEATURES)
    prediction = to_label(model.predict(inp)[0])
    probability = get_probability(inp)

    save_record(row, prediction)

    if request.is_json:
        return jsonify({"prediction": prediction, "probability": probability})
    return render_template(
        "prediction.html", prediction=prediction, probability=probability
    )


@app.route("/show-records", methods=["GET"])
def show_records():
    try:
        response = requests.get(f"{DB_SERVICE_URL}/get_records", timeout=3)
        response.raise_for_status()
        return render_template("records.html", records=response.json())
    except requests.RequestException as exc:
        app.logger.warning("Could not fetch records: %s", exc)
        return render_template(
            "records.html", records=[], error="Database service is unavailable."
        ), 503


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/ready")
def ready():
    return jsonify({"status": "ready", "model_loaded": model is not None})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)